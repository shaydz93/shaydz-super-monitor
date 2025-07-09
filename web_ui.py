from flask import Flask, request, session, redirect, url_for, render_template_string
import hashlib, os, json

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
        openai.api_key = key
        prompt = f"""You are ShaydZ, a home network and security assistant. User question: {question}
        Most recent network status:
        {', '.join(monitor.status_report())}
        Recent anomalies:
        {', '.join(monitor.detect_anomaly()[0])}
        Current threat intelligence:
        {str(monitor.intel.intel_data)[:500]}
        Please explain, summarize, or answer as helpfully as possible."""
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role":"system","content":"You are a helpful network and security assistant."},
                      {"role":"user","content":prompt}],
            max_tokens=300,
            temperature=0.4,
        )
        return resp.choices[0].message['content']
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
<a href='/logout'>Logout</a>
<p>Status: {{status}}</p>
<p>Anomalies: {{anomalies}}</p>
<form method='post' action='/feedback'>
  <input name='label' placeholder='Anomaly Label'>
  <input name='value' placeholder='Value'>
  <button type='submit'>Mark False Positive</button>
</form>
<form method='post' action='/ask'>
  <input name='question' placeholder='Ask the Assistant...' style='width:80%%;'>
  <button type='submit'>Ask</button>
</form>
{% if assistant_answer %}
<div style='border:1px solid #ccc; margin-top:10px; padding:5px;'>
<b>S h a y d Z Assistant:</b><br>
{{assistant_answer}}
</div>
{% endif %}
<a href='/settings'>Assistant Settings</a>
<h3>Headlines:</h3>
<ul>
  {% for source, entries in headlines.items() %}
    <li><b>{{source}}</b>
      <ul>
        {% for t, l in entries %}
          <li><a href="{{l}}">{{t}}</a></li>
        {% endfor %}
      </ul>
    </li>
  {% endfor %}
</ul>
"""

TEMPLATE_SETTINGS = """
<h2>Assistant Settings</h2>
<form method='post' action='/settings'>
    <input name='api_key' placeholder='OpenAI API Key (sk-...)' style='width:70%%;'>
    <button type='submit'>Save API Key</button>
</form>
{% if msg %}<p>{{msg}}</p>{% endif %}
<a href='/dashboard'>Back to Dashboard</a>
"""

def run_admin_ui(monitor):
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
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
        anomalies, _ = monitor.detect_anomaly()
        anomalies = "<br>".join(anomalies)
        headlines = monitor.intel.intel_data if hasattr(monitor, 'intel') else {}
        assistant_answer = session.pop('assistant_answer', None)
        return render_template_string(TEMPLATE_DASH, status=status, anomalies=anomalies, headlines=headlines, assistant_answer=assistant_answer)
    
    @app.route("/ask", methods=["POST"])
    def ask():
        if not session.get("admin"): return redirect(url_for('login'))
        question = request.form.get('question')
        ans = assistant_answer(question, monitor)
        session['assistant_answer'] = ans
        return redirect(url_for('dashboard'))

    @app.route("/feedback", methods=["POST"])
    def feedback():
        if not session.get("admin"): return redirect(url_for('login'))
        label = request.form.get("label")
        value = request.form.get("value")
        monitor.feedback_correction(label, value)
        return redirect(url_for('dashboard'))

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        msg = ""
        if request.method == "POST":
            if save_api_key(request.form.get("api_key", "")):
                msg = "API Key updated."
            else:
                msg = "Failed to save API Key. Check permissions."
        return render_template_string(TEMPLATE_SETTINGS, msg=msg)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for('login'))

    app.run(host="0.0.0.0", port=5001, debug=False)
