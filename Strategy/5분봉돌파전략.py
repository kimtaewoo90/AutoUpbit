import pyupbit
import time
import datetime
import math
import telegram
import pandas as pd
from functions import Utils


def SaveResult(profit_time, loss_time, balance, start_tag):
    now = datetime.datetime.now()
    res = [now, profit_time, loss_time, balance]
    if start_tag is True:
        res_df = pd.DataFrame(
            res, columns=["Time", "profit_time", "loss_time", "balance"])
        start_tag = False
    else:
        temp_df = pd.DataFrame(
            res, columns=["Time", "profit_time", "loss_time", "balance"])
        res_df = res_df.append(temp_df)


def SendMsg(msg):
    chat_token = "1474721655:AAH7cSJoNQdesO_lXRRGUf__mGIInPpicdU"
    bot = telegram.Bot(token=chat_token)
    bot.send_message(chat_id="1542664370", text=msg)


def GetMA(ticker, cur_price, big_days, small_days):
    df = pyupbit.get_ohlcv(ticker, "minute5")
    closed = df["close"]

    closed[-1] = cur_price
    big_windows = closed.rolling(big_days)
    small_windows = closed.rolling(small_days)

    #print(f"20mins ma : {big_windows.mean()[-1]}\n 5mins ma : {small_windows.mean()[-1]}")
    if big_windows.mean()[-1] < small_windows.mean()[-1]:
        return True
    else:
        return False


def GetTarget(ticker):
    Ticker = ticker
    df = pyupbit.get_ohlcv(Ticker, "minute5")

    res = df.iloc[-2]
    return res


def GetVolume():
    pairs = dict()
    tickers = pyupbit.get_tickers(fiat="KRW")

    SendMsg("Finding the Target Coins")
    for i in range(len(tickers)):
        time.sleep(0.5)
        df = pyupbit.get_ohlcv(tickers[i], "day")
        pairs['%s' % tickers[i]] = df.iloc[-1]["volume"] * df.iloc[-1]["close"]

    res = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
    SendMsg(f"Found Target Coin\nTarget Coin : {res[0][0]}")
    return res[0][0]


