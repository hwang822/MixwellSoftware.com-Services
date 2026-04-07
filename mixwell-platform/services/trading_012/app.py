import os, sys
from flask import Blueprint, Flask, render_template
from trading_service import get_top_symbols, scan_top_50_symbols, update_symbols_positions, update_symbols_daily_prices, update_symbols_day_prices, get_daytrading, get_positions, get_activities, get_final_symbols, sync_trades_from_alpaca, update_scan_results, get_final_symbols, trade_executor, check_sell_signals, scan_market, get_top_movers

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

from servicemodels import db, scan_market, get_trades, get_scan_symbols, get_pnls, OneDayPrice, DailyPrice, Position, Activities, ScanResult
#from trading import run_manual_trader, run_auto_trader
db.init_app(app)

tradingService = Blueprint("tradingService", __name__)
# ===== Dashboard Page =====
@tradingService.route("/")
def home():
    return render_template("trading.html")

# ===== Day Prices =====
@tradingService.route("/api/day_prices")
def api_day_prices():
    result = update_symbols_day_prices()
    return result

# ===== Daily Prices =====
@tradingService.route("/api/daily_prices")
def api_daily_prices():
    result = update_symbols_daily_prices()
    return result

# ===== Positions =====
@tradingService.route("/api/positions")
def api_positions():
    result = update_symbols_positions()
    return result

# ===== Trades =====
@tradingService.route("/api/trades")
def api_trades():
    rows = Activities.query.order_by(Activities.timestamp.desc()).limit(50).all()

    return [
        {
            "symbol": r.symbol,
            "side": r.side,
            "price": r.price,
            "qty": r.qty,
            "time": r.timestamp.strftime("%H:%M")
        }
        for r in rows
    ]

# ===== Scan Results =====
@tradingService.route("/api/scansymbols")
def api_scan():
    rows = ScanResult.query.order_by(ScanResult.score.desc()).all()

    return [
        {
            "symbol": r.symbol,
            "score": round(r.score, 2),
            "price": round(r.price, 2),
            "volume": round(r.volume, 2),
            "timestamp": r.timestamp
        }
        for r in rows
    ]

def create_app():
    app.register_blueprint(tradingService)
    return app

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
        #sync_trades_from_alpaca()
        #update_scan_results()
        #symbols = get_final_symbols()
        #trade_executor(symbols)
        #check_sell_signals()
        #update_symbols_day_prices()
        #update_symbols_daily_prices()
        #get_top_symbols()
        #scan_top_50_symbols()
        #update_symbols_positions()
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

