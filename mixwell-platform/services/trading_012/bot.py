import os
import sys

from scanner import scan_market

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

from servicemodels import Trade, ScanResult, db
#from app import app
import alpaca_trade_api as tradeapi
import time

api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)

def save_scan(df):
    #with app.app_context():
        for _, row in df.iterrows():
            db.session.add(ScanResult(
                symbol=row["symbol"],
                score=row["score"],
                price=row["price"],
                volume=row["volume"]
            ))
        db.session.commit()

def execute_trades(df):
    for _, row in df.iterrows():
        symbol = row["symbol"]

        api.submit_order(
            symbol=symbol,
            qty=5,
            side="buy",
            type="market",
            time_in_force="day"
        )

        save_trade(symbol, "buy", 5, row["price"])

def save_trade(symbol, side, qty, price):
    with app.app_context():
        db.session.add(Trade(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price
        ))
        db.session.commit()

def risk_control(symbol):
    try:
        position = api.get_position(symbol)

        entry = float(position.avg_entry_price)
        current = float(api.get_latest_trade(symbol).price)

        if current < entry * 0.97:
            print("STOP LOSS:", symbol)

            api.submit_order(
                symbol=symbol,
                qty=position.qty,
                side="sell",
                type="market",
                time_in_force="day"
            )

    except Exception as e:
        print("Risk control error:", e)        

def run_trade_for_symbols(symbols):
    for symbol in symbols:
        print("Trading:", symbol)

        api.submit_order(
            symbol=symbol,
            qty=5,
            side="buy",
            type="market",
            time_in_force="day"
        )   
    # ✅ 交易后立即检查
    risk_control(symbol)        

def run():
    df = scan_market()
    print(df)

    save_scan(df)
    execute_trades(df)

#while True:
    #run()
#    time.sleep(300)  # 每5分钟扫描