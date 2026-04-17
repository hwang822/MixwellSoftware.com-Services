from typing import Counter

from flask import Flask, jsonify, render_template
from tradingmolders import db, Trade
from trading_service import update_symbols_day_prices, update_symbols_daily_prices, update_symbols_trades, update_symbols_positions, update_user_account, update_symbols_scan
import random
from datetime import datetime
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trades.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# =========================
# 页面
# =========================

@app.route("/")
def home():
    return render_template("trading.html")

# =========================
# API - TABLE
# =========================

# =========================
# Mock 实时数据（之后换 Alpaca）
# =========================
#通用版本（支持：group + flat + expandable）


@app.route("/api/table/day_prices")
def api_day_prices():        
    dayprices = update_symbols_day_prices()         
    html = build_table_html(dayprices)
    return html

@app.route("/api/table/daily_prices")
def api_daily_prices():
    dailyprices = update_symbols_daily_prices()  
    html = build_table_html(dailyprices)
    return html

@app.route("/api/table/positions")
def api_positions():
    positions = update_symbols_positions()  
    html = build_table_html(positions)
    return html

@app.route("/api/table/top_symbols")
def api_topsymbols():
    topsymbols = update_symbols_scan()
    html = build_table_html(topsymbols)
    return html

@app.route("/api/table/trades")
def api_trades():
    trades = update_symbols_trades()
    html = build_table_html(trades)
    return html

@app.route("/api/table/account")
def api_account():
    account = update_user_account()
    data = [
        {"metric":"cash","value":12000},
        {"metric":"equity","value":18000},
        {"metric":"buying_power","value":24000}
    ]

    html = build_table_html(account)
    return html


##########################

# ==============================
# 模拟数据（你后面换成真实 trading table）
# ==============================

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




# ==============================
# Chart 数据构建
# ==============================
def build_chart_data():

    result_bar = []
    result_line = []

    symbols = set([t["symbol"] for t in TRADES])

    for sym in symbols:

        prices = DAY_PRICES.get(sym, [])
        trades = [t for t in TRADES if t["symbol"] == sym]

        avg_cost = trades[-1]["avg_cost"]

        # ===== BAR =====
        bar = {
            "symbol": sym,
            "color": COLOR_MAP.get(sym, "#ccc"),
            "bars": prices,
            "cost_line": avg_cost
        }

        # ===== LINE =====
        line = {
            "symbol": sym,
            "color": COLOR_MAP.get(sym, "#ccc"),
            "line": prices,
            "markers": [
                {
                    "time": t["time"],
                    "price": t["price"],
                    "action": t["action"],
                    "reason": t["reason"]
                } for t in trades
            ]
        }

        result_bar.append(bar)
        result_line.append(line)

    return result_bar, result_line


# 👉 交易触发更新
@app.route("/api/chart")
def api_chart_1():
    bar, line = build_chart_data()
    return jsonify({
        "bar": bar,
        "line": line
    })

@app.route("/api/barchart")
def api_barchart_1():
    result = build_bar_chart_json_test()
    return jsonify(result)

@app.route("/api/linechart")
def api_linechart_1():
    result = build_line_chart_json_test()
    return jsonify(result)

# 👉 模拟交易（触发更新）
@app.route("/api/trade")
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
    if isinstance(data, dict):
        groups = data.keys()    
        for group in groups:
            lastitem = data[group][-1]
            break
        cols = lastitem.keys()
        rows = lastitem.values()                    
        if len(rows) > 1:
            has_expand = True
    else:
        cols = data[0].keys()        
    
    thead = ""
    if has_expand:
        thead = "<tr><th></th>" + "".join([f"<th>{c}</th>" for c in cols]) + "</tr>"
    else:
        thead = "<tr>" + "".join([f"<th>{c}</th>" for c in cols]) + "</tr>"
    tbody = ""

    # ================= GROUPED MODE =================
    if has_expand:
        for i, row in enumerate(data):

            # ===== 主行 =====
            tbody += "<tr>"

            if has_expand:
                tbody += f"""
                <td id="btn_{i}" onclick="toggleRow('{i}')" style="cursor:pointer">[+]</td>
                """            
            lastitem = data[row][-1]
            values = lastitem.values()            
            for v in values:
                tbody += f"<td>{v}</td>"
            tbody += "</tr>"    

            # ===== child rows（关键修复）=====
            if has_expand:
                for item in data[row]:
                    tbody += f"<tr class='child child_{i}' style='display:none'>"

                    # 👉 按列对齐
                    if has_expand:
                        tbody += "<td></td>"   # button column                    

                    values= item.values()

                    for v in values:
                        # 👉 symbol 不显示
                        if v == "symbol":
                            tbody += "<td></td>"
                        else:
                            tbody += f"<td>{v}</td>"

                    tbody += "</tr>"                                                        

                    """
                    for c in cols:
                        # 👉 symbol 不显示
                        if c == "symbol":
                            tbody += "<td></td>"
                        else:
                            tbody += f"<td>{item.get(c,'')}</td>"

                    tbody += "</tr>"                                                        
                    """
    # ================= FLAT MODE =================
    else:
        for r in data:
            tbody += "<tr>"
            #tbody += "<td></td>"
            for c in cols:
                val = r.get(c, "")
                tbody += f"<td>{val}</td>"
            tbody += "</tr>"
    return f"""
    <table border="1" style="border-collapse:collapse;width:100%">
        <thead>{thead}</thead>
        <tbody>{tbody}</tbody>
    </table>
    """

# 📊 5. LINE CHART → JSON GENERATOR
def build_line_chart_json(data, schema):

    x_key = schema["chart"]["line"]["x"]
    y_key = schema["chart"]["line"]["y"]
    group = schema["chart"]["line"]["group"]

    result = {}

    for d in data:
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

def build_line_chart_json_test():
    return build_line_chart_json(data, schema)

#📊 6. BAR CHART → JSON GENERATOR
def build_bar_chart_json(data, schema):

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

def build_bar_chart_json_test():
    result = build_bar_chart_json(data, schema)
    return result


# =========================

if __name__ == "__main__":
    with app.app_context():    
        db.create_all()
    app.run(debug=True)