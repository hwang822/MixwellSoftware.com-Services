import os, sys
from flask import Blueprint, Flask, jsonify, render_template
import auto_trader
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import Utility
from flask import Flask, render_template
from servicemodels import Trade, ScanResult, db
from bot import run_manual_trade, rebuild_positions
#from auto_trader import auto_trader

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport
#Utility.kill_port_safe(serviceport)
servicename = "Trading"  
servicedb = f"{Config.SQLALCHEMY_DATABASE_URI}/{servicename}_{serviceport}"
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb.lower()}" 

db.init_app(app)

tradingService = Blueprint("tradingService", __name__)
@tradingService.route("/")
def home():    
    try:        
        trades = Trade.query.order_by(Trade.timestamp.desc()).all()
        scans = ScanResult.query.order_by(ScanResult.score.desc()).limit(3).all()
        pnl = 0
        buy_price = {}

        for t in reversed(trades):
            if t.side == "buy":
                buy_price[t.symbol] = t.price
            elif t.side == "sell" and t.symbol in buy_price:
                pnl += (t.price - buy_price[t.symbol])

        total_trades = len(trades)

        return render_template(
            f"{servicename.lower()}.html",
            trades=trades,
            scans=scans,
            pnl=round(pnl, 2),
            total_trades=total_trades,
            servicename = f"{servicename} Service"
        )

#        return render_template(f"{servicename.lower()}.html", servicename = f"{servicename} Service")        
    except Exception as e:
        print(e)

@tradingService.route("/scan", methods=["POST"])
def scan():
    from scanner import scan_market
    df = scan_market()

    return df.to_json(orient="records")

@tradingService.route("/start_auto", methods=["POST"])
def start_auto():
    return {"status": auto_trader.start()}

@tradingService.route("/stop_auto", methods=["POST"])
def stop_auto():
    return {"status": auto_trader.stop()}

@tradingService.route("/status")
def status():
    return {
        "running": auto_trader.running,
        "end_time": str(auto_trader.end_time)
    }

@tradingService.route("/admin/rebuild_positions")
def rebuild_positions_api():
    rebuild_positions()
    return jsonify({"status": "success", "message": "Positions rebuilt"})

@tradingService.route("/manual_trade", methods=["POST"])
def manual_trade():

    try:
        #with app.app_context():   # 🔥 关键（线程/非请求安全）
        run_manual_trade()

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
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

