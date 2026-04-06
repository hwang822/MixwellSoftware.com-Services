import os, sys
from flask import Blueprint, Flask, render_template
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from flask import Flask, render_template

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport
servicename = "Trading"  
servicedb = f"{Config.SQLALCHEMY_DATABASE_URI}/{servicename}_{serviceport}"
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb.lower()}" 

from servicemodels import db, Position, ScanResult # scan_market, get_trades, get_scan_symbols, get_pnls
from trading import run_manual_trader, run_auto_trader
from trading_service import sync_trades_from_alpaca, update_scan_results, get_final_symbols, trade_executor, check_sell_signals, scan_market

db.init_app(app)

tradingService = Blueprint("tradingService", __name__)
#@tradingService.route("/")
def home1():    
    positions = Position.query.all()
    scans = ScanResult.query.order_by(ScanResult.score.desc()).limit(10).all()

    return render_template(
        "trading.html",
        positions=positions,
        scans=scans)


from flask import Flask, render_template_string, request
import requests
import json
import time
import random

app = Flask(__name__)

# ------------------------------
# MOCK TRADING FUNCTIONS (replace with real ones)
# ------------------------------

def sync_trades_from_alpaca_bt():
    return sync_trades_from_alpaca()
    #return [{"symbol": "AAPL", "qty": 10}, {"symbol": "TSLA", "qty": 5}]

def update_scan_results_bt():
    return update_scan_results()
    #return [{"symbol": "NVDA", "score": 95}, {"symbol": "MSFT", "score": 90}]

def get_final_symbols_bt():
    return get_final_symbols()
    #return ["NVDA", "MSFT", "AAPL"]

def trade_executor_bt(symbols):
    return trade_executor()
    #return [{"symbol": s, "action": "BUY", "price": random.randint(100,300)} for s in symbols]

def check_sell_signals_bt():
    return check_sell_signals()
    #return [{"symbol": "TSLA", "signal": "SELL"}]

# ------------------------------
# HTML TEMPLATE
# ------------------------------
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background: #f4f4f4; }
        button { padding: 6px 12px; margin: 5px; }
    </style>
</head>
<body>

<h1>📊 Trading Control Panel</h1>

<form method="get">
    <button name="run" value="sync">Run Sync Trades</button>
    <button name="run" value="scan">Run Scan</button>
    <button name="run" value="symbols">Get Symbols</button>
    <button name="run" value="trade">Execute Trade</button>
    <button name="run" value="sell">Check Sell</button>
    <button name="run" value="all">Run ALL</button>
</form>

<hr>
<h2>Results</h2>
{{ content|safe }}

</body>
</html>
"""

# ------------------------------
# RENDER
# ------------------------------

def render_chart(data):
    labels = []
    values = []

    for i, row in enumerate(data):
        labels.append(row.get("symbol", str(i)))
        values.append(row.get("price") or row.get("score") or 0)

    return f"""
    <canvas id='chart'></canvas>
    <script>
    const ctx = document.getElementById('chart');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {labels},
            datasets: [{{
                label: 'Values',
                data: {values}
            }}]
        }}
    }});
    </script>
    """


def render_table(data):
    if not isinstance(data, list) or len(data) == 0:
        return f"<pre>{data}</pre>"

    headers = data[0].keys()
    html = "<table><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"

    for row in data:
        html += "<tr>" + "".join(f"<td>{row.get(h, '')}</td>" for h in headers) + "</tr>"

    html += "</table>"
    return html


def render(data):
    if isinstance(data, list) and len(data) > 0:
        keys = data[0].keys()
        if "price" in keys or "score" in keys:
            return render_chart(data) + render_table(data)
        return render_table(data)

    return f"<pre>{json.dumps(data, indent=2)}</pre>"

# ------------------------------
# ROUTE
# ------------------------------

@tradingService.route("/")
def home():

    action = request.args.get("run")

    result = "Click a button"

    if action == "sync":
        result = sync_trades_from_alpaca_bt()

    elif action == "scan":
        result = update_scan_results_bt()

    elif action == "symbols":
        result = get_final_symbols_bt()

    elif action == "trade":
        symbols = get_final_symbols_bt()
        result = trade_executor(symbols)

    elif action == "sell":
        result = check_sell_signals_bt()

    elif action == "all":
        s1 = sync_trades_from_alpaca_bt()
        s2 = update_scan_results_bt()
        s3 = get_final_symbols_bt()
        s4 = trade_executor_bt(s3)
        s5 = check_sell_signals_bt()

        result = {
            "sync": s1,
            "scan": s2,
            "symbols": s3,
            "trade": s4,
            "sell": s5
        }

    html = render(result)

    return render_template_string(TEMPLATE, content=html)

# ------------------------------
# RUN
# ------------------------------


def create_app():
    app.register_blueprint(tradingService)
    return app

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
        sync_trades_from_alpaca()
        #scan_market()        
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

