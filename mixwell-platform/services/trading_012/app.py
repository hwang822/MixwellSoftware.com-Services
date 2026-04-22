import os
import sys

from flask import Blueprint, Config, Flask, jsonify, render_template
from servicemodels import db
from tradingservice import update_symbols_trades, update_symbols_positions, update_user_account, update_symbols_scan, get_color, update_symbols_prices, auto_trade, update_last_trade_info

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

@tradingService.route("/api/day_prices")
def api_day_prices():            
    dayprices, lines = update_symbols_prices(False)         
    html = build_table_html(dayprices)
    return jsonify({
        "html": html,
        "lines": lines
    })    

@tradingService.route("/api/daily_prices")
def api_daily_prices():
    dailyprices, lines = update_symbols_prices(True)  
    html = build_table_html(dailyprices)
    return jsonify({
        "html": html,
        "lines": lines
    })    

@tradingService.route("/api/positions")
def api_positions():
    positions, bars = update_symbols_positions()  
    html = build_table_html(positions)
    return jsonify({
        "html": html,
        "bars": bars
    })    

@tradingService.route("/api/top_symbols")
def api_topsymbols():
    topsymbols, bars = update_symbols_scan()
    html = build_table_html(topsymbols)
    return jsonify({
        "html": html,
        "bars": bars
    })        

@tradingService.route("/api/trades")
def api_trades():
    trades, lines = update_symbols_trades()
    html = build_table_html(trades)
    return jsonify({
        "html": html,
        "lines": lines
    })    


@tradingService.route("/api/account")
def api_account():
    account = update_user_account()
    html = build_table_html(account)
    return html

# 👉 模拟交易（触发更新）
@tradingService.route("/api/run_trades")
def api_run_trade():    
    auto_trade()
    return jsonify({"status": "ok"})

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
        thead = "<tr>" + "".join([f"<th>{c}</th>" for c in cols]) + "</tr>"
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

def create_app():
    app.register_blueprint(tradingService)
    return app

# =========================

if __name__ == "__main__":
    #with app.app_context():    
    #    db.create_all()
    create_app().run(host="127.0.0.1", port=serviceport)
