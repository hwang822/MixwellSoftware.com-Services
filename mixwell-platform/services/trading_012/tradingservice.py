
import json
import os
import sys
import hashlib
from zoneinfo import ZoneInfo
import alpaca_trade_api as tradeapi
from datetime import date, datetime, time, timedelta, timezone
import pytz

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from servicemodels import Position, Trade, DailyPrice, db

api = tradeapi.REST(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, Config.ALPACA_BASE_URL)
SYMBOLS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "SPY"]

#get_alpaca_prices_api("AAPL", 1, "5min", 100)
#get_alpaca_prices_api("AAPL", 20, "1Day", 30)

def get_alpaca_prices_api(symbol, days, interval, limit, only_today=True):

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    bars = api.get_bars(
        symbol,
        interval,
        start=start.isoformat(),
        end=end.isoformat(),
        adjustment='raw',
        limit=limit,
        feed='iex'
    ).df

    result = []

    if not bars.empty:

        # ✅ remove forming bar
        if interval in ["1min", "5min", "15min"] and len(bars) > 1:
            bars = bars.iloc[:-1]
        today_est = datetime.now(
            ZoneInfo("America/New_York")
        ).date()

        #today_est = datetime.now(ZoneInfo("America/New_York")).date()

        for index, bar in bars.iterrows():

            # ✅ 先转 EST
            est = index.astimezone(ZoneInfo("America/New_York"))

            # ✅ 只取今天（可选）
            if only_today and est.date() != today_est:
                continue
            #interval_norm = interval.lower()
            # ✅ 只过滤交易时间（分钟级）
            if interval in ["1min", "5min", "15min"]:
                if not (time(9,30) <= est.time() <= time(16,0)):
                    continue

            # ✅ 时间格式
            if interval == "1Day":
                ts = est.strftime("%Y-%m-%d")
            else:
                ts = est.strftime("%Y-%m-%d %H:%M")

            result.append({
                "timestamp": ts,
                "symbol": symbol,
                "price_close": bar.close,
                "qty": 0,
                "mv": 0,
                "mv_ref": 0,
                "mv_change($)": 0,
                "cost": 0,
                "pnl": 0,
                "pct": 0,
                "total_pnl": 0,
                "action" : None,
                "notes" : None,
                "price_low": bar.low,
                "price_high": bar.high,
                "volume" : bar.volume,
                "node" : None
            })

    return result

def get_top_symbols():
    assets = api.list_assets(status='active')
    symbols = [
        a.symbol for a in assets
        if a.tradable and a.exchange in ["NASDAQ", "NYSE"]
    ]

    return symbols

def get_color(symbol):
    h = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
    #hue = h % 360
    index = h % 360
    hue = (index * 137.508) % 360
    return f"hsl({hue}, 70%, 50%)"

SYMBOL_COLORS = {}
for symbol in SYMBOLS:
    SYMBOL_COLORS[symbol] = get_color(symbol) 

ACTION_ICONS = {
    "buy":  "path://M512 128 L896 768 L128 768 Z",   # ▲
    "sell": "path://M128 256 L896 256 L512 896 Z",   # ▼
    "hold": "path://M512 128 A384 384 0 1 1 511 128 Z",  # ●
    "skip": "path://M128 128 H896 V896 H128 Z"       # ■
}

def utc_to_est(time_str):
    # 1️⃣ 解析 UTC 字符串
    dt_utc = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    #dt_utc = datetime.strptime(time_str.replace("Z", "+00:00"))
    dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))

    # 2️⃣ 转换到纽约时区（自动 EST / EDT）
    dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))

    # 3️⃣ 输出字符串
    return dt_est.strftime("%Y-%m-%d %H:%M")


#计算 最近变化


def scan_market():

    results = []

    for symbol in SYMBOLS:

        bars = get_alpaca_prices_api(symbol, 1, "5min", 100, False)

        if len(bars) < 2:
            continue
        first = bars[0]
        last  = bars[-1]

        change = (last["price_close"] - first["price_close"]) / first["price_close"]
        volume = sum(b["volume"] for b in bars) / len(bars)
        score  = change * volume
        results.append({
            "symbol": symbol,
            "change": change,
            "volume": volume,
            "score": score
        })

        results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results


