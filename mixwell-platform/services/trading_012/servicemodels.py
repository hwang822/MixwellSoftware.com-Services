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
    type = db.Column(db.String(20))                     #fill or partial_fill
    reason = db.Column(db.String(255))                  #reason for sell/buy
    pnl = db.Column(db.Float)                           #gain/loss
    total_price = db.Column(db.Float)                   #total price = price*total_qty
    total_cost = db.Column(db.Float)                    #total cost buy/sell of chash 
    total_qty = db.Column(db.Float)                     #total cost buy/sell of qty 
    activity_type = db.Column(db.String(10))            #For trade activities, this will always be FILL
    cum_qty = db.Column(db.Integer)         	        #The cumulative quantity of shares involved in the execution.
    leaves_qty = db.Column(db.Integer)                  #For partially_filled orders, the quantity of shares that are left to be filled.
    order_id = db.Column(db.String(100))                #The id for the order that filled
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
    #__table_args__ = (
    #    db.UniqueConstraint("symbol", "timestamp", name="uix_symbol_date"),
    
    """

    def get_trades():
        trades = Activities.query.order_by(Activities.timestamp.desc()).all()
        return trades 

    def get_scan_symbols():    
        symbos = ScanResult.query.order_by(ScanResult.score.desc()).limit(3).all()
        return symbos

    def get_pnls(trades):    
        pnl = 0
        buy_price = {}
        for t in reversed(trades):
            if t.side == "buy":
                buy_price[t.symbol] = t.price
            elif t.side == "sell" and t.symbol in buy_price:
                pnl += (t.price - buy_price[t.symbol])
        return pnl

    def save_trades(symbol, side, qty, price):
        db.session.add(Trade(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price
        ))
        db.session.commit()    

    def save_scans(df):
        for _, row in df.iterrows():
            db.session.add(ScanResult(
                symbol=row["symbol"],
                score=row["score"],
                price=row["price"],
                volume=row["volume"]
            ))
        db.session.commit()

    def get_top_symbols_from_db():
        scans = ScanResult.query.order_by(ScanResult.score.desc()).limit(3).all()
        return [s.symbol for s in scans]

    def calculate_total_pnl():
        trades = Activities.query.order_by(Activities.timestamp.asc()).all()
        pnl = 0
        buy_price = {}
        for t in trades:
            if t.side == "buy":
                buy_price[t.symbol] = t.price
            elif t.side == "sell" and t.symbol in buy_price:
                pnl += (t.price - buy_price[t.symbol])
                del buy_price[t.symbol]
        return pnl

    import os
    import sys

    import alpaca_trade_api as tradeapi
    import pandas as pd
    #from config import *
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    sys.path.insert(0, f"{base_dir}")
    from config.settings import Config

    api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)


    SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

    def scan_market():

        results = []

        for symbol in SYMBOLS:
            bars = api.get_bars(symbol, "1Min", limit=30, adjustment='raw').df

            if len(bars) < 2:
                continue

            change = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0]
            volume = bars["volume"].mean()

            score = change * volume

            results.append({
                "symbol": symbol,
                "score": score,
                "price": bars["close"].iloc[-1],
                "volume": volume
            })
            
        df = pd.DataFrame(results)
        df = df.sort_values("score", ascending=False)

        return df.head(3)  # 选Top 3

    ##################################
    # Update Scan Symbols
    ##################################
    def update_symbols_scan():    
        #from scanner import scan_market
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

        return sorted_symbols

    ##################################
    # Run Trades
    ##################################

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

            save_trades(symbol, "buy", 5, row["price"])


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

        save_scans(df)
        execute_trades(df)

    #while True:
    #    run()
    #    time.sleep(300)  # 每5分钟扫描

    def run_trades():
        df = scan_market()
        execute_trades(df)



    
    ##################################
    # Update Positions  # 2️⃣ 持仓管理（核心）#manage_positions()
    ##################################
    def refresh_positions():
        positions = Position.query.all()

        for pos in positions:
            current = float(api.get_latest_trade(pos.symbol).price)

            pos.current_price = current
            pos.pnl = (current - pos.avg_price) * pos.quantity
            pos.updated_at = datetime.utcnow()

        db.session.commit()    

    def rebuild_positions(conn):
        cursor = conn.cursor()

        # 1️⃣ 获取所有 trades
        cursor.execute(
            SELECT symbol, side, quantity, price
            FROM trades
            ORDER BY symbol, timestamp
        rows = cursor.fetchall()

        positions = {}

        # 2️⃣ 逐条重建
        for symbol, side, qty, price in rows:
            if symbol not in positions:
                positions[symbol] = {
                    "qty": 0,
                    "cost": 0   # total cost
                }

            pos = positions[symbol]

            if side == "BUY":
                pos["cost"] += qty * price
                pos["qty"] += qty

            elif side == "SELL":
                if pos["qty"] == 0:
                    continue  # 防御

                avg_price = pos["cost"] / pos["qty"]

                pos["qty"] -= qty
                pos["cost"] -= qty * avg_price

        # 3️⃣ 清空旧 position
        cursor.execute("DELETE FROM position")

        # 4️⃣ 写回 position 表
        for symbol, pos in positions.items():
            if pos["qty"] <= 0:
                continue

            avg_price = pos["cost"] / pos["qty"]


        conn.commit()


    def rebuild_positions():
        trades = Activities.query.order_by(Activities.symbol, Activities.timestamp).all()

        positions = defaultdict(lambda: {"qty": 0.0, "cost": 0.0})

        for t in trades:
            pos = positions[t.symbol]

            if t.side == "buy":
                pos["cost"] += t.qty * t.price
                pos["qty"] += t.qty

            elif t.side == "sell":
                if pos["qty"] <= 0:
                    continue  # 防御

                avg_price = pos["cost"] / pos["qty"]

                pos["qty"] -= t.quantity
                pos["cost"] -= t.quantity * avg_price

        # 🧹 清空旧表
        Position.query.delete()

        # 📝 写入新数据
        for symbol, pos in positions.items():
            if pos["qty"] <= 0:
                continue

            avg_price = pos["cost"] / pos["qty"]

            db.session.add(Position(
                symbol=symbol,
                quantity=round(pos["qty"], 4),
                avg_price=round(avg_price, 4),
                updated_at=datetime.utcnow()
            ))

        db.session.commit()

    from datetime import datetime

    def update_position(symbol, qty, price, side):
        pos = Position.query.filter_by(symbol=symbol).first()

        if side == "buy":
            if pos:
                total_qty = pos.quantity + qty
                pos.avg_price = (pos.avg_price * pos.quantity + price * qty) / total_qty
                pos.quantity = total_qty
            else:
                pos = Position(
                    symbol=symbol,
                    qty=qty,
                    avg_price=price
                )
                db.session.add(pos)

        elif side == "sell":
            if pos:
                pos.quantity -= qty
                if pos.quantity <= 0:
                    db.session.delete(pos)

        db.session.commit()

    def evaluate_position(symbol):
        pos = Position.query.filter_by(symbol=symbol).first()
        if not pos:
            return "NO_POSITION"

        entry = pos.avg_price
        current = 250 #pos.current_price
        pnl_pct = (current - entry) / entry

        # ❗策略（你可以调整）
        if pnl_pct < -0.03:
            return "SELL_STOP_LOSS"

        if pnl_pct > 0.05:
            return "SELL_TAKE_PROFIT"

        return "HOLD"

    def run_trade_for_symbols(symbols):

        # 1️⃣ 买入逻辑
        for symbol in symbols:
            price = float(api.get_latest_trade(symbol).price)

            api.submit_order(
                symbol=symbol,
                qty=5,
                side="buy",
                type="market",
                time_in_force="day"
            )

            update_position(symbol, 5, price, "buy")
    """