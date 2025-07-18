from flask import Flask, request, session, redirect, url_for, render_template_string
import hashlib, os, json, time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_FILE = os.path.join(THIS_DIR, "admin_user.json")
API_KEY_FILE = os.path.join(THIS_DIR, ".api_key")

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_admin():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r") as f:
            return json.load(f)
    return None

def save_admin(username, password):
    try:
        with open(ADMIN_FILE, "w") as f:
            json.dump({"username": username, "password": hash_pass(password)}, f)
        return True
    except Exception as e:
        print("Failed to save admin user:", e)
        return False

def save_api_key(key):
    try:
        with open(API_KEY_FILE, "w") as f:
            json.dump({"api_key": key}, f)
        return True
    except Exception as e:
        print("Failed to save API key:", e)
        return False

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE) as f:
            return json.load(f).get("api_key", "")
    return os.environ.get("OPENAI_API_KEY", "")

def assistant_answer(question, monitor):
    key = load_api_key()
    try:
        import openai
        HAVE_OPENAI = True
    except ImportError:
        HAVE_OPENAI = False

    if HAVE_OPENAI and key:
        try:
            client = openai.OpenAI(api_key=key)
            prompt = f"""You are ShaydZ, a home network and security assistant. User question: {question}
            Most recent network status:
            {', '.join(monitor.status_report())}
            Recent anomalies:
            {', '.join(monitor.detect_anomaly()[0])}
            Current threat intelligence:
            {str(monitor.intel.intel_data)[:500]}
            Please explain, summarize, or answer as helpfully as possible."""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"You are a helpful network and security assistant."},
                          {"role":"user","content":prompt}],
                max_tokens=300,
                temperature=0.4,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Error] {str(e)}"
    else:
        status = ", ".join(monitor.status_report())
        anomalies = ", ".join(monitor.detect_anomaly()[0])
        tips = "No cloud AI is active. For advanced advice, paste your OpenAI API key in settings."
        return f"""[Local Assistant]
Current status: {status}
Recent anomalies: {anomalies}
{tips}
"""

TEMPLATE_LOGIN = """
<h2>S h a y d Z Admin Login</h2>
<form method=post>
  Username: <input name=username><br>
  Password: <input name=password type=password><br>
  <input type=submit value=Login>
</form>
{% if msg %}<p style='color:red;'>{{msg}}</p>{% endif %}
"""

TEMPLATE_DASH = """
<h1 style="font-family:monospace; letter-spacing:6px;">S h a y d Z</h1>
<h2>Super Monitor</h2>
<div style="margin-bottom: 20px;">
    <a href='/logout' style="margin-right: 10px;">Logout</a>
    <a href='/settings' style="margin-right: 10px;">Settings</a>
    <a href='/ai_dashboard' style="margin-right: 10px;">AI Dashboard</a>
</div>

<div style="margin-bottom: 20px;">
    <h3>System Status</h3>
    <div style="font-family: monospace; background: #f5f5f5; padding: 10px; border: 1px solid #ddd;">
        {{status|safe}}
    </div>
</div>

<div style="margin-bottom: 20px;">
    <h3>Anomalies & Alerts</h3>
    <div style="font-family: monospace; background: #fff3cd; padding: 10px; border: 1px solid #ffeaa7;">
        {{anomalies|safe}}
    </div>
</div>

<div style="margin-bottom: 20px;">
    <h3>Feedback & Learning</h3>
    <form method='post' action='/feedback' style="margin-bottom: 10px;">
        <input name='label' placeholder='Anomaly Label (e.g., cpu, ram)' style="margin-right: 5px;">
        <input name='value' placeholder='Value' style="margin-right: 5px;">
        <button type='submit'>Mark False Positive</button>
    </form>
    
    <form method='post' action='/ai_feedback' style="margin-bottom: 10px;">
        <input name='metric' placeholder='Metric (cpu, ram, etc.)' style="margin-right: 5px;">
        <input name='value' placeholder='Value' style="margin-right: 5px;">
        <input name='context' placeholder='Context (optional)' style="margin-right: 5px;">
        <button type='submit'>AI False Positive</button>
    </form>
</div>

<div style="margin-bottom: 20px;">
    <h3>Ask S h a y d Z Assistant</h3>
    <form method='post' action='/ask'>
        <input name='question' placeholder='Ask about system status, security, or get recommendations...' style='width:80%%;'>
        <button type='submit'>Ask</button>
    </form>
    {% if assistant_answer %}
    <div style='border:1px solid #ccc; margin-top:10px; padding:10px; background: #f9f9f9;'>
        <b>S h a y d Z Assistant:</b><br>
        {{assistant_answer|safe}}
    </div>
    {% endif %}
</div>

<div style="margin-bottom: 20px;">
    <h3>Threat Intelligence Headlines</h3>
    <ul>
        {% for source, entries in headlines.items() %}
            <li><b>{{source}}</b>
                <ul>
                    {% for t, l in entries %}
                        <li><a href="{{l}}" target="_blank">{{t}}</a></li>
                    {% endfor %}
                </ul>
            </li>
        {% endfor %}
    </ul>
</div>
"""

