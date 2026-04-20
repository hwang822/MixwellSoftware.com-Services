import os
import sys

from flask import Blueprint, Config, Flask, jsonify, render_template
from servicemodels import db
from tradingservice import update_symbols_trades, update_symbols_positions, update_user_account, update_symbols_scan, update_symbols_day_prices_line
from tradingservice import get_color, update_symbols_scan_bar, update_symbols_day_prices, update_symbols_daily_prices, update_symbols_daily_prices_line, update_symbols_positions_bar
import random
from datetime import datetime


#app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trades.db"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

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

db.init_app(app)

tradingService = Blueprint("tradingService", __name__)

# =========================
# 页面
# =========================

@tradingService.route("/")
def home():
    return render_template("trading.html", servicename = f"{servicename} Service")

# =========================
# Mock 实时数据（之后换 Alpaca）
# =========================
#通用版本（支持：group + flat + expandable）

@tradingService.route("/api/barchart")
def api_barchart():
    result = build_bar_chart_json(data, schema)
    return jsonify(result)

@tradingService.route("/api/linechart")
def api_linechart():        
    result = build_line_chart_json(data, schema)
    return jsonify(result)

@tradingService.route("/api/barchart/positions")
def api_barchart_positionss():
    positionsBar = update_symbols_positions_bar()
    print (positionsBar)
    return jsonify(positionsBar)

@tradingService.route("/api/barchart/top_symbols")
def api_barchart_topsymbols():    
    result = update_symbols_scan_bar()
    return jsonify(result)

@tradingService.route("/api/barchart/trades")
def api_barchart_trades():
    result = update_symbols_trades()
    #result = build_bar_chart_json(data,schema)
    return jsonify(result)

@tradingService.route("/api/linechart/day_prices")
def api_linechart_dayprices():
    daypriceLine = update_symbols_day_prices_line()   
    return jsonify(daypriceLine)
@tradingService.route("/api/linechart/daily_prices")
def api_linechart_dailyprices():
    dailypriceLine = update_symbols_daily_prices_line()   
    return jsonify(dailypriceLine)


###### Table

@tradingService.route("/api/table/day_prices")
def api_day_prices():            
    dayprices, lines = update_symbols_day_prices(True)         
    html = build_table_html(dayprices)
    return jsonify({
        "html": html,
        "lines": lines
    })    

@tradingService.route("/api/table/daily_prices")
def api_daily_prices():
    dailyprices, lines = update_symbols_day_prices(False)  
    html = build_table_html(dailyprices)
    return jsonify({
        "html": html,
        "lines": lines
    })    

@tradingService.route("/api/table/positions")
def api_positions():
    positions, bars = update_symbols_positions()  
    html = build_table_html(positions)
    return jsonify({
        "html": html,
        "bars": bars
    })    

@tradingService.route("/api/table/top_symbols")
def api_topsymbols():
    topsymbols, bars = update_symbols_scan()
    html = build_table_html(topsymbols)
    return jsonify({
        "html": html,
        "bars": bars
    })        

@tradingService.route("/api/table/trades")
def api_trades():
    trades, lines = update_symbols_trades()
    html = build_table_html(trades)
    return jsonify({
        "html": html,
        "lines": lines
    })    

@tradingService.route("/api/table/account")
def api_account():
    account = update_user_account()
    html = build_table_html(account)
    return html

# 👉 模拟交易（触发更新）
@tradingService.route("/api/trades")
def api_trade():
    TRADES.append({
        "symbol": "AAPL",
        "time": datetime.now().strftime("%H:%M"),
        "action": "BUY",
        "price": random.randint(149, 155),
        "qty": 10,
        "avg_cost": 149,
        "reason": "Auto trade"
    })

    return jsonify({"status": "ok"})

##########################
# ==============================
# 模拟数据（你后面换成真实 trading table）
# ==============================
# =========================
# API - TABLE
# =========================

TRADES = [
    {
        "symbol": "AAPL",
        "time": "10:05",
        "action": "BUY",
        "price": 150,
        "qty": 10,
        "avg_cost": 148,
        "reason": "Breakout"
    },
    {
        "symbol": "AAPL",
        "time": "10:20",
        "action": "SELL",
        "price": 152,
        "qty": 10,
        "avg_cost": 148,
        "reason": "Take profit"
    }
]

COLOR_MAP = {
    "AAPL": "#00FF99",
    "NVDA": "#FFAA00"
}



# 👉 交易触发更新

# +++++++++++++++++++++++++


"""
🧠 1. FULL DESIGN (what you are building)
DATA (single source)
   ↓
SCHEMA (rules / mapping)
   ↓
├── TABLE HTML
└── CHART JSON    
"""