##################
# new models
##################
def get_latest_trade(symbol):
    trade = api.get_latest_trade(symbol)
    return trade # float(trade.price)


def get_symbol_position(symbol):
    positions = api.list_positions()
    pos = next((p for p in positions if p.symbol == symbol), None)
    return pos

def get_ny_time_now():
    dt = datetime.now(ZoneInfo("America/New_York"))
    return dt.strftime("%Y-%m-%d %H:%M")

def is_trading_time(ts):

    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)     

    d = ts.date()
    t = ts.time()
    # 上午 09:30–12:00
    return time(9, 30) <= t <=  time(16, 0)
    # 09:30 - 16:00 

def is_best_trading_time(ts):

    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)     

    t = ts.time()

    # 上午 10:00–12:00
    morning = time(10, 0) <= t <= time(12, 0)

    # 下午 13:00–15:00
    afternoon = time(13, 0) <= t <= time(15, 0)

    # 09:30–10:00 → 开盘噪音（波动大 ❌）
    # 10:00–12:00 → 趋势稳定 ✅
    # 12:00–13:00 → 午盘低量 ❌
    # 13:00–15:00 → 主趋势延续 ✅
    # 15:00–16:00 → 收盘波动 ❌（除非你做收盘策略）

    return morning or afternoon

LOG_DIR = "logs"
def save_today_log(lines):
    try:
        # 👉 确保目录存在
        os.makedirs(LOG_DIR, exist_ok=True)
        file = os.path.join(LOG_DIR, "trading_log.json") #get_today_file())        
        with open(file, "w") as f:   # "w" = overwrite
            json.dump(lines, f, indent=2, default=str)
    except Exception as e:
        print (e)