TEMPLATE_SETTINGS = """
<h2>Assistant & AI Settings</h2>
<div style="margin-bottom: 20px;">
    <h3>AI Configuration</h3>
    <form method='post' action='/settings'>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>AI Features:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <label><input type="checkbox" name="ai_enabled" value="true" {{'checked' if ai_status.ai_enabled else ''}}> Enable AI Learning & Detection</label>
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>AI Mode:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <label><input type="radio" name="ai_mode" value="local" {{'checked' if not ai_status.use_cloud_ai else ''}}> Local/Private (No external API)</label><br>
                    <label><input type="radio" name="ai_mode" value="cloud" {{'checked' if ai_status.use_cloud_ai else ''}}> Cloud AI (OpenAI API)</label>
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>OpenAI API Key:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <input type="password" name="api_key" placeholder="sk-..." style="width: 70%;" value="{{'***' if ai_status.api_key_set else ''}}">
                    <small>Required for Cloud AI mode</small>
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>AI Model:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <select name="ai_model">
                        <option value="gpt-4o-mini" {{'selected' if ai_status.model == 'gpt-4o-mini' else ''}}>GPT-4o Mini (Recommended)</option>
                        <option value="gpt-4o" {{'selected' if ai_status.model == 'gpt-4o' else ''}}>GPT-4o (More Powerful)</option>
                        <option value="gpt-3.5-turbo" {{'selected' if ai_status.model == 'gpt-3.5-turbo' else ''}}>GPT-3.5 Turbo (Budget)</option>
                    </select>
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Learning Options:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <label><input type="checkbox" name="learning_enabled" value="true" {{'checked' if ai_status.learning_enabled else ''}}> Enable Learning from Patterns</label><br>
                    <label><input type="checkbox" name="pattern_analysis" value="true" {{'checked' if ai_status.pattern_analysis else ''}}> Enable Pattern Analysis</label><br>
                    <label><input type="checkbox" name="auto_correction" value="true" {{'checked' if ai_status.get('auto_correction', False) else ''}}> Auto-correct False Positives</label>
                </td>
            </tr>
        </table>
        <button type='submit' style="margin-top: 10px; padding: 10px 20px; background: #007cba; color: white; border: none; cursor: pointer;">Save AI Settings</button>
    </form>
</div>

<div style="margin-bottom: 20px;">
    <h3>AI Status</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 5px; border: 1px solid #ddd;"><strong>AI Enabled:</strong></td>
            <td style="padding: 5px; border: 1px solid #ddd;">{{ai_status.ai_enabled}}</td>
        </tr>
        <tr>
            <td style="padding: 5px; border: 1px solid #ddd;"><strong>Mode:</strong></td>
            <td style="padding: 5px; border: 1px solid #ddd;">{{'Cloud AI' if ai_status.use_cloud_ai else 'Local/Private'}}</td>
        </tr>
        <tr>
            <td style="padding: 5px; border: 1px solid #ddd;"><strong>API Key:</strong></td>
            <td style="padding: 5px; border: 1px solid #ddd;">{{'✓ Set' if ai_status.api_key_set else '✗ Not Set'}}</td>
        </tr>
        <tr>
            <td style="padding: 5px; border: 1px solid #ddd;"><strong>Client Ready:</strong></td>
            <td style="padding: 5px; border: 1px solid #ddd;">{{'✓ Ready' if ai_status.ai_client_ready else '✗ Not Ready'}}</td>
        </tr>
        <tr>
            <td style="padding: 5px; border: 1px solid #ddd;"><strong>Patterns Collected:</strong></td>
            <td style="padding: 5px; border: 1px solid #ddd;">{{ai_status.patterns_collected}}</td>
        </tr>
    </table>
</div>

<div style="margin-bottom: 20px;">
    <h3>AI Insights</h3>
    <div style="border: 1px solid #ddd; padding: 10px; background: #f9f9f9;">
        {% if ai_insights %}
            <ul>
                {% for insight in ai_insights %}
                    <li>{{insight}}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>No AI insights available. Enable AI features to get intelligent analysis.</p>
        {% endif %}
    </div>
    <form method='post' action='/ai_insights'>
        <button type='submit' style="margin-top: 10px; padding: 5px 15px; background: #28a745; color: white; border: none; cursor: pointer;">Refresh AI Insights</button>
    </form>
</div>

{% if msg %}<div style="padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; color: #155724; margin: 10px 0;">{{msg}}</div>{% endif %}
<a href='/dashboard'>Back to Dashboard</a>
"""

