import os, sys
from flask import Blueprint, Flask, render_template, request
import requests
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import db

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport

servicename = "SmartMeter"  
servicedb = f"{Config.SQLALCHEMY_DATABASE_URI}/{servicename}_{serviceport}"
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb.lower()}" 

db.init_app(app)
try:
    with app.app_context():        
        db.create_all()
except Exception as e:
    print(e)

smartMeter = Blueprint("smartMeter", __name__)
@smartMeter.route("/")
def home():    
    """
        try:        

            token_url = "https://services.smartmetertexas.net/v2/token/"
            
            payload = {
                "username": "YOUR_USERNAME",
                "password": "YOUR_PASSWORD"
            }

            headers = {"Content-Type": "application/json"}

            token_resp = requests.post(token_url, json=payload, headers=headers)

            if token_resp.status_code != 200:
                return f"Token error: {token_resp.text}"

            token = token_resp.json().get("access_token")

            data_url = "https://services.smartmetertexas.net/v2/15minintervalreads/"

            headers = {
                "Authorization": f"Bearer {token}"
            }

            params = {
                "esiid": "YOUR_ESIID",
                "startDate": "2024-01-01",
                "endDate": "2024-01-02"
            }

            data_resp = requests.get(data_url, headers=headers, params=params)

            return data_resp.text
        except Exception as e:
            print(e)
    """        
    return render_template("smartmeter.html", servicename = f"{servicename} Service")        

def smartmeter_home():
    try:
        url = "https://services.smartmetertexas.net/v2/token/"
        url = "https://services.smartmetertexas.net/v2/greenbutton/" 
        r = requests.post(url, timeout=5)
        return f"Status: {r.status_code}, Response: {r.text}"
    except Exception as e:
        print (e)
        return f"Error: {str(e)}"


from flask import Flask, render_template_string, request
import requests
import json
import time

app = Flask(__name__)

BASE_URL = "https://services.smartmetertexas.net/v2"

# ------------------------------
# TOKEN CACHE
# ------------------------------
TOKEN_CACHE = {
    "token": None,
    "expires": 0
}

USERNAME = "YOUR_USERNAME"
PASSWORD = "YOUR_PASSWORD"


def get_token():
    if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires"]:
        return TOKEN_CACHE["token"]

    url = f"{BASE_URL}/token/"
    payload = {"username": USERNAME, "password": PASSWORD}

    r = requests.post(url, json=payload, timeout=5)

    if r.status_code != 200:
        return None

    data = r.json()
    token = data.get("access_token")

    TOKEN_CACHE["token"] = token
    TOKEN_CACHE["expires"] = time.time() + 300  # cache 5 min

    return token

# ------------------------------
# HTML TEMPLATE
# ------------------------------
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Meter Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background: #f4f4f4; }
        pre { background: #111; color: #0f0; padding: 10px; }
    </style>
</head>
<body>

<h1>⚡ Smart Meter Texas Dashboard</h1>

<form method="get">
    ESIID: <input name="esiid" value="{{esiid}}">
    Start: <input name="start" value="{{start}}">
    End: <input name="end" value="{{end}}">
    <button type="submit">Query</button>
</form>

<h3>APIs</h3>
<ul>
    <li><a href="/api/15min?esiid={{esiid}}&start={{start}}&end={{end}}">15-Min Data</a></li>
    <li><a href="/api/daily?esiid={{esiid}}&start={{start}}&end={{end}}">Daily</a></li>
    <li><a href="/api/meter">Meter Info</a></li>
</ul>

<hr>
<h2>Output</h2>
{{ content|safe }}

</body>
</html>
"""

# ------------------------------
# AUTO RENDER
# ------------------------------

def render_chart(data):
    labels = []
    values = []

    for row in data:
        labels.append(row.get("time") or row.get("date") or "")
        values.append(row.get("usage") or row.get("kwh") or 0)

    return f"""
    <canvas id='chart'></canvas>
    <script>
    const ctx = document.getElementById('chart');
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {labels},
            datasets: [{{
                label: 'Usage',
                data: {values}
            }}]
        }}
    }});
    </script>
    """


def render_json(data):
    # Chart detection
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        keys = data[0].keys()
        if "usage" in keys or "kwh" in keys:
            return render_chart(data)

        # table fallback
        headers = keys
        html = "<table><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
        for row in data:
            html += "<tr>" + "".join(f"<td>{row.get(h, '')}</td>" for h in headers) + "</tr>"
        html += "</table>"
        return html

    if isinstance(data, dict):
        return f"<pre>{json.dumps(data, indent=2)}</pre>"

    if isinstance(data, str):
        if data.endswith(".mp4"):
            return f'<video controls width="600"><source src="{data}"></video>'
        if data.endswith(".pdf"):
            return f'<iframe src="{data}" width="100%" height="600"></iframe>'
        return f"<p>{data}</p>"

    return f"<pre>{data}</pre>"

# ------------------------------
# API CALL
# ------------------------------

def call_api(endpoint, params=None):
    token = get_token()

    if not token:
        return {"error": "Token failed"}

    headers = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/{endpoint}/"

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ------------------------------
# ROUTES
# ------------------------------

@app.route("/")
def home():
    esiid = request.args.get("esiid", "")
    start = request.args.get("start", "2024-01-01")
    end = request.args.get("end", "2024-01-02")

    return render_template_string(TEMPLATE, content="Ready", esiid=esiid, start=start, end=end)

@app.route("/api/<name>")
def api(name):
    esiid = request.args.get("esiid")
    start = request.args.get("start")
    end = request.args.get("end")

    mapping = {
        "15min": "15minintervalreads",
        "daily": "dailyreads",
        "meter": "meterInfo"
    }

    endpoint = mapping.get(name)

    params = {}
    if esiid:
        params["esiid"] = esiid
    if start:
        params["startDate"] = start
    if end:
        params["endDate"] = end

    data = call_api(endpoint, params)
    html = render_json(data)

    return render_template_string(TEMPLATE, content=html, esiid=esiid, start=start, end=end)

# ------------------------------
# RUN
# ------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)



def create_app():
    app.register_blueprint(smartMeter)
    return app

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
    create_app().run(host="127.0.0.1", port=serviceport)
