import pyupbit
import sys
import time
import datetime
import math
import telegram
import pandas as pd

class Connection:

    def ConnectToUpbit(self):
        # 객체생성(Upbit 연결)
        access = "frGzp5hUEaQBNQ1uuO60Dx3QGkSm5ugsEVdfrpnr"
        secret = "L4wHqPfrfc7x8NYWHaL8IoUxbV8MBuhoxZG2ZHJa"
        upbit = pyupbit.Upbit(access, secret)

        return upbit

class UtilClass:

    #def __init__(self):
    #    super().__init__()


    def SaveResult(self, profit_time, loss_time, balance, start_tag):
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


    def SendMsg(self, msg):
        chat_token = "1474721655:AAH7cSJoNQdesO_lXRRGUf__mGIInPpicdU"
        bot = telegram.Bot(token=chat_token)
        bot.send_message(chat_id="1542664370", text=msg)


    def GetMA(self, ticker, cur_price, big_days, small_days):
        df = pyupbit.get_ohlcv(ticker, "minute5")
        closed = df["close"]

        closed[-1] = cur_price
        big_windows = closed.rolling(big_days)
        small_windows = closed.rolling(small_days)

        # signal_1
        if big_windows.mean()[-1] < small_windows.mean()[-1]:
            if big_windows.mean()[-2] < big_windows.mean()[-1] and small_windows.mean()[-2] < small_windows.mean()[-1]:
                return True
            else:
                return False
        else:
            return False


    def GetTarget(self, ticker):
        Ticker = ticker
        df = pyupbit.get_ohlcv(Ticker, "minute5")

        res = df.iloc[-2]
        return res


    def GetVolume(self):
        pairs = dict()
        tickers = pyupbit.get_tickers(fiat="KRW")

        self.SendMsg("Finding the Target Coins")
        for i in range(len(tickers)):
            time.sleep(0.5)
            df = pyupbit.get_ohlcv(tickers[i], "day")
            pairs['%s' % tickers[i]] = df.iloc[-1]["volume"] * df.iloc[-1]["close"]
        
        res = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
        self.SendMsg(f"Found Target Coin\nTarget Coin : {res[0][0]}")
        return res[0][0]

    def GetVolumeList(self):
        pairs = dict()
        tickers = pyupbit.get_tickers(fiat="KRW")

        self.SendMsg("Finding the Target Coins")
        for i in range(len(tickers)):
            time.sleep(0.5)
            df = pyupbit.get_ohlcv(tickers[i], "day")
            pairs['%s' % tickers[i]] = df.iloc[-1]["volume"] * df.iloc[-1]["close"]
        
        res = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
        self.SendMsg(f"Found Target Coin\nTarget Coin : {res[0][0]}")
        return res