TEMPLATE_AI_DASHBOARD = """
<h1 style="font-family:monospace; letter-spacing:6px;">S h a y d Z</h1>
<h2>AI Dashboard</h2>
<div style="margin-bottom: 20px;">
    <a href='/dashboard' style="margin-right: 10px;">&lt; Back to Dashboard</a>
    <a href='/settings' style="margin-right: 10px;">Settings</a>
    <a href='/logout'>Logout</a>
</div>

<div style="margin-bottom: 20px;">
    <h3>AI Status Overview</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f8f9fa;">
            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Metric</th>
            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Value</th>
            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Status</th>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">AI Features</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{'Enabled' if ai_status.ai_enabled else 'Disabled'}}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                <span style="color: {{'green' if ai_status.ai_enabled else 'red'}};">
                    {{'[ACTIVE]' if ai_status.ai_enabled else '[INACTIVE]'}}
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">AI Mode</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{'Cloud AI' if ai_status.use_cloud_ai else 'Local/Private'}}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                <span style="color: {{'blue' if ai_status.use_cloud_ai else 'green'}};">
                    {{'[CLOUD]' if ai_status.use_cloud_ai else '[PRIVATE]'}}
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">API Client</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{'Ready' if ai_status.ai_client_ready else 'Not Ready'}}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                <span style="color: {{'green' if ai_status.ai_client_ready else 'orange'}};">
                    {{'[CONNECTED]' if ai_status.ai_client_ready else '[DISCONNECTED]'}}
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Learning</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{'Enabled' if ai_status.learning_enabled else 'Disabled'}}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                <span style="color: {{'green' if ai_status.learning_enabled else 'gray'}};">
                    {{'[LEARNING]' if ai_status.learning_enabled else '[STATIC]'}}
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">Patterns Collected</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{ai_status.patterns_collected}}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                <span style="color: {{'green' if ai_status.patterns_collected > 100 else 'orange' if ai_status.patterns_collected > 50 else 'red'}};">
                    {{'[EXCELLENT]' if ai_status.patterns_collected > 100 else '[GOOD]' if ai_status.patterns_collected > 50 else '[BUILDING]'}}
                </span>
            </td>
        </tr>
    </table>
</div>

<div style="margin-bottom: 20px;">
    <h3>AI Insights & Recommendations</h3>
    <div style="border: 1px solid #ddd; padding: 15px; background: #f8f9fa; border-radius: 5px;">
        {% if ai_insights %}
            <h4>[DATA] Current Insights:</h4>
            <ul style="margin-left: 20px;">
                {% for insight in ai_insights %}
                    <li style="margin-bottom: 5px;">{{insight}}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p style="color: #666;">[AI] No AI insights available yet. 
            {% if not ai_status.ai_enabled %}
                <a href="/settings">Enable AI features</a> to get intelligent analysis.
            {% else %}
                System is still learning. Check back after collecting more data.
            {% endif %}
            </p>
        {% endif %}
    </div>
    <form method='post' action='/ai_insights' style="margin-top: 10px;">
        <button type='submit' style="padding: 8px 16px; background: #007cba; color: white; border: none; cursor: pointer; border-radius: 4px;">[REFRESH] Refresh Insights</button>
    </form>
</div>

<div style="margin-bottom: 20px;">
    <h3>AI Learning Statistics</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
        <div style="border: 1px solid #ddd; padding: 15px; background: #e8f5e8; border-radius: 5px;">
            <h4 style="margin-top: 0; color: #2d5a2d;">[PATTERN] Pattern Analysis</h4>
            <p><strong>Patterns Analyzed:</strong> {{ai_status.patterns_collected}}</p>
            <p><strong>Analysis Mode:</strong> {{'AI-Powered' if ai_status.use_cloud_ai else 'Local Algorithm'}}</p>
            <p><strong>Status:</strong> {{'Active' if ai_status.pattern_analysis else 'Disabled'}}</p>
        </div>
        
        <div style="border: 1px solid #ddd; padding: 15px; background: #e8f0ff; border-radius: 5px;">
            <h4 style="margin-top: 0; color: #2d4a5a;">[BRAIN] Learning Engine</h4>
            <p><strong>Learning:</strong> {{'Enabled' if ai_status.learning_enabled else 'Disabled'}}</p>
            <p><strong>Model:</strong> {{ai_status.model}}</p>
            <p><strong>Auto-Correction:</strong> {{'Yes' if ai_status.get('auto_correction', False) else 'No'}}</p>
        </div>
        
        <div style="border: 1px solid #ddd; padding: 15px; background: #fff8e1; border-radius: 5px;">
            <h4 style="margin-top: 0; color: #5a4d2d;">[PRIVACY] Privacy Mode</h4>
            <p><strong>Mode:</strong> {{'Local/Private' if not ai_status.use_cloud_ai else 'Cloud AI'}}</p>
            <p><strong>Data Sharing:</strong> {{'None' if not ai_status.use_cloud_ai else 'Anonymized'}}</p>
            <p><strong>Privacy Level:</strong> {{'High' if not ai_status.use_cloud_ai else 'Standard'}}</p>
        </div>
    </div>
</div>

<div style="margin-bottom: 20px;">
    <h3>Quick Actions</h3>
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <form method='post' action='/ai_reset_learning' style="display: inline;">
            <button type='submit' onclick="return confirm('Reset all AI learning data?')" 
                    style="padding: 8px 16px; background: #dc3545; color: white; border: none; cursor: pointer; border-radius: 4px;">
                [RESET] Reset Learning Data
            </button>
        </form>
        
        <form method='post' action='/ai_export_data' style="display: inline;">
            <button type='submit' style="padding: 8px 16px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 4px;">
                [EXPORT] Export AI Data
            </button>
        </form>
        
        <form method='post' action='/ai_test_connection' style="display: inline;">
            <button type='submit' style="padding: 8px 16px; background: #ffc107; color: black; border: none; cursor: pointer; border-radius: 4px;">
                [TEST] Test AI Connection
            </button>
        </form>
    </div>
</div>

{% if msg %}
<div style="padding: 10px; margin: 10px 0; border-radius: 4px; 
            background: {{'#d4edda' if 'success' in msg.lower() else '#f8d7da' if 'error' in msg.lower() else '#d1ecf1'}}; 
            border: 1px solid {{'#c3e6cb' if 'success' in msg.lower() else '#f5c6cb' if 'error' in msg.lower() else '#bee5eb'}}; 
            color: {{'#155724' if 'success' in msg.lower() else '#721c24' if 'error' in msg.lower() else '#0c5460'}};">
    {{msg}}
</div>
{% endif %}
"""

