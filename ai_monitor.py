import psutil, os, time, json, socket, subprocess
from collections import deque
from datetime import datetime
from threat_intel import ThreatIntelAggregator

BASELINE_FILE = os.path.join(os.path.dirname(__file__), "baseline.json")
MONITORED_HOSTS = ["8.8.8.8", "1.1.1.1"]
MIN_HISTORY = 20

class SelfLearningMonitor:
    def __init__(self, window=100):
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
        self.load_baseline()
        self.intel = ThreatIntelAggregator()
        self.intel.start_background(interval=1800)
        self.current_iocs = set()
        self.last_feed_pull = 0

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
                std = float((sum((x - mean) ** 2 for x in arr) / len(arr)) ** 0.5)
                self.baseline[k] = (mean, std)
        for host, hist in self.host_status.items():
            arr = list(hist)
            if len(arr) >= MIN_HISTORY:
                mean = float(sum(arr)) / len(arr)
                std = float((sum((x - mean) ** 2 for x in arr) / len(arr)) ** 0.5)
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
            mean, std = self.baseline.get(metric, (0, 1))
            val = history[-1]
            if std > 0 and abs(val - mean) > 3 * std and not self.feedback.get(f"{metric}-{int(val)}"):
                anomalies.append(f"Anomaly: {label} {val} (Norm {mean:.1f}±{std:.1f})")
        for host in MONITORED_HOSTS:
            mean, std = self.baseline.get(host, (0, 1))
            val = self.host_status[host][-1]
            if val == -1:
                anomalies.append(f"Device Down: {host}")
            elif std > 0 and abs(val - mean) > 3 * std:
                anomalies.append(f"Anomaly: {host} {val}ms (Norm {mean:.1f}±{std:.1f})")
        net = psutil.net_connections()
        for conn in net:
            try:
                ip = conn.raddr.ip if hasattr(conn, "raddr") and conn.raddr else None
                if ip and ip in self.current_iocs:
                    anomalies.append(f"Threat IP: {ip}")
            except Exception:
                continue
        return anomalies if anomalies else ["All Normal"], bool(anomalies)

    def get_temp(self):
        try:
            out = subprocess.getoutput("vcgencmd measure_temp")
            return float(out.split('=')[1].replace("'C",""))
        except:
            try:
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    return float(f.read()) / 1000
            except:
                return -1

    def get_gateway(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return '.'.join(ip.split('.')[:3]) + '.1'
        except Exception:
            return "192.168.1.1"  # fallback guess

    def ping_host(self, host):
        try:
            r = subprocess.run(['ping', '-c', '1', '-W', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = r.stdout.decode()
            ms = [float(x.split('=')[1].replace(' ms','')) for x in out.split() if "time=" in x]
            return ms[0] if ms else -1
        except:
            return -1

    def failed_logins(self):
        log_files = ['/var/log/auth.log', '/var/log/secure']
        count = 0
        for log in log_files:
            try:
                with open(log) as f:
                    lines = f.readlines()[-500:]
                    count += sum(1 for line in lines if "Failed password" in line and "invalid user" not in line)
            except Exception:
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
        for a in anomalies:
            if "Device Down" in a:
                os.system("echo 'Device Down Detected!' | wall")
            if "Temp" in a and "Tmp:" in a:
                temp_val = float(a.split("Tmp:")[1].split('C')[0])
                if temp_val > 80:
                    os.system("sudo shutdown now")
            if "Threat IP:" in a:
                ip = a.split("Threat IP:")[1].strip()
                os.system(f"sudo iptables -A INPUT -s {ip} -j DROP")
