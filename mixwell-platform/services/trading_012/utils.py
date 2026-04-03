from servicemodels import ScanResult, Trade
#from app import app

def calculate_total_pnl():
    #with app.app_context():
        trades = Trade.query.order_by(Trade.timestamp.asc()).all()

        pnl = 0
        buy_price = {}

        for t in trades:
            if t.side == "buy":
                buy_price[t.symbol] = t.price
            elif t.side == "sell" and t.symbol in buy_price:
                pnl += (t.price - buy_price[t.symbol])
                del buy_price[t.symbol]

        return pnl
    
def get_top_symbols_from_db():
    #with app.app_context():
        scans = ScanResult.query.order_by(ScanResult.score.desc()).limit(3).all()
        return [s.symbol for s in scans]