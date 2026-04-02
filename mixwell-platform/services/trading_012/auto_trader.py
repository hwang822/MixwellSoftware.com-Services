import threading
import time
from datetime import datetime, timedelta
from bot import run_trade_for_symbols
from utils import get_top_symbols_from_db, calculate_total_pnl

class AutoTrader:
    def __init__(self):
        self.running = False
        self.end_time = None
        self.thread = None

    def start(self):
        if self.running:
            return "Already running"

        self.running = True
        self.end_time = datetime.now() + timedelta(days=3)

        self.thread = threading.Thread(target=self.run_loop)
        self.thread.start()

        return "Started"

    def stop(self):
        self.running = False
        return "Stopped"

def run_loop(self):
    while self.running:

        if datetime.now() > self.end_time:
            print("Auto trading finished")
            self.running = False
            break

        symbols = get_top_symbols_from_db()

        run_trade_for_symbols(symbols)

        # ✅ 全局风控
        total_pnl = calculate_total_pnl()

        print("Total PnL:", total_pnl)

        if total_pnl < -200:
            print("MAX LOSS REACHED, STOP")
            self.running = False
            break

        time.sleep(300)

auto_trader = AutoTrader()