if __name__ == "__main__":

    conn = Utils.Connection()
    upbit = conn.ConnectToUpbit()

    # initialize params
    loss_time = 0
    profit_time = 0
    total_gain = 0
    
    noMoreVol = False # Get Tickers
    start_tag = True  # For Save result (make DataFrame for first time)
    start_msg = True  # To send msg for first running bot

    # start
    while True:
        target = 0
        if loss_time == 3:
            sleep_time = 3600
            SendMsg(f"loss count : {loss_time}\nsleep time : {sleep_time} sec")
            time.sleep(sleep_time)
            loss_time = 0
            noMoreVol = False

        # Monitoring the price for Buy coin
        while True:
            now = datetime.datetime.now()

            if noMoreVol is False:
                day = now.day
                profit_time = 0
                #loss_time = 0
                Ticker = GetVolume()
                start_msg = True

            noMoreVol = True    # GetVolume 중복 실행 방지

            if start_msg is True:
                SendMsg(f"Monitoring price of {Ticker}")
                start_msg = False
   
            try:
                res = GetTarget(Ticker)
                five_closed = res["close"]
                five_times = res.name
                five_temp = five_closed
                cur_price = pyupbit.get_current_price(Ticker)
                time.sleep(2)
            except:
                five_closed = five_temp

            if not type(cur_price) == float:
                time.sleep(1)
                cur_price = pyupbit.get_current_price(Ticker)

            buy_price = 0
            sell_price = 0
            balance = upbit.get_balance("KRW")
            judge_ma = GetMA(Ticker, cur_price, 20, 5)
            print(f"Target Coin : {Ticker} / Judge MA : {judge_ma} / five_closed : {five_closed} / Current_price : {cur_price} / Target_buy_price : {round(five_closed * 1.005)}")

            # Buy the coin
            if cur_price >= five_closed * 1.005 and judge_ma is True:
                
                buy_amt = balance - math.ceil(balance * 0.05)
                buy_price = cur_price
                resp = upbit.buy_market_order(Ticker, buy_amt)
                print(f"Success to Buy {Ticker} at {buy_price}")
                SendMsg(
                f"""!Success to Buy!\nTicker : {Ticker}\nBuy Price : {buy_price}\nTargetPrice : {round(buy_price * 1.02)}\nLossCut Price : {math.ceil(buy_price*0.975)}
                """)

                
                # Monitoring the price for Sell coin
                while True:
                    try:
                        time.sleep(1)
                        cur_price_to_sell = pyupbit.get_current_price(Ticker)
                        print(f"[{datetime.datetime.now()}]: Ticker : {Ticker} / Buy_Price : {buy_price} / Current_Price : {cur_price_to_sell} / Target_Sell_Price : {round(buy_price * 1.02)} / LosCut_Sell_Price : {math.ceil(buy_price*0.975)} / PnL : {format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %" )

                        # Sell the coin
                        if cur_price_to_sell >= math.ceil(buy_price * 1.02) or cur_price_to_sell <= math.ceil(buy_price * 0.975):# or sell_timing is True:
                            remained_coin = upbit.get_balance(Ticker)
                            resp_sell = upbit.sell_limit_order(Ticker, cur_price_to_sell, remained_coin)
                            sell_price = cur_price_to_sell
                            uuid = resp_sell["uuid"]
                            print(uuid)
                            SendMsg("waiting for Limit Short Orders")
                            print("waiting for Limit Short Orders")

                            sell_start_time = time.time()
                            while True:
                                state = upbit.get_order(Ticker)
                                waiting_sell_time = time.time()

                                print(f"waiting_sell_time - sell_start_time = {waiting_sell_time - sell_start_time}")
                                
                                # 계속 지정가 매도가 체결이 안되면 취소하고 시장가로 매도 하기
                                if waiting_sell_time - sell_start_time > 200:
                                    SendMsg("시장가 매도 주문 시작")
                                    upbit.cancel_order(uuid)
                                    time.sleep(1)
                                    resp_market_sell = upbit.sell_market_order(Ticker, remained_coin)
                                    time.sleep(2)
                                    res_balance = upbit.get_balance("KRW")
                                    total_gain = total_gain + (res_balance - balance)
                                    SendMsg(
                                    f"""시장가 매도 체결 결과\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                    """)
                                    df = pyupbit.get_ohlcv(Ticker, "minute5")
                                    five_bong = df.iloc[-1]
                                    sell_five_bong = five_bong.name                                    
                                    break

                                # 지정가 매도 성공시
                                if len(state) == 0:
                                    res_balance = upbit.get_balance("KRW")
                                    time.sleep(1)
                                    total_gain = total_gain + (res_balance - balance)
                                    SendMsg(
                                    f"""지정가 매도 체결 결과\nSell price : {sell_price}\nBought price : {buy_price}\nPnL : {format((sell_price - buy_price)/buy_price * 100, '.2f')} %\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                    """)
                                    df = pyupbit.get_ohlcv(Ticker, "minute5")
                                    five_bong = df.iloc[-1]
                                    sell_five_bong = five_bong.name
                                    break
                            
                            # 시장가 또는 지정가 매도가 체결 된 후 profit 인지 loss 인지 판단 & 알림
                            if sell_price > buy_price:
                                profit_time = profit_time + 1
                                print(f"Profit count : [ {profit_time} ]")
                                SendMsg(f"Profit count : [ {profit_time} ]")

                            elif sell_price <= buy_price:
                                loss_time = loss_time + 1
                                print(f"loss count : [ {loss_time} ]")
                                SendMsg(f"loss count : [ {loss_time} ]")
                                noMoreVol = False
                            #SaveResult(profit_time, loss_time, total_gain, start_tag)

                            # 매도시의 5분봉과 같은 5분봉에서 재매수 방지
                            while True:
                                if datetime.datetime.now() - sell_five_bong > datetime.timedelta(minutes=5):
                                    SendMsg("Find signals in new Five scalping\n")
                                    break
                            break
                    except:
                        print(type(cur_price_to_sell))
                        continue 
            break





        