def load_today_log(today=True):
    src_file = os.path.join(LOG_DIR, "trading_log.json")
    dse_file = os.path.join(LOG_DIR, "lastday_traking_log.json")
    if today:
        if not os.path.exists(src_file):
            return []
        with open(src_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 1️⃣ Delete old lastday file if exists
        if not os.path.exists(src_file):
            if os.path.exists(dse_file):
                with open(dse_file, "r", encoding="utf-8") as f:
                    return json.load(f)        
        else:            
            if os.path.exists(dse_file):
                os.remove(dse_file)
        # 2️⃣ Rename current → lastday
            os.rename(src_file, dse_file)
            with open(dse_file, "r", encoding="utf-8") as f:
                return json.load(f)        

def alpaca_trading_api():

    ## 📚 官方文档 👉 [https://alpaca.markets/docs/](https://alpaca.markets/docs/)

    ### 1️⃣ Account（账户）
    result = api.get_account()
    #print (result)
    ### 2️⃣ Orders（下单）

    #result = api.submit_order(symbol="AAPL",qty=10,side="buy", type="market",time_in_force="day")
    #print (result)
    
    #判断“今天是否是交易日”
    today = date.today()
    calendar = api.get_calendar(start=today.isoformat(), end=today.isoformat())

    if len(calendar) > 0:
        print("Today is a trading day")
    else:
        print("Today is NOT a trading day (weekend/holiday)")

    clock = api.get_clock()

    if clock.is_open:
        print("Market is OPEN now")
    else:
        print("Market is CLOSED now")

    ### 3️⃣ Positions（持仓）
    result = api.list_positions()
    #print (result)

    result = api.get_position("AAPL")
    #print (result)

    ### 4️⃣ Activities（你
    result = api.get_activities()
    #print (result)

    ### 5️⃣ Assets（股票列表）
    #result = api.list_assets()
    #print (result)

    ### 6️⃣ Market Data（行情）
    result = api.get_latest_trade("AAPL")
    #print (result)

    # get daily data
    end = datetime.utcnow()
    start = end - timedelta(days=2)        
    start = start.isoformat() + "Z",
    end = end.isoformat() + "Z",
    result = api.get_bars(
        "AAPL",
        "1Day", 
        start = start,
        end = end,
        adjustment = 'raw',
        feed='iex'
    ).df
    #print (result)

    #get mins data

    est = pytz.timezone("US/Eastern")
    now = datetime.now(est)
    # 今日开盘时间
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
    # 👉 转 UTC（Alpaca 必须）
    start = market_open.astimezone(pytz.utc)
    end = market_end.astimezone(pytz.utc)

    try:
        result = api.get_bars(  # not work at NY close time
            "AAPL",
            "5min", 
            #start = start,
            #end = end,
            adjustment = 'raw',
            feed='iex'
        ).df
    except Exception as e:    
        print(e)
    return   
#alpaca_trading_api()


#update_symbols_daily_prices()
################################
# update_symbols_prices()  #
###############################

def save_test_log(lines):
    try:
        # 👉 确保目录存在
        os.makedirs(LOG_DIR, exist_ok=True)
        file = os.path.join(LOG_DIR, "trading_test.json")         
        with open(file, "w") as f:   # "w" = overwrite
            json.dump(lines, f, indent=2, default=str)
    except Exception as e:
        print (e)


def load_test_log():
    src_file = os.path.join(LOG_DIR, "trading_test.json")
    if not os.path.exists(src_file):
        return []
    with open(src_file, "r", encoding="utf-8") as f:
            return json.load(f)

def get_alpaca_prices_test(symbol):
    src_file = os.path.join(LOG_DIR, "trading_test_data.json")
    if not os.path.exists(src_file):
        return []
    with open(src_file, "r", encoding="utf-8") as f:
        data = json.load(f)        
        result = data[symbol]["items"]                
        new_items = []
        for price in result:
            print (price)
            new_items.append({
                "symbol": symbol,
                "timestamp": price["timestamp"],
                "price_close":price["price_close"],
                "qty": 0,
                "mv": 0,
                "cost": 0,
                "mv_chagne($)": 0,
                "mv_ref": 0,                
                "pnl": 0,
                "pct": 0,
                "total_pnl": 0,
                "action" : None,
                "notes" : None,
                "price_low": price["price_low"],
                "price_high": price["price_high"],
                "volume" : price["volume"],
                "node" : None
            })
        #data[symbol]["items"].append(new_items)
    return new_items

def execut_order(symbol, side, test = False):
    if test: # not execut for test
        return
    pos = get_symbol_position(symbol)
    if pos:                
        if side == "sell":        
            sell_qty = pos.qty
            if sell_qty > 0:
                api.submit_order(symbol=symbol,qty= sell_qty,side= side,type="market",time_in_force="day") 
        else:  # to buy
            buy_qty = round(2000/pos.current_price)
            if buy_qty == 0:
                buy_price = pos.current_price
                if buy_price < 0:
                    buy_qty = round(2000/buy_price)                
                    api.submit_order(symbol=symbol,qty= buy_qty,side= side,type="market",time_in_force="day")  
    return


def should_trade(prices):
     
    curreent_prices = prices
    last_prices = prices[:-1]
    last_price = last_prices[-1]
    price = curreent_prices[-1]
    
    last_cost = last_price["cost"]
    last_mv = last_price["mv"]
    last_mv_ref = last_price["mv_ref"]
    last_qty = last_price["qty"]
    last_pnl = last_price["pnl"]
    last_total_pnl = last_price["total_pnl"]
    

    current_price = price["price_close"]
    current_qty = round(2000/current_price)
    current_mv = current_price*current_qty 
    price["mv"] = round(current_price*current_qty, 2)
    current_mv_change = 0
    if last_mv > 0:
        current_mv_change = current_mv - last_mv
    price["mv_change($)"] = current_mv

    return price 
    if len(prices)<5:        
        recent = last_prices
        last_mv_ref = min(p["price_close"] for p in recent) * current_qty 
    else:
        timestamp = price["timestamp"] 
        time = timestamp.split(" ")[1]
        current_price = price["price_close"]
        current_qty = round(2000/current_price)
        current_mv = current_price*current_qty 
        current_pnl = 0
        current_action = None
        price["mv"] = round(current_mv, 2)
        price["mv_change($)"] = round(current_mv_change, 2) 
        price["mv_ref"] = last_mv_ref
        if last_cost == 0:  # buy only                
            if time <= "15:50": # not buy after nytime 15:50
                if len(prices) > 5:
                    if current_mv_change > 3: # start up from lower
                        price["action"] = "buy"
                        price["notes"] = f"{current_action}: mv:{round(current_mv, 2)} - ref:{round(last_mv_ref, 2)} = {round((current_mv_change),2)}  > 3$ "
                        price["cost"] = current_mv
                        price["mv_ref"] = current_mv                                
                        price["qty"] = current_qty                    
                        #execut_order(symbol,acction) 
                    else:
                        price["action"] = "skip"                        
                        price["cost"] = last_cost
                        price["notes"] = f"Skip: mv={round(current_mv, 2)} with ref={round(last_mv_ref, 2)} in range 3$ "                    
                        if current_mv < last_mv_ref:
                            price["mv_ref"] = current_mv
                        else:
                            price["mv_ref"] = last_mv_ref
            
        else: # sell only
            #current_mv = last_mv                  
            if time >= "15:55": # not sell all after nytime 15:55
                price["action"] = "sell"              
                #execut_order(symbol, acction)
                current_pnl = current_mv - last_cost                      
                price["pnl"] = round(current_pnl, 2)
                price["pct"] = round((current_mv - last_cost)/last_cost*100, 2)
                price["total_pnl"] += int(current_pnl)                    
                price["notes"] = f"{current_action}: mv:{round(last_mv_ref,2)} < ref:{round(last_mv_ref,2)} = {round(current_mv_change,2)}  < -3$,  to take win {round(current_pnl, 2)} $ "                       
                price["cost"] = 0
                price["qty"] = last_qty
                price["mv_ref"] = current_mv                         
            else:
                if (current_mv - last_mv_ref) > 8 or current_mv_change < -3:                             
                    current_action = "sell"
                    price["action"] = current_action              
                    #execut_order(symbol, acction)                      
                    price["pnl"] = current_mv - last_cost
                    price["pct"] = (current_mv - last_cost)/last_cost*100
                    price["pnl"] += current_pnl
                    price["notes"] = f"{current_action}: mv:{round(last_mv_ref,2)} < ref:{round(last_mv_ref,2)} = {round(current_mv_change,2)}  < -3$,  to take win {round(current_pnl, 2)} $ "                       
                    price["cost"] = 0
                    price["mv_ref"] = current_mv                         
                else:
                    price["action"] = "hold"
                    price["notes"] = f"Hold: mv:{round(last_mv_ref,2)} - ref:{round(last_mv_ref,2)} = {round((current_mv_change), 2)} in range 3$"                    
                    price["cost"] = last_cost
                    price["mv"] = last_mv                    
                    price["qty"] = current_qty 
                    if current_mv > last_mv_ref:
                        price["mv_ref"] = current_mv
                    else:
                        price["mv_ref"] = last_mv_ref
    return price

def update_symbols_day_prices_test_ui():
    log_data = load_test_log()
    new_log_data = {}
    for symbol in SYMBOLS:
        items = log_data[symbol]
        new_items = sorted(items, key=lambda x: x["timestamp"], reverse=True)    
        new_log_data[symbol] = {
                "symbol" : symbol,
                "colors" : SYMBOL_COLORS[symbol],
                "items" : new_items
            }
    lines = []                
    for symbol in SYMBOLS:
        v = []
        items = log_data[symbol]
        last_qty = 0
        for item in items:
            timestamp = item["timestamp"]        
            timestamp = timestamp.split(" ")[1]
            action = item["action"]
            notes =  item["notes"]
            qty = int(item["qty"])
            mv = int(item["mv"])
            last_qty = qty
            node = None
            if action=="sell" or action=="sell":                                                
                node = {
                        "icon": ACTION_ICONS[action],
                        "notes" : notes 
                    }   
            
            time_price = {
                "x" : timestamp,
                "y" : mv,
                "z" : last_qty,
                "node" : node
            }
            v.append(time_price)            
        
        min_y = min(p["y"] for p in v)   
        for p in v:
            p["y"] = (p["y"] - min_y)             

        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
    return  new_log_data, lines

TRADING_INDEX = 0
def update_symbols_day_prices_test():    
    global TRADING_INDEX
    
    trading_log = {}
    start = len(trading_log)
    for symbol in SYMBOLS:                    
        new_prices = []
        prices = get_alpaca_prices_api(symbol, 1, "5min", 100)                
        for index, price in enumerate(prices):        
            p = price["price_close"]
            qty = round(2000/p)
            price["mv"] =  round(qty * p, 2)                        
            if TRADING_INDEX > 5:
                price = should_trade(prices[:TRADING_INDEX])
            new_prices.append(price)
        trading_log[symbol] = new_prices
    TRADING_INDEX = TRADING_INDEX +1 
    if TRADING_INDEX > 70:
        TRADING_INDEX = 0
    save_test_log(trading_log)    
    return update_symbols_day_prices_test_ui()

def update_symbols_day_prices_ui(today = True):  # core function            
    log_data = load_today_log(today)    
    new_log_data = {}
    lines = []        

    if len(log_data) > 0:
        for symbol in SYMBOLS:
            v = []
            new_items = []          
            items = log_data[symbol]["items"]
            for item in items:
                timestamp = item["timestamp"]        
                timestamp = timestamp.split(" ")[1]
                action = item["action"]
                notes =  item["notes"]
                #node = item["node"]
                mv_change = round(float(item["mv_change($)"]), 2)
                mv = round(float(item["mv"]), 2)
                qty = int(item["qty"])
                new_item = {
                    "time" : timestamp,
                    "symbol" : item["symbol"], 
                    "price" : round(float(item["price_close"]), 2), 
                    "qty" : qty,
                    "mv" : mv,
                    "mv_ref" : round(float(item["mv_ref"]), 2),
                    "mv_change($)" : mv_change,
                    "cost" : round(float(item["cost"]), 2),
                    "pnl" : round(float(item["pnl"]), 2),
                    "pct" : round(float(item["pct"]), 2),
                    "total_pnl" : round(float(item["total_pnl"]), 2),
                    "action" : action,
                    "notes" : notes
                    #"trade" : node
                }                   
                new_items.append(new_item)
                node = None
                if action == "sell" or action == "buy":
                    node = {
                        "icon": ACTION_ICONS[action],
                        "notes" : notes 
                    }    
                time_price = {
                    "x" : timestamp,
                    "y" : mv,
                    "z" : qty,
                    "node" : node
                }
                v.append(time_price)            
            
            min_y = min(p["y"] for p in v)   
            for p in v:
                p["y"] = (p["y"] - min_y)             

            new_items = sorted(new_items, key=lambda x: x["time"], reverse=True)    
            new_log_data[symbol] = {
                "symbol" : symbol,
                "colors" : SYMBOL_COLORS[symbol],
                "items" : new_items
            }

            lines.append({
                "symbol" : symbol,
                "color"  : SYMBOL_COLORS[symbol],
                "series" : v
            })
    return  new_log_data, lines

tradelog = {
    "timestamp" : None,
    "symbol" : None,
    "price_close": 0,
    "qty" : 0,
    "mv" : 0,
    "mv_ref" : 0,                         
    "mv_change($)" : 0,                
    "cost": 0,
    "pnl": 0,
    "pct": 0,
    "total_pnl": 0,
    "action" : 0,
    "notes" : 0,                
}


def update_symbols_day_prices():  # core function        
    #grouped = {}
    clock = api.get_clock()    
    if clock.is_open:
        grouped_log_new = {}
        grouped_log = load_today_log()
        timestamp = get_ny_time_now()
        time = timestamp.split(" ")[1]
        len_log = len(grouped_log)
        for symbol in SYMBOLS:
            start = 0
            last_mv_ref = 0
            last_cost = 0
            last_mv = 0
            last_total_pnl = 0
            last_pnl = 0
            last_qty = 0
            trading_log = []
            if len_log > 0:
                trading_log = grouped_log[symbol]["items"]            
                start = len(trading_log)
                last_trade = trading_log[-1]
                last_mv_ref = last_trade["mv_ref"]
                last_cost = last_trade["cost"]
                last_mv =  last_trade["mv"]
                last_pnl = last_trade["pnl"]
                last_total_pnl = last_trade["total_pnl"]
                last_qty = last_trade["qty"]
            #trades = get_alpaca_prices_api(symbol, 1, "5min", 100)
            test_trade = get_latest_trade(symbol)                                                
            #test_trade = trades[start]
            #timestamp = test_trade["timestamp"]
            #time = timestamp.split(" ")[1]
            #current_price = test_trade["price_close"]

            current_price = test_trade.p
            test_trade = get_latest_trade(symbol)                        
            test_qty = round(2000/current_price)
            current_mv = current_price * test_qty
            current_mv_ref = current_mv                
            current_action = None
            current_notes = None
            current_mv_change = 0
            current_cost = 0
            current_pnl = 0
            current_pct = 0
            current_total_pnl = 0
            current_qty = 0
            
            if last_mv == 0:
                current_mv_change = 0
            else:
                current_mv_change = current_mv - last_mv

            if start < 5:
                if current_mv < last_mv_ref:
                    current_mv_ref = current_mv
            else:
                                
                if last_cost == 0:  # buy only                
                    if time <= "15:50": # not buy after nytime 15:50
                        if start > 5:

                            if current_mv_change > 3: # start up from lower
                                current_action = "buy"
                                current_notes = f"{current_action}: mv:{round(current_mv, 2)} - ref:{round(last_mv_ref, 2)} = {round((current_mv_change),2)}  > 3$ "
                                current_cost = current_mv
                                current_mv_ref = current_mv                                
                                current_qty = test_qty
                                
                                #execut_order(symbol,acction) 
                            else:
                                current_action = "skip"                        
                                current_cost = last_cost
                                current_notes = f"Skip: mv={round(current_mv, 2)} with ref={round(last_mv_ref, 2)} in range 3$ "                    
                                if current_mv < last_mv_ref:
                                    current_mv_ref = current_mv
                                else:
                                    current_mv_ref = last_mv_ref
                    
                else: # sell only
                    #current_mv = last_mv                  
                    if time >= "15:55": # not sell all after nytime 15:55
                        current_action = "sell"              
                        #execut_order(symbol, acction)                      
                        current_pnl = current_mv - last_cost
                        current_pct = (current_mv - last_cost)/last_cost*100
                        current_total_pnl += current_pnl                    
                        current_notes = f"{current_action}: mv:{round(last_mv_ref,2)} < ref:{round(last_mv_ref,2)} = {round(current_mv_change,2)}  < -3$,  to take win {round(current_pnl, 2)} $ "                       
                        current_cost = 0
                        current_qty = last_qty
                        current_mv_ref = current_mv                         
                    else:
                        if (current_mv - last_mv_ref) > 8 or current_mv_change < -3:                             
                            current_action = "sell"              
                            #execut_order(symbol, acction)                      
                            current_pnl = current_mv - last_cost
                            current_pct = (current_mv - last_cost)/last_cost*100
                            current_total_pnl += current_pnl
                            current_notes = f"{current_action}: mv:{round(last_mv_ref,2)} < ref:{round(last_mv_ref,2)} = {round(current_mv_change,2)}  < -3$,  to take win {round(current_pnl, 2)} $ "                       
                            current_cost = 0
                            current_mv_ref = current_mv                         
                        else:
                            current_action = "hold"
                            current_notes = f"Hold: mv:{round(last_mv_ref,2)} - ref:{round(last_mv_ref,2)} = {round((current_mv_change), 2)} in range 3$"                    
                            current_cost = last_cost
                            #current_mv = last_mv                    
                            current_qty = test_qty 
                            if current_mv > last_mv_ref:
                                current_mv_ref = current_mv
                            else:
                                current_mv_ref = last_mv_ref

            tradelog = {
                "timestamp" : timestamp,
                "symbol" : symbol,
                "price_close": current_price,
                "qty" : current_qty,
                "mv" : current_mv,
                "mv_ref" : current_mv_ref,                         
                "mv_change($)" : current_mv_change,                
                "cost": current_cost,
                "pnl": current_pnl,
                "pct": current_pct,
                "total_pnl": current_total_pnl,
                "action" : current_action,
                "notes" : current_notes,                
            }
                #execut_order(symbol, current_action)
            trading_log.append(tradelog)
            grouped_log_new[symbol] = {
                "colors" : SYMBOL_COLORS[symbol], 
                "items" : trading_log }

        save_today_log(grouped_log_new)
        return update_symbols_day_prices_ui(True)                
    else:
        return update_symbols_day_prices_ui(False)
        

def update_symbols_daily_prices():  # core function    
    lines = []
    grouped = {}    
    for symbol in SYMBOLS:
        prices = get_alpaca_prices_api(symbol, 30, "1Day", 30, False)      
        if not prices:
            continue 
        grouped[symbol] = {"colors" : SYMBOL_COLORS[symbol], "items" : prices }    
        v = []
        lastPrice = 0
        currentPrice = 0
        lastPrice = round(float(prices[0]["price_close"]), 2)
        for price in prices:
            ts = datetime.fromisoformat(price["timestamp"]).strftime("%m-%d")
            currentPrice = round(float(price["price_close"]), 2)
            priceRate = round(float(currentPrice - lastPrice),2)
            lastPrice = currentPrice
            trade = None
            time_price = {
                "x" : ts, 
                "y" : lastPrice,
                "node" : trade
                }                     
            v.append(time_price)
        min_y = min(p["y"] for p in v)   
        for p in v:
            p["y"] = p["y"] - min_y                       

        lines.append({
            "symbol" : symbol,
            "color"  : SYMBOL_COLORS[symbol],
            "series" : v
        })
        
    return grouped, lines

################################
#  update_user_account()  #
################################

def update_user_account():
    result = []           
    account = api.get_account()    
    result.append({
        "account_number": account.account_number,
        "buying_power": float(account.buying_power),
        "cash": float(account.cash),
        "equity": float(account.equity),
        "position_market_value": float(account.portfolio_value),
        "long_market_value": float(account.long_market_value),
        "short_market_value": float(account.short_market_value),
        "created_date": account.created_at.strftime("%Y-%m-%d")
    })
    return result

##################################
# Update Scan Symbols
##################################
def update_symbols_scan():    
    #from scanner import scan_market
    results = []
    bars = []
    scans = scan_market()
    for scan in scans:
        results.append({
                "symbol": scan["symbol"],
                "score": round(float(scan["score"]), 2),
                "price": round(float(scan["change"]), 2),
                "volume": round(float(scan["volume"]), 2)
            })
        bars.append({
                "x": scan["symbol"],
                "y": round(float(scan["score"]), 2),
                "color" : SYMBOL_COLORS[scan["symbol"]]
                })
        
    return results, bars

################################
#  update_symbols_positions()  #
################################
def update_symbols_positions():  # core functions
    result = []           
    bars = []
    positions = api.list_positions()
    for pos in positions:
        mv = round(float(pos.market_value), 2)
        cost = round(float(pos.cost_basis), 2)
        price = round(float(pos.current_price), 2)
        avg_price = round(float(pos.avg_entry_price), 2)
        pnl = mv-cost
        pct = pnl / abs(cost) * 100 if cost else 0
        if pct <= -2:
            action = f" PNL % <= -2 SELL (STOP LOSS) "
        elif pct >= 3:
            action = f" PNL % >= 3 SELL (TAKE PROFIT) "
        else:
            action = f" PNL % (-2, 3) HOLD "        

        result.append({
                "symbol": pos.symbol,
                "qty": int(pos.qty),
                "avg_entry_price": round(float(pos.avg_entry_price), 2),
                "market_value": round(float(pos.market_value), 2),
                "cost_basis": round(float(pos.cost_basis), 2),
                "pnl": round(float(pnl), 2),
                "pct": round(float(pct), 2),
                "action": action
            })
        bars.append({
            "x": pos.symbol,
            "y" : abs(mv -cost),
            "color" : SYMBOL_COLORS[pos.symbol]
        })
    return result, bars
    
################################
# update_symbols_trades()      #
################################

def get_all_activities():

    activities = []
    page_token = None
    # ===== 1️⃣ 拉取 Alpaca 数据 =====
    while True:  # no fee member only could get 100 data per time access
        res = api.get_activities(
            activity_types="FILL",
            page_token=page_token,
            direction="desc"
        )
        if not res:
            break
        activities.extend(res)
        page_token = res[-1].id

        if len(res) < 100:
            break
    return activities 

def update_symbols_trades():
    activities = get_all_activities()
    grouped = {}
    lines = []

    if not activities:
        return grouped, lines

    # 1️⃣ sort by time
    activities = sorted(activities, key=lambda x: x.transaction_time)

    # 2️⃣ group by symbol
    trades_grouped = {}
    for a in activities:
        trades_grouped.setdefault(a.symbol, []).append(a)

    summary = 0

    # 3️⃣ process each symbol
    for symbol, trades in trades_grouped.items():

        trade_datas = []
        v = []

        total_qty = 0
        cost = 0.0                 # remaining position cost
        realized_pnl = 0.0         # ✅ REAL pnl only
        cost_max = 0.0

        for t in trades:
            time = utc_to_est(t.transaction_time.strftime("%Y-%m-%d %H:%M"))
            qty = int(t.qty)
            price = round(float(t.price), 2)

            # ===== BUY =====
            if t.side == "buy":
                total_qty += qty
                cost += qty * price

                cost_max = max(cost_max, cost)

            # ===== SELL =====
            elif t.side in ["sell", "sell_short"]:
                if total_qty > 0:
                    avg_cost = cost / total_qty

                    # ✅ realized pnl only
                    realized = (price - avg_cost) * qty
                    realized_pnl += realized

                    # update position
                    total_qty -= qty
                    cost -= avg_cost * qty

            # ===== Unrealized (for display only) =====
            if total_qty > 0:
                mv = total_qty * price
                unrealized_pnl = mv - cost
                pct = (unrealized_pnl / cost * 100) if cost > 0 else 0
            else:
                mv = 0
                unrealized_pnl = 0
                pct = 0
                cost = 0  # reset when flat

            total_pnl = round(realized_pnl, 2)

            # ===== trade table =====
            trade_data = {
                "symbol": symbol,
                "side": t.side,
                "price": price,
                "qty": qty,
                "total_qty": total_qty,
                "cost_base": round(cost, 2),
                "market_value": round(mv, 2),
                "pnl": round(unrealized_pnl, 2),   # display only
                "pct": round(pct, 2),
                "total_pnl": total_pnl,            # ✅ real pnl
                "reason": t.side,
                "id": t.id.split("::")[0],
                "transaction_time": time
            }

            trade_datas.append(trade_data)

            # ===== chart series =====
            if t.side == "buy":
                action = "buy"
            else:
                action = "sell" 

            time_price = {
                "x": time,
                "y": pct,   # ✅ equity curve (IMPORTANT)
                "z": 0, # total_qty,   # for your frontend logic
                "node": {                    
                    "icon": ACTION_ICONS[action],
                    "notes": action
                }
            }

            v.append(time_price)

        grouped[symbol] = {
            "colors": SYMBOL_COLORS[symbol],
            "items": trade_datas
        }

        lines.append({
            "symbol": symbol,
            "color": SYMBOL_COLORS[symbol],
            "series": v
        })

        pct_total = (realized_pnl / cost_max) if cost_max > 0 else 0

        #print(
        #    f"{symbol} most cost: {round(cost_max, 2)}, "
        #    f"total pnl: {round(realized_pnl, 2)}, "
        #    f"pct: {round(pct_total, 2)}"
        #)

        summary += realized_pnl

    #print(f"Summary PnL for all: {round(summary, 2)}")

    return grouped, lines
