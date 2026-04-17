from datetime import time
import os, sys
from flask import Blueprint, Flask, jsonify, render_template
from trading_service import update_user_account, update_symbols_positions, update_symbols_daily_prices, update_symbols_day_prices, update_symbols_trades, update_symbols_scan

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

from servicemodels import db
db.init_app(app)

# service codes
tradingService = Blueprint("tradingService", __name__)
# ===== Dashboard Page =====
@tradingService.route("/")
@app.route("/")
def home():
    return render_template("index.html")

# ===== Run Trades =====
@tradingService.route("/run_trade")
def run_trade():
    #auto_trade()    
    return jsonify({"status":"done"})

# ===== Day Prices =====
@tradingService.route("/api/day_prices")
def api_day_prices():
    result = update_symbols_day_prices()    
    return jsonify(result)

# ===== Daily Prices =====
@tradingService.route("/api/daily_prices")
def api_daily_prices():
    result = update_symbols_daily_prices()
    return jsonify(result)

# ===== Positions =====
@tradingService.route("/api/positions")
def api_positions():
    result = update_symbols_positions()
    return jsonify(result)

# 全局内存（paper trading）
TRADES = []
POSITIONS = {}
CASH = 10000
LAST_PRICE = {}

# ===== Trades =====
@tradingService.route("/api/trades")
def api_trades():    
    #pos = run_cycle()
#    return jsonify(pos)
    result = update_symbols_trades()
    return jsonify(result)

# ===== User Account =====
@tradingService.route("/api/user_account")
def api_user_account():
    try:
        result = update_user_account()
        return jsonify(result)
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ===== Scan Results =====
@tradingService.route("/api/scansymbols")
def api_scan():
    result = update_symbols_scan()
    return jsonify(result)

def create_app():
    app.register_blueprint(tradingService)
    return app

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

