#from collections import defaultdict

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from datetime import datetime

class Account(db.Model):
    account_number = id = db.Column(db.String(100), primary_key=True)
    cash = db.Column(db.Float)
    equity = db.Column(db.Float)
    long_market_value = db.Column(db.Float)
    short_market_value = db.Column(db.Float)
    position_market_Value = db.Column(db.Float)
    created_at = db.Column(db.DateTime)

class Trade(db.Model):
    id = db.Column(db.String(100), primary_key=True)    #An ID for the activity. Always in :: format. Can be sent as page_token in requests to facilitate the paging of results.
    symbol = db.Column(db.String(20))                   #The symbol of the security being traded.
    side = db.Column(db.String(10))                     #buy or sell
    price = db.Column(db.Float)                         #The per-share price that the trade was executed at.
    qty = db.Column(db.Integer)                         #The number of shares involved in the trade execution.
    total_buy = db.Column(db.Float)                     #total cost buy of chash
    total_sell = db.Column(db.Float)                   #total cost sell of chash 
    total_qty = db.Column(db.Float)                     #total cost buy/sell of qty 
    pnl = db.Column(db.Float)                           #gain/loss
    reason = db.Column(db.String(255))                  #reason for sell/buy
    transaction_time = db.Column(db.DateTime)           #The time at which the execution occurred.

class ScanResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    score = db.Column(db.Float)
    price = db.Column(db.Float)
    volume = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Position(db.Model):
    __tablename__ = "position"
    symbol = db.Column(db.String(20), primary_key=True)
    quantity = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)    

class DailyPrice(db.Model):
    __tablename__ = "daily_prices"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), index=True)
    avg_price = db.Column(db.Float)
    date = db.Column(db.Date, index=True)
    
class OneDayPrice(db.Model):
    __tablename__ = "day_prices"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), index=True)
    price_open = db.Column(db.Float)
    price_close = db.Column(db.Float)
    volume = db.Column(db.Float)
    high = db.Column(db.Float)
    low = db.Column(db.Float)
    vw = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True)

##################################
# Update Scan Symbols
##################################
def update_symbols_scan():    
    #from scanner import scan_market
    try:
        df = scan_market()

        symbol_scores = df.to_json(orient="records")

        # 1️⃣ 排序（高 → 低）
        sorted_symbols = sorted(
            symbol_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        # 2️⃣ 清空旧数据（推荐方式）
        ScanResult.query.delete()

        # 3️⃣ 写入新数据
        for rank, (symbol, data) in enumerate(sorted_symbols, start=1):
            row = ScanResult(
                symbol=symbol,
                score=data["score"],
                price=data["price"],
                rank=rank,
                updated_at=datetime.utcnow()
            )
            db.session.add(row)

        db.session.commit()
    except Exception as e:
        print(e)

    rows = ScanResult.query.all()
    results = [
        {
            "symbol": r["symbol"],
            "score": round(r["score"], 2),
            "price": round(r["price"], 2),
            "volume": round(r["volume"], 2),
            "timestamp": r["timestamp"].strftime("%Y-%m-%d %H:%M")
        }
        for r in rows
    ]
    return results

