import psutil, os, time, json, socket, subprocess
from collections import deque
from datetime import datetime
from threat_intel import ThreatIntelAggregator
from config import setup_logging

BASELINE_FILE = os.path.join(os.path.dirname(__file__), "baseline.json")
AI_LEARNING_FILE = os.path.join(os.path.dirname(__file__), "ai_learning.json")
AI_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ai_config.json")
MONITORED_HOSTS = ["8.8.8.8", "1.1.1.1"]
MIN_HISTORY = 20

class SelfLearningMonitor:
    def __init__(self, window=100):
        self.logger = setup_logging()
        self.cpu_history = deque(maxlen=window)
        self.ram_history = deque(maxlen=window)
        self.disk_history = deque(maxlen=window)
        self.temp_history = deque(maxlen=window)
        self.ping_history = deque(maxlen=window)
        self.net_history = deque(maxlen=window)
        self.fail_login_history = deque(maxlen=window)
        self.host_status = {host: deque(maxlen=window) for host in MONITORED_HOSTS}
        self.baseline = {}
        self.feedback = {}
        self.ai_learning_data = {}
        self.ai_config = self.load_ai_config()
        self.load_baseline()
        self.load_ai_learning()
        self.intel = ThreatIntelAggregator()
        self.intel.start_background(interval=1800)
        self.current_iocs = set()
        self.last_feed_pull = 0
        self.pattern_history = deque(maxlen=1000)  # Store patterns for AI learning
        self.ai_client = None
        self.initialize_ai_client()

    def update(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        temp = self.get_temp()
        ping = self.ping_host(self.get_gateway())
        net = len(psutil.net_connections())
        fails = self.failed_logins()
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        self.disk_history.append(disk)
        self.temp_history.append(temp)
        self.ping_history.append(ping)
        self.net_history.append(net)
        self.fail_login_history.append(fails)
        for host in MONITORED_HOSTS:
            self.host_status[host].append(self.ping_host(host))
        now = time.time()
        if now - self.last_feed_pull > 1800:
            self.last_feed_pull = now
            self.refresh_iocs()

    def learn_baseline(self):
        for k, hist in [
            ('cpu', self.cpu_history), ('ram', self.ram_history),
            ('ping', self.ping_history), ('net', self.net_history),
            ('disk', self.disk_history), ('temp', self.temp_history),
            ('fail', self.fail_login_history)
        ]:
            arr = list(hist)
            if len(arr) >= MIN_HISTORY:
                mean = float(sum(arr)) / len(arr)
                variance = sum((x - mean) ** 2 for x in arr) / len(arr)
                std = float(variance ** 0.5)
                # Avoid division by zero in anomaly detection
                if std < 0.1:
                    std = 0.1
                self.baseline[k] = (mean, std)
        for host, hist in self.host_status.items():
            arr = list(hist)
            if len(arr) >= MIN_HISTORY:
                mean = float(sum(arr)) / len(arr)
                variance = sum((x - mean) ** 2 for x in arr) / len(arr)
                std = float(variance ** 0.5)
                # Avoid division by zero in anomaly detection
                if std < 0.1:
                    std = 0.1
                self.baseline[host] = (mean, std)

    def detect_anomaly(self):
        if len(self.cpu_history) < MIN_HISTORY:
            return ["Learning..."], False
        anomalies = []
        metrics = [
            ('cpu', self.cpu_history, "CPU"),
            ('ram', self.ram_history, "RAM"),
            ('disk', self.disk_history, "Disk"),
            ('temp', self.temp_history, "Temp"),
            ('ping', self.ping_history, "Ping"),
            ('net', self.net_history, "Connections"),
            ('fail', self.fail_login_history, "Failed Login"),
        ]
        for metric, history, label in metrics:
            if not history:
                continue
            mean, std = self.baseline.get(metric, (0, 0.1))
            val = history[-1]
            if val == -1:  # Skip invalid measurements
                continue
            if std > 0 and abs(val - mean) > 3 * std and not self.feedback.get(f"{metric}-{int(val)}"):
                anomalies.append(f"Anomaly: {label} {val} (Norm {mean:.1f}±{std:.1f})")
        for host in MONITORED_HOSTS:
            if not self.host_status[host]:
                continue
            mean, std = self.baseline.get(host, (0, 0.1))
            val = self.host_status[host][-1]
            if val == -1:
                anomalies.append(f"Device Down: {host}")
            elif std > 0 and abs(val - mean) > 3 * std:
                anomalies.append(f"Anomaly: {host} {val}ms (Norm {mean:.1f}±{std:.1f})")
        
        # Check for threat IPs
        try:
            net = psutil.net_connections()
            for conn in net:
                try:
                    ip = conn.raddr.ip if hasattr(conn, "raddr") and conn.raddr else None
                    if ip and ip in self.current_iocs:
                        anomalies.append(f"Threat IP: {ip}")
                except Exception:
                    continue
        except Exception:
            pass
        
        return anomalies if anomalies else ["All Normal"], bool(anomalies)

    def get_temp(self):
        try:
            # Try Raspberry Pi specific temperature command
            out = subprocess.getoutput("vcgencmd measure_temp")
            if "temp=" in out:
                return float(out.split('=')[1].replace("'C",""))
        except Exception:
            pass
        
        try:
            # Try generic Linux thermal zone
            with open("/sys/class/thermal/thermal_zone0/temp", 'r') as f:
                temp_str = f.read().strip()
                return float(temp_str) / 1000
        except Exception:
            pass
        
        try:
            # Try alternative thermal zones
            for i in range(5):
                thermal_path = f"/sys/class/thermal/thermal_zone{i}/temp"
                if os.path.exists(thermal_path):
                    with open(thermal_path, 'r') as f:
                        temp_str = f.read().strip()
                        temp = float(temp_str) / 1000
                        if 0 < temp < 150:  # Reasonable temperature range
                            return temp
        except Exception:
            pass
        
        return -1  # Could not read temperature

    def get_gateway(self):
        try:
            # Try to get gateway from routing table
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
        except Exception:
            pass
        
        try:
            # Fallback: connect to external IP to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            # Assume gateway is .1 on the same subnet
            return '.'.join(ip.split('.')[:3]) + '.1'
        except Exception:
            pass
        
        return "192.168.1.1"  # Ultimate fallback

    def ping_host(self, host):
        try:
            r = subprocess.run(['ping', '-c', '1', '-W', '2', host], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                             timeout=5, text=True)
            if r.returncode == 0:
                out = r.stdout
                # Parse ping output for time
                for line in out.split('\n'):
                    if "time=" in line:
                        time_part = line.split("time=")[1].split()[0]
                        return float(time_part)
            return -1
        except (subprocess.TimeoutExpired, ValueError, IndexError):
            return -1
        except Exception:
            return -1

    def failed_logins(self):
        log_files = ['/var/log/auth.log', '/var/log/secure']
        count = 0
        for log in log_files:
            try:
                with open(log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-500:]  # Read last 500 lines
                    for line in lines:
                        if "Failed password" in line and "invalid user" not in line:
                            count += 1
            except (FileNotFoundError, PermissionError):
                continue
            except Exception as e:
                print(f"Error reading log {log}: {e}")
                continue
        return count

    def status_report(self):
        t = datetime.now().strftime("%H:%M:%S")
        cpu = self.cpu_history[-1] if self.cpu_history else 0
        ram = self.ram_history[-1] if self.ram_history else 0
        disk = self.disk_history[-1] if self.disk_history else 0
        temp = self.temp_history[-1] if self.temp_history else 0
        ping = self.ping_history[-1] if self.ping_history else -1
        net = self.net_history[-1] if self.net_history else 0
        fails = self.fail_login_history[-1] if self.fail_login_history else 0
        hosts = [f"{h}: {self.host_status[h][-1]}ms" for h in MONITORED_HOSTS]
        return [
            f"{t}",
            f"CPU:{cpu:.1f}% RAM:{ram:.1f}%",
            f"Disk:{disk:.1f}% Tmp:{temp:.1f}C",
            f"Ping:{ping:.1f}ms Net:{net}",
            f"Fails:{fails}",
            *hosts
        ]

    def refresh_iocs(self):
        iocs = set()
        for k, entries in self.intel.intel_data.items():
            for e in entries:
                if "." in e[0] and e[0].count(".") == 3:
                    iocs.add(e[0])
        self.current_iocs = iocs

    def save_baseline(self):
        data = {
            'baseline': self.baseline,
            'feedback': self.feedback
        }
        try:
            with open(BASELINE_FILE, "w") as f:
                json.dump(data, f)
            # print(f"[DEBUG] Baseline saved to {BASELINE_FILE}")
        except Exception as e:
            print(f"[ERROR] Could not save baseline: {e}")

    def load_baseline(self):
        if os.path.exists(BASELINE_FILE):
            try:
                with open(BASELINE_FILE, "r") as f:
                    data = json.load(f)
                    self.baseline = data.get('baseline', {})
                    self.feedback = data.get('feedback', {})
                # print(f"[DEBUG] Baseline loaded from {BASELINE_FILE}")
            except Exception as e:
                print(f"[ERROR] Could not load baseline: {e}")

    def feedback_correction(self, anomaly_label, value):
        self.feedback[f"{anomaly_label}-{int(value)}"] = True
        self.save_baseline()

    def trigger_action(self, anomalies):
        import subprocess
        import shlex
        for a in anomalies:
            if "Device Down" in a:
                subprocess.run(["echo", "Device Down Detected!", "|", "wall"], check=False)
            if "Temp" in a and "Tmp:" in a:
                try:
                    temp_val = float(a.split("Tmp:")[1].split('C')[0])
                    if temp_val > 80:
                        subprocess.run(["sudo", "shutdown", "now"], check=False)
                except ValueError:
                    pass
            if "Threat IP:" in a:
                try:
                    ip = a.split("Threat IP:")[1].strip()
                    # Validate IP address format
                    parts = ip.split('.')
                    if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
                        subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], check=False)
                except (ValueError, IndexError):
                    pass

    def load_ai_config(self):
        """Load AI configuration settings"""
        default_config = {
            "ai_enabled": False,
            "use_cloud_ai": False,
            "api_key": "",
            "ai_model": "gpt-4o-mini",
            "learning_enabled": True,
            "auto_correction": False,
            "confidence_threshold": 0.8,
            "pattern_analysis": True
        }
        
        if os.path.exists(AI_CONFIG_FILE):
            try:
                with open(AI_CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                self.logger.error(f"Error loading AI config: {e}")
        
        return default_config

    def save_ai_config(self):
        """Save AI configuration settings"""
        try:
            with open(AI_CONFIG_FILE, "w") as f:
                json.dump(self.ai_config, f, indent=2)
            self.logger.info("AI configuration saved")
        except Exception as e:
            self.logger.error(f"Error saving AI config: {e}")

    def update_ai_config(self, **kwargs):
        """Update AI configuration with new values"""
        for key, value in kwargs.items():
            if key in self.ai_config:
                self.ai_config[key] = value
        self.save_ai_config()
        self.initialize_ai_client()

    def initialize_ai_client(self):
        """Initialize AI client if cloud AI is enabled"""
        if self.ai_config.get("use_cloud_ai", False) and self.ai_config.get("api_key"):
            try:
                import openai
                self.ai_client = openai.OpenAI(api_key=self.ai_config["api_key"])
                self.logger.info("AI client initialized successfully")
            except ImportError:
                self.logger.warning("OpenAI library not installed. Install with: pip install openai")
                self.ai_client = None
            except Exception as e:
                self.logger.error(f"Error initializing AI client: {e}")
                self.ai_client = None
        else:
            self.ai_client = None

    def load_ai_learning(self):
        """Load AI learning data"""
        if os.path.exists(AI_LEARNING_FILE):
            try:
                with open(AI_LEARNING_FILE, "r") as f:
                    self.ai_learning_data = json.load(f)
                self.logger.info("AI learning data loaded")
            except Exception as e:
                self.logger.error(f"Error loading AI learning data: {e}")
                self.ai_learning_data = {}

    def save_ai_learning(self):
        """Save AI learning data"""
        try:
            with open(AI_LEARNING_FILE, "w") as f:
                json.dump(self.ai_learning_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving AI learning data: {e}")

    def analyze_pattern_locally(self, metrics_data):
        """Local pattern analysis without external API"""
        patterns = []
        
        # Simple local pattern detection
        if len(self.pattern_history) >= 50:
            recent_patterns = list(self.pattern_history)[-50:]
            
            # Detect cyclic patterns
            cpu_values = [p.get('cpu', 0) for p in recent_patterns]
            if len(set(cpu_values)) < 5:  # Low variance indicates pattern
                patterns.append("Cyclic CPU usage detected")
            
            # Detect gradual increases
            if len(cpu_values) >= 10:
                trend = sum(cpu_values[-5:]) / 5 - sum(cpu_values[:5]) / 5
                if trend > 20:
                    patterns.append("Gradual CPU increase trend detected")
            
            # Detect network anomalies
            net_values = [p.get('net', 0) for p in recent_patterns]
            if max(net_values) > 2 * (sum(net_values) / len(net_values)):
                patterns.append("Network spike pattern detected")
        
        return patterns

    def analyze_pattern_with_ai(self, metrics_data):
        """AI-powered pattern analysis using cloud API"""
        if not self.ai_client:
            return []
        
        try:
            # Prepare data for AI analysis
            data_summary = {
                "cpu_avg": sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
                "ram_avg": sum(self.ram_history) / len(self.ram_history) if self.ram_history else 0,
                "recent_anomalies": len([x for x in self.pattern_history if x.get('anomaly', False)]),
                "time_of_day": datetime.now().hour,
                "day_of_week": datetime.now().weekday()
            }
            
            prompt = f"""
            Analyze this system monitoring data for patterns and anomalies:
            
            Current metrics: {metrics_data}
            Historical averages: {data_summary}
            
            Identify:
            1. Unusual patterns
            2. Potential security threats
            3. Performance issues
            4. Predictive insights
            
            Respond with a JSON object containing:
            - patterns: list of detected patterns
            - threats: list of potential threats
            - recommendations: list of recommendations
            - confidence: float between 0-1
            """
            
            response = self.ai_client.chat.completions.create(
                model=self.ai_config.get("ai_model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a cybersecurity and system monitoring expert. Analyze data and provide insights in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            try:
                analysis = json.loads(ai_response)
                return analysis
            except json.JSONDecodeError:
                # Fallback to text analysis
                return {"patterns": [ai_response], "confidence": 0.5}
            
        except Exception as e:
            self.logger.error(f"AI analysis error: {e}")
            return []

    def enhanced_anomaly_detection(self):
        """Enhanced anomaly detection with AI learning"""
        if len(self.cpu_history) < MIN_HISTORY:
            return ["Learning..."], False
        
        # Get basic anomalies
        basic_anomalies, has_basic_anomaly = self.detect_anomaly()
        
        if not self.ai_config.get("ai_enabled", False):
            return basic_anomalies, has_basic_anomaly
        
        # Prepare current metrics
        current_metrics = {
            "cpu": self.cpu_history[-1] if self.cpu_history else 0,
            "ram": self.ram_history[-1] if self.ram_history else 0,
            "disk": self.disk_history[-1] if self.disk_history else 0,
            "temp": self.temp_history[-1] if self.temp_history else 0,
            "ping": self.ping_history[-1] if self.ping_history else 0,
            "net": self.net_history[-1] if self.net_history else 0,
            "timestamp": time.time(),
            "anomaly": has_basic_anomaly
        }
        
        # Store pattern for learning
        self.pattern_history.append(current_metrics)
        
        enhanced_anomalies = list(basic_anomalies)
        
        # AI-powered analysis
        if self.ai_config.get("pattern_analysis", True):
            if self.ai_config.get("use_cloud_ai", False):
                ai_analysis = self.analyze_pattern_with_ai(current_metrics)
                if ai_analysis:
                    if "patterns" in ai_analysis:
                        enhanced_anomalies.extend(ai_analysis["patterns"])
                    if "threats" in ai_analysis:
                        enhanced_anomalies.extend([f"AI Threat: {t}" for t in ai_analysis["threats"]])
            else:
                # Local pattern analysis
                local_patterns = self.analyze_pattern_locally(current_metrics)
                enhanced_anomalies.extend([f"Local Pattern: {p}" for p in local_patterns])
        
        # Learning and auto-correction
        if self.ai_config.get("learning_enabled", True):
            self.learn_from_patterns()
        
        return enhanced_anomalies, has_basic_anomaly or len(enhanced_anomalies) > len(basic_anomalies)

    def learn_from_patterns(self):
        """Learn from historical patterns to improve detection"""
        if len(self.pattern_history) < 100:
            return
        
        # Analyze false positives
        false_positives = self.feedback.get("false_positives", [])
        if false_positives:
            # Adjust thresholds based on false positives
            for fp in false_positives:
                metric = fp.get("metric")
                value = fp.get("value")
                if metric in self.baseline:
                    mean, std = self.baseline[metric]
                    # Increase threshold for this metric
                    self.baseline[metric] = (mean, std * 1.1)
        
        # Save learning data
        self.ai_learning_data["last_learning"] = time.time()
        self.ai_learning_data["pattern_count"] = len(self.pattern_history)
        self.ai_learning_data["false_positive_count"] = len(false_positives)
        self.save_ai_learning()

    def get_ai_insights(self):
        """Get AI-powered insights about system state"""
        if not self.ai_config.get("ai_enabled", False):
            return "AI insights disabled"
        
        insights = []
        
        # Local insights
        if len(self.pattern_history) >= 50:
            recent_data = list(self.pattern_history)[-50:]
            anomaly_rate = sum(1 for p in recent_data if p.get("anomaly", False)) / len(recent_data)
            insights.append(f"Anomaly rate: {anomaly_rate:.2%}")
            
            avg_cpu = sum(p.get("cpu", 0) for p in recent_data) / len(recent_data)
            insights.append(f"Average CPU: {avg_cpu:.1f}%")
        
        # Cloud AI insights
        if self.ai_config.get("use_cloud_ai", False) and self.ai_client:
            try:
                system_summary = self.get_system_summary()
                ai_insights = self.get_ai_recommendations(system_summary)
                if ai_insights:
                    insights.extend(ai_insights)
            except Exception as e:
                self.logger.error(f"Error getting AI insights: {e}")
        
        return insights

    def get_system_summary(self):
        """Get comprehensive system summary for AI analysis"""
        return {
            "uptime": time.time() - (self.ai_learning_data.get("start_time", time.time())),
            "total_anomalies": len([p for p in self.pattern_history if p.get("anomaly", False)]),
            "current_load": {
                "cpu": self.cpu_history[-1] if self.cpu_history else 0,
                "ram": self.ram_history[-1] if self.ram_history else 0,
                "disk": self.disk_history[-1] if self.disk_history else 0,
                "temp": self.temp_history[-1] if self.temp_history else 0
            },
            "threat_intel_count": len(self.current_iocs),
            "monitored_hosts": len(MONITORED_HOSTS)
        }

    def get_ai_recommendations(self, system_summary):
        """Get AI-powered recommendations"""
        if not self.ai_client:
            return []
        
        try:
            prompt = f"""
            Based on this system monitoring summary, provide 3-5 actionable recommendations:
            
            System Summary: {json.dumps(system_summary, indent=2)}
            
            Focus on:
            1. Performance optimization
            2. Security improvements
            3. Monitoring enhancements
            4. Predictive maintenance
            
            Provide concise, actionable recommendations.
            """
            
            response = self.ai_client.chat.completions.create(
                model=self.ai_config.get("ai_model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a system administrator and cybersecurity expert. Provide practical recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.4
            )
            
            recommendations = response.choices[0].message.content.split('\n')
            return [rec.strip() for rec in recommendations if rec.strip()]
            
        except Exception as e:
            self.logger.error(f"Error getting AI recommendations: {e}")
            return []

    def mark_false_positive(self, metric, value, context=None):
        """Mark an anomaly as false positive for learning"""
        if "false_positives" not in self.feedback:
            self.feedback["false_positives"] = []
        
        fp_entry = {
            "metric": metric,
            "value": value,
            "timestamp": time.time(),
            "context": context
        }
        
        self.feedback["false_positives"].append(fp_entry)
        self.save_baseline()
        self.logger.info(f"Marked false positive: {metric}={value}")

    def get_ai_status(self):
        """Get current AI system status"""
        return {
            "ai_enabled": self.ai_config.get("ai_enabled", False),
            "use_cloud_ai": self.ai_config.get("use_cloud_ai", False),
            "api_key_set": bool(self.ai_config.get("api_key")),
            "ai_client_ready": self.ai_client is not None,
            "learning_enabled": self.ai_config.get("learning_enabled", True),
            "pattern_analysis": self.ai_config.get("pattern_analysis", True),
            "patterns_collected": len(self.pattern_history),
            "model": self.ai_config.get("ai_model", "gpt-4o-mini")
        }
