from datetime import datetime
import os
import sys

from scanner import scan_market

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config

from servicemodels import Trade, ScanResult, Position, db
#from app import app
import alpaca_trade_api as tradeapi
import time
from utils import get_top_symbols_from_db

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
    #with app.app_context():
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

def update_position(symbol, qty, price, side):
    pos = Position.query.filter_by(symbol=symbol).first()

    if side == "buy":
        if pos:
            total_qty = pos.qty + qty
            pos.avg_price = (pos.avg_price * pos.qty + price * qty) / total_qty
            pos.qty = total_qty
        else:
            pos = Position(
                symbol=symbol,
                qty=qty,
                avg_price=price
            )
            db.session.add(pos)

    elif side == "sell":
        if pos:
            pos.qty -= qty
            if pos.qty <= 0:
                db.session.delete(pos)

    db.session.commit()

def evaluate_position(symbol):
    pos = Position.query.filter_by(symbol=symbol).first()
    if not pos:
        return "NO_POSITION"

    entry = pos.avg_price
    current = pos.current_price
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

    # 2️⃣ 持仓管理（核心）
    #manage_positions()

def refresh_positions():
    positions = Position.query.all()

    for pos in positions:
        current = float(api.get_latest_trade(pos.symbol).price)

        pos.current_price = current
        pos.pnl = (current - pos.avg_price) * pos.qty
        pos.updated_at = datetime.utcnow()

    db.session.commit()    

def rebuild_positions(conn):
    cursor = conn.cursor()

    # 1️⃣ 获取所有 trades
    cursor.execute("""
        SELECT symbol, side, quantity, price
        FROM trades
        ORDER BY symbol, timestamp
    """)
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

        cursor.execute("""
            INSERT INTO position (symbol, quantity, avg_price, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (symbol, pos["qty"], avg_price))

    conn.commit()

#def update_scan_results(symbol_scores: dict):
def update_scan_results():    
    from scanner import scan_market
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

def run_manual_trade():    
    print("=== MANUAL TRADE START ===")

    clock = api.get_clock()

    if not clock.is_open:
        print("Market closed, skip trade")
    #        return []

    update_scan_results()

    # 1️⃣ 刷新持仓价格
    refresh_positions()

    # 2️⃣ 获取数据
    symbols_to_buy = get_top_symbols_from_db()   # ScanResult
    positions = Position.query.all()

    # 3️⃣ 处理已有持仓（SELL / HOLD）
    for pos in positions:
        action = evaluate_position(pos.symbol)

        print("Position:", pos.symbol, action)

        if "sell" in action:
            api.submit_order(
                symbol=pos.symbol,
                qty=pos.qty,
                side="sell",
                type="market",
                time_in_force="day"
            )

            update_position(pos.symbol, pos.qty, pos.current_price, "sell")

    # 4️⃣ 处理买入（避免重复买）
    existing_symbols = [p.symbol for p in positions]

    for symbol in symbols_to_buy:
        if symbol in existing_symbols:
            continue  # 已持仓就不买

        price = float(api.get_latest_trade(symbol).price)

        api.submit_order(
            symbol=symbol,
            qty=5,
            side="buy",
            type="market",
            time_in_force="day"
        )

        update_position(symbol, 5, price, "buy")

    print("=== MANUAL TRADE END ===")

from collections import defaultdict

def rebuild_positions():
    trades = Trade.query.order_by(Trade.symbol, Trade.timestamp).all()

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

"""
symbol_scores = {
    "AAPL": {"score": 0.92, "price": 180},
    "TSLA": {"score": 0.88, "price": 250},
    ...
}
"""


def run():
    df = scan_market()
    print(df)

    save_scan(df)
    execute_trades(df)

#while True:
#    run()
#    time.sleep(300)  # 每5分钟扫描

def run_trades():
     df = scan_market()
     execute_trades(df)