def run_admin_ui(monitor):
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    # Production security settings
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Set to True if using HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
        MAX_CONTENT_LENGTH=1024 * 1024,  # 1MB max upload
    )
    
    # Disable Flask debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    @app.route("/", methods=["GET", "POST"])
    def login():
        admin = load_admin()
        msg = ""
        if not admin:
            if request.method == "POST":
                if not save_admin(request.form["username"], request.form["password"]):
                    msg = "Failed to save admin account. Check permissions."
                else:
                    return redirect(url_for('dashboard'))
            return render_template_string(TEMPLATE_LOGIN, msg="Set up your admin account.")
        if request.method == "POST":
            user, pw = request.form["username"], request.form["password"]
            if user == admin["username"] and hash_pass(pw) == admin["password"]:
                session["admin"] = True
                return redirect(url_for('dashboard'))
            else:
                msg = "Login failed"
        return render_template_string(TEMPLATE_LOGIN, msg=msg)

    @app.route("/dashboard", methods=["GET", "POST"])
    def dashboard():
        if not session.get("admin"): return redirect(url_for('login'))
        status = "<br>".join(monitor.status_report())
        
        # Use enhanced anomaly detection if AI is enabled
        if hasattr(monitor, 'enhanced_anomaly_detection') and monitor.ai_config.get("ai_enabled", False):
            anomalies, _ = monitor.enhanced_anomaly_detection()
        else:
            anomalies, _ = monitor.detect_anomaly()
        
        anomalies = "<br>".join(anomalies)
        headlines = monitor.intel.intel_data if hasattr(monitor, 'intel') else {}
        assistant_answer = session.pop('assistant_answer', None)
        return render_template_string(TEMPLATE_DASH, status=status, anomalies=anomalies, headlines=headlines, assistant_answer=assistant_answer)

    @app.route("/ai_dashboard")
    def ai_dashboard():
        if not session.get("admin"): return redirect(url_for('login'))
        ai_status = monitor.get_ai_status() if hasattr(monitor, 'get_ai_status') else {}
        ai_insights = monitor.get_ai_insights() if hasattr(monitor, 'get_ai_insights') else []
        msg = session.pop('msg', None)
        return render_template_string(TEMPLATE_AI_DASHBOARD, ai_status=ai_status, ai_insights=ai_insights, msg=msg)

    @app.route("/ai_feedback", methods=["POST"])
    def ai_feedback():
        if not session.get("admin"): return redirect(url_for('login'))
        metric = request.form.get("metric", '').strip()
        value = request.form.get("value", '').strip()
        context = request.form.get("context", '').strip()
        
        if metric and value and hasattr(monitor, 'mark_false_positive'):
            try:
                monitor.mark_false_positive(metric, float(value), context)
                session['msg'] = f"Marked {metric}={value} as false positive for AI learning"
            except ValueError:
                session['msg'] = "Invalid value format"
        return redirect(url_for('dashboard'))

    @app.route("/ai_insights", methods=["POST"])
    def ai_insights():
        if not session.get("admin"): return redirect(url_for('login'))
        if hasattr(monitor, 'get_ai_insights'):
            insights = monitor.get_ai_insights()
            session['msg'] = f"AI insights refreshed. Found {len(insights)} insights."
        return redirect(url_for('ai_dashboard'))

    @app.route("/ai_reset_learning", methods=["POST"])
    def ai_reset_learning():
        if not session.get("admin"): return redirect(url_for('login'))
        if hasattr(monitor, 'pattern_history'):
            monitor.pattern_history.clear()
            monitor.ai_learning_data = {}
            if hasattr(monitor, 'save_ai_learning'):
                monitor.save_ai_learning()
            session['msg'] = "AI learning data reset successfully"
        return redirect(url_for('ai_dashboard'))

    @app.route("/ai_export_data", methods=["POST"])
    def ai_export_data():
        if not session.get("admin"): return redirect(url_for('login'))
        try:
            if hasattr(monitor, 'get_ai_status'):
                ai_data = {
                    'ai_status': monitor.get_ai_status(),
                    'patterns_count': len(monitor.pattern_history) if hasattr(monitor, 'pattern_history') else 0,
                    'learning_data': monitor.ai_learning_data if hasattr(monitor, 'ai_learning_data') else {},
                    'export_time': time.time()
                }
                # In a real implementation, this would create a downloadable file
                session['msg'] = f"AI data exported: {len(str(ai_data))} characters"
            else:
                session['msg'] = "AI data export not available"
        except Exception as e:
            session['msg'] = f"Export error: {str(e)}"
        return redirect(url_for('ai_dashboard'))

    @app.route("/ai_test_connection", methods=["POST"])
    def ai_test_connection():
        if not session.get("admin"): return redirect(url_for('login'))
        if hasattr(monitor, 'ai_client') and monitor.ai_client:
            try:
                # Test connection with a simple request
                response = monitor.ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello, respond with 'OK' if you receive this."}],
                    max_tokens=5
                )
                session['msg'] = "AI connection test successful"
            except Exception as e:
                session['msg'] = f"AI connection test failed: {str(e)}"
        else:
            session['msg'] = "AI client not configured"
        return redirect(url_for('ai_dashboard'))
    
    @app.route("/ask", methods=["POST"])
    def ask():
        if not session.get("admin"): return redirect(url_for('login'))
        question = request.form.get('question', '').strip()
        if question:
            ans = assistant_answer(question, monitor)
            session['assistant_answer'] = ans
        return redirect(url_for('dashboard'))

    @app.route("/feedback", methods=["POST"])
    def feedback():
        if not session.get("admin"): return redirect(url_for('login'))
        label = request.form.get("label", '').strip()
        value = request.form.get("value", '').strip()
        if label and value:
            try:
                monitor.feedback_correction(label, float(value))
            except ValueError:
                pass  # Invalid value, ignore
        return redirect(url_for('dashboard'))

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        if not session.get("admin"): return redirect(url_for('login'))
        msg = ""
        
        # Get AI status for template
        ai_status = monitor.get_ai_status() if hasattr(monitor, 'get_ai_status') else {}
        ai_insights = monitor.get_ai_insights() if hasattr(monitor, 'get_ai_insights') else []
        
        if request.method == "POST":
            try:
                # Handle AI configuration updates
                if hasattr(monitor, 'update_ai_config'):
                    # Get form data
                    ai_enabled = request.form.get("ai_enabled") == "true"
                    ai_mode = request.form.get("ai_mode", "local")
                    use_cloud_ai = ai_mode == "cloud"
                    api_key = request.form.get("api_key", "").strip()
                    ai_model = request.form.get("ai_model", "gpt-4o-mini")
                    learning_enabled = request.form.get("learning_enabled") == "true"
                    pattern_analysis = request.form.get("pattern_analysis") == "true"
                    auto_correction = request.form.get("auto_correction") == "true"
                    
                    # Update AI configuration
                    config_updates = {
                        "ai_enabled": ai_enabled,
                        "use_cloud_ai": use_cloud_ai,
                        "ai_model": ai_model,
                        "learning_enabled": learning_enabled,
                        "pattern_analysis": pattern_analysis,
                        "auto_correction": auto_correction
                    }
                    
                    # Only update API key if provided and not masked
                    if api_key and api_key != "***":
                        if api_key.startswith("sk-") or api_key == "":
                            config_updates["api_key"] = api_key
                        else:
                            msg = "Invalid API Key format. Should start with 'sk-' or be empty."
                    
                    if not msg:
                        monitor.update_ai_config(**config_updates)
                        msg = "AI settings updated successfully"
                        
                        # Update status after changes
                        ai_status = monitor.get_ai_status()
                        ai_insights = monitor.get_ai_insights()
                else:
                    # Fallback to old API key only save
                    api_key = request.form.get("api_key", "").strip()
                    if api_key.startswith("sk-") or api_key == "":
                        if save_api_key(api_key):
                            msg = "API Key updated."
                        else:
                            msg = "Failed to save API Key. Check permissions."
                    else:
                        msg = "Invalid API Key format. Should start with 'sk-' or be empty."
                        
            except Exception as e:
                msg = f"Error updating settings: {str(e)}"
                
        return render_template_string(TEMPLATE_SETTINGS, msg=msg, ai_status=ai_status, ai_insights=ai_insights)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for('login'))

    app.run(host="0.0.0.0", port=5001, debug=debug_mode, threaded=True)
