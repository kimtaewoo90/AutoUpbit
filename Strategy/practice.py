import pyupbit
import time
import telegram


def GetTarget(ticker):
    Ticker = ticker
    df = pyupbit.get_ohlcv(Ticker, "minute5")

    yday = df.iloc[-1]

    yday_high = yday["close"]
    return yday_high


def GetMA(ticker, days):
    df = pyupbit.get_ohlcv(ticker)
    closed = df["close"]
    print(f"closed : {closed.iloc[-1]}")
    cur = pyupbit.get_current_price(ticker)
    closed[-1] = cur
    print(f"cur: {closed.iloc[-1]}")
    windows = closed.rolling(days)
    ma = windows.mean()

    return ma


def SendMsg(msg):
    chat_token = "1474721655:AAH7cSJoNQdesO_lXRRGUf__mGIInPpicdU"
    bot = telegram.Bot(token=chat_token)
    bot.send_message(chat_id="1542664370", text=msg)


def market_order(uuid, remained_coin):
    SendMsg("시장가 매도 주문 시작")
    upbit.cancel_order(uuid)
    time.sleep(1)
    resp_market_sell = upbit.sell_market_order(Ticker, remained_coin)
    market_uuid = resp_market_sell["uuid"]
    time.sleep(5)
    get_order = upbit.get_order(
        Ticker, state="done")
    market_sell_price = get_order["price"]
 
   
    return resp_market_sell


if __name__ == "__main__":

    access = "frGzp5hUEaQBNQ1uuO60Dx3QGkSm5ugsEVdfrpnr"
    #secret = lines[1].strip()
    secret = "L4wHqPfrfc7x8NYWHaL8IoUxbV8MBuhoxZG2ZHJa"
    upbit = pyupbit.Upbit(access, secret)

    Ticker = "KRW-DOGE"
    #buy_resp = upbit.buy_market_order(Ticker, 5000)

    # 지정가 매도
    #remained_coin =  upbit.get_balance(Ticker)
    #sell_resp = upbit.sell_limit_order(Ticker, 1000, remained_coin)
    #uuid = sell_resp["uuid"]
    #market_resp = market_order(uuid, remained_coin)

    #print(pyupbit.get_ohlcv(Ticker, "minute5"))

    import os, sys

    print(sys.path.append(os.path.dirname(os.path.dirname(__file__))))