data = [
    {
        "symbol": "AAPL",
        "qty": 10,
        "avg_price": 148,
        "mv": 1500,
        "time": "10:00",
        "change_rate": 0.01
    },
    {
        "symbol": "AAPL",
        "qty": 10,
        "avg_price": 148,
        "mv": 1520,
        "time": "10:05",
        "change_rate": 0.02
    },
    {
        "symbol": "NVDA",
        "qty": 5,
        "avg_price": 880,
        "mv": 4500,
        "time": "10:00",
        "change_rate": -0.01
    },
    {
        "symbol": "NVDA",
        "qty": 5,
        "avg_price": 880,
        "mv": 4480,
        "time": "10:05",
        "change_rate": -0.015
    }
]

#⚙️ 3. SCHEMA (drives everything)
schema = {
    "table_columns": ["symbol", "qty", "avg_price", "mv"],

    "chart": {
        "line": {
            "x": "time",
            "y": "change_rate",
            "group": "symbol"
        },
        "bar": {
            "x": "symbol",
            "y": "change_rate"
        }
    }
}

def build_table_html(data):
    has_expand = False
    lastitem = {}
    if isinstance(data, dict):
        groups = data.keys()
        for group in groups:
            lastitem = data[group]["items"][-1]
            break
        cols = lastitem.keys()
        rows = lastitem.values()                    
        if len(rows) > 1:
            has_expand = True
    else:
        cols = data[0].keys()        
    
    thead = ""
    if has_expand:
        thead = "<tr><th></th>" + "".join([f"<th>{c}</th>" for c in cols]) + f"</tr>"
    else:
        thead = "<tr>" + "".join([f"<th>{c}\</th>" for c in cols]) + "</tr>"
    tbody = ""

    # ================= GROUPED MODE =================
    if has_expand:
        colors = {}
        items = {}
        for i, row in enumerate(data):
            colors = data[row]["colors"]
            items = data[row]["items"]        
            # ===== 主行 =====
            tbody += "<tr>"
            if has_expand:
                tbody += f"""
                <td id="btn_{i}" onclick="toggleRow('{i}')" style="cursor:pointer">[+]</td>
                """            
            lastitem = items[-1]            
            for k, v in lastitem.items():
                #tbody += f"<td>{v}</td>"
                if k == "symbol":
                    tbody += f"<td style='color:{colors}'>{v}</td>"
                else:
                    tbody += f"<td>{v}</td>"                
            tbody += "</tr>"    

            # ===== child rows（关键修复）=====
            if has_expand:
                for item in items:
                    tbody += f"<tr class='child child_{i}' style='display:none'>"

                    # 👉 按列对齐
                    if has_expand:
                        tbody += "<td></td>"   # button column                    
                    for k, v in item.items():
                        # 👉 symbol 不显示
                        if k == "symbol":
                            tbody += "<td></td>"
                        else:
                            tbody += f"<td>{v}</td>"

                    tbody += "</tr>"                                                        
                                    
    # ================= FLAT MODE =================
    else:
        for r in data:
            tbody += "<tr>"
            #tbody += "<td></td>"
            for c in cols:
                val = r.get(c, "")
                if c == "symbol":
                    colors = get_color(val)
                    tbody += f"<td style='color:{colors}'>{val}</td>"
                else:
                    tbody += f"<td>{val}</td>"                
            tbody += "</tr>"
    return f"""
    <table border="1" style="border-collapse:collapse;width:100%">
        <thead>{thead}</thead>
        <tbody>{tbody}</tbody>
    </table>
    """

# =========================
# API - TABLE
# =========================


# 📊 5. LINE CHART → JSON GENERATOR
def build_line_chart_json(data_input, schema):
    
    x_key = schema["chart"]["line"]["x"]
    y_key = schema["chart"]["line"]["y"]
    group = schema["chart"]["line"]["group"]

    result = {}

    for d in data_input:
        g = d[group]

        if g not in result:
            result[g] = []

        result[g].append({
            "x": d[x_key],
            "y": d[y_key]
        })

    return [
        {
            "symbol": k,
            "series": v
        }
        for k, v in result.items()
    ]


#📊 6. BAR CHART → JSON GENERATOR
def build_bar_chart_json(data, schema):

###########################


    x_key = schema["chart"]["bar"]["x"]
    y_key = schema["chart"]["bar"]["y"]

    # group by symbol (take latest value per symbol)
    latest = {}

    for d in data:
        latest[d["symbol"]] = d

    return [
        {
            "x": k,
            "y": v[y_key]
        }
        for k, v in latest.items()
    ]


def create_app():
    app.register_blueprint(tradingService)
    return app

# =========================

if __name__ == "__main__":
    with app.app_context():    
        db.create_all()
        #get_db_info()        
    #app.run(debug=True)
    create_app().run(host="127.0.0.1", port=serviceport)
