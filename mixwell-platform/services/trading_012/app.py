import os, sys
from flask import Blueprint, Flask, render_template
from trading_service import get_top_symbols, scan_top_50_symbols, update_daily_prices, scan_market_store, get_daytrading, get_positions, get_activities, get_final_symbols, sync_trades_from_alpaca, update_scan_results, get_final_symbols, trade_executor, check_sell_signals, scan_market, get_top_movers

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
from trading import run_manual_trader, run_auto_trader
db.init_app(app)

tradingService = Blueprint("tradingService", __name__)
# ===== Dashboard Page =====
@tradingService.route("/")
def home():
    return render_template("trading.html")

# ===== Day Prices =====
@tradingService.route("/api/day_prices")
def api_day_prices_all():
    symbols = ["AAPL", "NVDA", "TSLA", "AMD"]

    result = {}

    for s in symbols:
        rows = OneDayPrice.query.filter_by(symbol=s)\
            .order_by(OneDayPrice.timestamp.desc())\
            .limit(50).all()[::-1]

        result[s] = {
            "labels": [r.timestamp.strftime("%H:%M") for r in rows],
            "prices": [r.price_close for r in rows]
        }
    return result

# ===== Daily Prices =====
@tradingService.route("/api/daily_prices")
def api_daily_prices_all():
    symbols = ["AAPL", "NVDA", "TSLA", "AMD"]
    result = {}
    for s in symbols:
        rows = DailyPrice.query.filter_by(symbol=s)\
            .order_by(DailyPrice.date.desc())\
            .limit(50).all()[::-1]
        result[s] = {
            "labels": [r.date.strftime("%H:%M") for r in rows],
            "prices": [r.avg_price for r in rows]
        }
    return result

# ===== Positions =====
@tradingService.route("/api/positions")
def api_positions():
    rows = Position.query.all()
    return [
        {
            "symbol": r.symbol,
            "qty": r.quantity,
            "price": round(r.avg_price, 2),
            "time": r.updated_at.strftime("%m/%d %H:%M") if r.updated_at else ""
        }
        for r in rows
    ]

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


@app.route("/api/day_prices_all")
def api_day_prices_all():
    symbols = ["AAPL", "NVDA", "TSLA"]

    result = {}

    try:
        for s in symbols:        
            rows = OneDayPrice.query.filter_by(symbol=s)\
                .order_by(OneDayPrice.timestamp.desc())\
                .limit(50).all()[::-1]

            result[s] = {
                "labels": [r.timestamp.strftime("%H:%M") for r in rows],
                "prices": [r.price_close for r in rows]
            }
    except Exception as e:
        print (e)
    return result

"""


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

@tradingService.route("/scan_symbols_price", methods=["POST"])
def scan_symbols_price():
    df = scan_market_store()
    return df.to_json(orient="records")


@tradingService.route("/scan_symbols", methods=["POST"])
def scan_symbols():
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

@app.route("/api/daily_prices/<symbol>")
def get_daily_prices(symbol):
    rows = []
    #rows = DailyPrice.query.filter_by(symbol=symbol)\
    #    .order_by(DailyPrice.date).all()

    return {
        "labels": [r.date.strftime("%m/%d") for r in rows],
        "prices": [r.avg_price for r in rows]
    }
"""

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
        #scan_market_store()
        #update_daily_prices()
        #get_top_symbols()
        #scan_top_50_symbols()
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

