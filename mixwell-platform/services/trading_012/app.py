import os, sys
from flask import Blueprint, Flask, render_template
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
#from models import db
from flask import Flask, render_template
from servicemodels import Trade, ScanResult, db

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
@tradingService.route("/")
def home():    

    try:        
        trades = Trade.query.order_by(Trade.timestamp.desc()).limit(50).all()
        scans = ScanResult.query.order_by(ScanResult.score.desc()).limit(10).all()
        pnl = 0
        buy_price = {}

        for t in reversed(trades):
            if t.side == "buy":
                buy_price[t.symbol] = t.price
            elif t.side == "sell" and t.symbol in buy_price:
                pnl += (t.price - buy_price[t.symbol])

        return render_template(
            f"{servicename.lower()}.html",
            trades=trades,
            scans=scans,
            pnl=round(pnl, 2),
            servicename = f"{servicename} Service"
        )
    except Exception as e:
        print(e)

    #return render_template(f"{servicename.lower()}.html", servicename = f"{servicename} Service")        
@tradingService.route("/scan", methods=["POST"])
def scan():
    from scanner import scan_market
    df = scan_market()

    return df.to_json(orient="records")

def create_app():
    app.register_blueprint(tradingService)
    return app

if __name__ == "__main__":
    try:
        with app.app_context():        
            db.create_all()
    except Exception as e:
        print (e)
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

