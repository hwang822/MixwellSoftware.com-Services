import os, sys
from flask import Blueprint, Flask, render_template
from trading_service import get_daytrading, get_positions, get_activities, get_final_symbols, sync_trades_from_alpaca, update_scan_results, get_final_symbols, trade_executor, check_sell_signals, scan_market, get_top_movers

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

from servicemodels import db, scan_market, get_trades, get_scan_symbols, get_pnls
from trading import run_manual_trader, run_auto_trader
db.init_app(app)

tradingService = Blueprint("tradingService", __name__)
@tradingService.route("/")
def home():    
    try:        
        trades = get_activities() #get_trades() # Trade.query.order_by(Trade.timestamp.desc()).all()
        scans = get_final_symbols() #get_scan_symbols() # ScanResult.query.order_by(ScanResult.score.desc()).limit(3).all()        
        positions = get_positions()
        #prices = get_daytrading()
        pnls = get_pnls(trades)
        ##pnls = scan_market()

        total_trades = len(trades)

        return render_template(
            f"{servicename.lower()}.html",
            trades=trades,
            scans=scans,
            positions=positions,
            pnl=round(pnls, 2),
            total_trades=total_trades,
            servicename = f"{servicename} Service"
        )

#        return render_template(f"{servicename.lower()}.html", servicename = f"{servicename} Service")        
    except Exception as e:
        print(e)

@app.route("/api/pnl")
def pnl():
    trades = get_daytrading()
    total = 0
    pnl_data = []

    for t in trades:
        if t.side == "SELL":
            total += t.price * t.quantity
        else:
            total -= t.price * t.quantity

        pnl_data.append(total)

    return {"pnl": pnl_data}

@tradingService.route("/scan", methods=["POST"])
def scan():
    df = scan_market()
    return df.to_json(orient="records")

@tradingService.route("/start_auto_trader", methods=["POST"])
def start_auto():
    return {"status": run_auto_trader.start()}

@tradingService.route("/stop_auto_trader", methods=["POST"])
def stop_auto():
    return {"status": run_auto_trader.stop()}

@tradingService.route("/trader_status")
def status():
    return {
        "running": run_auto_trader.running,
        "end_time": str(run_auto_trader.end_time)
    }

@tradingService.route("/start_manual_trader", methods=["POST"])
def manual_trade():

    try:
        #with app.app_context():   # 🔥 关键（线程/非请求安全）
        run_manual_trader()

        return {"status": "success"}

    except Exception as e:
        print(e)
        return {"status": "error", "msg": str(e)}
    
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
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

