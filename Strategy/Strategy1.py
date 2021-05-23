"""
signal1 : 현재가 >= 5분봉시가 * 1.005
signal2 : 현재5분봉시가 >= 직전5분봉종가
signal3 : 5분MA >= 10분MA & 5분봉MA/10분봉MA가 상승추세
"""

import sys
import pyupbit
import time
import datetime
import math
import telegram
import pandas as pd

# PyQt UI imports
from PyQt5.QtCore import QThread, pyqtSignal, Qt


# Users package
from functions import Utils
import config
import Main

# ----------- Global Variables ------------------ #

#global global_ticker
#------------------------------------------------ #


class Signals():


    def signal1(self, cur_price, target_price):
        if cur_price > target_price:
            return True
        else:
            return False

    def signal2(self, five_open, five_closed):
        if five_open >= five_closed:
            return True
        else:
            return False

    # judge_ma => 5분/10분 MA 골든크로스 & 5분봉/10분봉 상승일때만 True.
    def signal3(self, judge_ma):
        if judge_ma is True:
            return True
        else:
            return False

    #TODO: 호가정보로 시그널 찾기
    # 매수세가 갑자기 늘어날때
    def signal4(self, Ticker):
        orderbook = pyupbit.get_orderbook(Ticker)
        total_bid_size = orderbook[0]["total_bid_size"]
        total_ask_size = orderbook[0]["total_ask_size"]
        
        if total_bid_size > total_ask_size:
            return True, total_ask_size, total_bid_size
        elif total_bid_size < total_ask_size:
            return False, total_ask_size, total_bid_size
  
    def sell_signal1(self, ticker, small_days):
        df = pyupbit.get_ohlcv(ticker, "minute5")
        closed = df["close"]
        
        small_windows = closed.rolling(small_days)

        if small_windows.mean()[-2] > small_windows.mean()[-1]:
            return True
        else:
            return False




class Bot(QThread):

    Log = pyqtSignal(str)
    
    # Informations
    GetTicker = pyqtSignal(str)
    GetCurPrice = pyqtSignal(float, float)
    Balance = pyqtSignal(float)
    TotalPnL = pyqtSignal(float)
    GetBuyCnt = pyqtSignal(str)  # 매수여부
    ProfitTime = pyqtSignal(int)
    LossTime = pyqtSignal(int)

    # Signal1
    GetSignal1 = pyqtSignal(bool)
    GetFiveClose = pyqtSignal(float)
    GetTargetPrice = pyqtSignal(float)

    # Signal2
    GetFiveOpen = pyqtSignal(float)
    GetSignal2 = pyqtSignal(bool)

    # Signal3
    GetMAsignals = pyqtSignal(bool)
    GetSignal3 = pyqtSignal(bool)

    # Signal4
    TotalAskSize = pyqtSignal(float)
    TotalBidSize = pyqtSignal(float)
    TotalSize = pyqtSignal(float)
    GetSignal4 = pyqtSignal(bool)


    #TargetTicker = pyqtSignal(str)
    BuyPrice = pyqtSignal(float)
    CurPrice = pyqtSignal(float)            
    TargetPrice = pyqtSignal(float)
    LossCutPrice = pyqtSignal(float)
    PnL = pyqtSignal(float)

                          
    def __init__(self):
        super().__init__()

        #self.running = True

    def run(self):

        # initialize params
        target_price = 0
        total_loss_time = 0
        loss_time = 0
        total_profit_time = 0
        profit_time = 0
        total_gain = 0
        signal1 = False
        signal2 = False
        signal3 = False

        GetTicker = False # Get Tickers
        #start_tag = True  # For Save result (make DataFrame for first time)
        start_msg = True  # To send msg for first running bot
        #five_mins = True  # To imporve performance
        monitoring_flag = 0

        # declare user imports
        util = Utils.UtilClass()
        conn = Utils.Connection()
        upbit = conn.ConnectToUpbit()
    

        #signals = Signals.Signals()
        start_balance = upbit.get_balance("KRW")
        
        # start
        while True:

            if loss_time == 3:
                sleep_time = 3600
                util.SendMsg(f"loss count : {loss_time}\nsleep time : {sleep_time} sec")
                time.sleep(sleep_time)
                loss_time = 0
                GetTicker = False
                #start_orderbook = False

            # Monitoring the price for Buy coin
            while True:
                if GetTicker is False:
                    profit_time = 0
                    self.Log.emit("Getting Target Ticker")
                    config.global_ticker = util.GetVolume()                    
                    Ticker = config.global_ticker
                    self.Log.emit(f"Found Ticker, Target Coin is {Ticker}")
                    start_msg = True
                    bot_start = datetime.datetime.now()

                GetTicker = True    # GetVolume 중복 실행 방지

                if start_msg is True:
                    util.SendMsg(f"Monitoring price of {Ticker}")
                    self.Log.emit(f"Monitoring price of {Ticker}")
                    start_msg = False
                    
                try:
                    res = util.GetTarget(Ticker)
                    five_closed = res["close"]
                    five_open = pyupbit.get_ohlcv(Ticker, "minute5")
                    five_open = five_open.iloc[-1]
                    five_open = five_open["open"]
                    five_temp = five_closed
                    cur_price = pyupbit.get_current_price(Ticker)
                    time.sleep(0.5)
                except:
                    five_closed = five_temp

                if not type(cur_price) == float:
                    time.sleep(0.2)
                    cur_price = pyupbit.get_current_price(Ticker)
                    self.Log.emit("Error with Get current price")

                buy_price = 0
                sell_price = 0
                balance = upbit.get_balance("KRW")
                judge_ma = util.GetMA(Ticker, cur_price, 10, 5)
                target_price = round(five_closed * 1.005)

                # Signals Class instance
                signals = Signals()

                # Get signals
                signal1 = signals.signal1(cur_price, target_price)
                signal2 = signals.signal2(five_open, five_closed)
                signal3 = signals.signal3(judge_ma)
                signal4, total_ask_size, total_bid_size = signals.signal4(Ticker)

                # Display
                self.GetTicker.emit(Ticker)
                self.GetCurPrice.emit(cur_price, target_price)
                self.GetTargetPrice.emit(target_price)
                self.GetFiveClose.emit(five_closed)
                self.GetFiveOpen.emit(five_open)
                self.GetSignal1.emit(signal1)
                self.GetSignal2.emit(signal2)
                
                self.GetSignal3.emit(signal3)
                self.GetMAsignals.emit(judge_ma)
                
                self.GetSignal4.emit(signal4)
                self.TotalAskSize.emit(total_ask_size)
                self.TotalBidSize.emit(total_bid_size)
                self.TotalSize.emit(total_ask_size - total_bid_size)
                                
                self.GetBuyCnt.emit("False")
                self.Balance.emit(balance)

                if monitoring_flag == 0:
                    self.Log.emit(f"[{datetime.datetime.now()}] : Monitoring {Ticker}")
                    monitoring_flag = 1

                print(f"Target Coin : {Ticker} / Judge MA : {judge_ma} / five_closed : {five_closed} now_five_open : {five_open} / Current_price : {cur_price} / Target_buy_price : {target_price}")

                # 1시간동안 매수가 없으면 티커 다시 찾기
                if bot_start - datetime.datetime.now() > datetime.timedelta(hours=1):
                    GetTicker = False

                # Buy the coin
                if signal1 is True and\
                    signal2 is True and\
                    signal3 is True and\
                    signal4 is True:
                    
                    buy_amt = balance - math.ceil(balance * 0.05)
                    buy_price = cur_price
                    #resp = upbit.buy_market_order(Ticker, buy_amt)
                    upbit.buy_market_order(Ticker, buy_amt)
                    print(f"Success to Buy {Ticker} at {buy_price}")

                    # 매수여부 Display
                    self.GetBuyCnt.emit("True")

                    util.SendMsg(
                    f"""!Success to Buy!\nTicker : {Ticker}\nBuy Price : {buy_price}\nTargetPrice : {round(buy_price * 1.02)}\nLossCut Price : {math.ceil(buy_price*0.975)}
                    """)
                    self.Log.emit( f"""!Success to Buy!\nTicker : {Ticker}\nBuy Price : {buy_price}\nTargetPrice : {round(buy_price * 1.02)}\nLossCut Price : {math.ceil(buy_price*0.975)}
                    """)
                    
                    # Monitoring the price for Sell coin
                    while True:
                        try:
                            time.sleep(0.5)

                            losscut_rate = config.losscut_rate
                            profit_rate = config.profit_rate

                            cur_price_to_sell = pyupbit.get_current_price(Ticker)
                            print(f"[{datetime.datetime.now()}]: Ticker : {Ticker} / Buy_Price : {buy_price} / Current_Price : {cur_price_to_sell} / Target_Sell_Price : {round(buy_price * profit_rate)} / LosCut_Sell_Price : {math.ceil(buy_price*losscut_rate)} / PnL : {format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %" )

                            monitoring_pnl = (cur_price_to_sell - buy_price)/buy_price * 100
                            self.GetCurPrice.emit(cur_price_to_sell, round(buy_price * profit_rate))
                            self.BuyPrice.emit(buy_price)
                            self.TargetPrice.emit(round(buy_price * profit_rate))
                            self.LossCutPrice.emit(math.ceil(buy_price * losscut_rate))
                            self.PnL.emit(monitoring_pnl)

                            # add sell signals : 5분봉이 하락전환 시 매도                             
                            sell_signal1 = signals.sell_signal1(Ticker, 5)

                            # Get sell signal. Sell the coin
                            if cur_price_to_sell >= math.ceil(buy_price * profit_rate) or\
                               cur_price_to_sell <= math.ceil(buy_price * losscut_rate) or\
                               sell_signal1 is True:

                                remained_coin = upbit.get_balance(Ticker)
                                resp_sell = upbit.sell_limit_order(Ticker, cur_price_to_sell, remained_coin)
                                sell_price = cur_price_to_sell
                                uuid = resp_sell["uuid"]
                                print(uuid)
                                util.SendMsg("waiting for Limit Short Orders")
                                self.Log.emit("waiting for Limit Short Orders")

                                sell_start_time = time.time()
                                while True:
                                    state = upbit.get_order(Ticker)
                                    waiting_sell_time = time.time()
                                    
                                    # 계속 지정가 매도가 체결이 안되면 취소하고 시장가로 매도 하기
                                    if waiting_sell_time - sell_start_time > 60:
                                        util.SendMsg("시장가 매도 주문 시작")
                                        upbit.cancel_order(uuid)
                                        time.sleep(1)
                                        #resp_market_sell = upbit.sell_market_order(Ticker, remained_coin)
                                        upbit.sell_market_order(Ticker, remained_coin)
                                        self.Log.emit("시장가 매도 후 잔고 변경중(5sec)")
                                        time.sleep(5)
                                        res_balance = upbit.get_balance("KRW")
                                        total_gain = total_gain + (res_balance - balance)
                                        util.SendMsg(
                                        f"""시장가 매도 체결 결과\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                        """)
                                        self.Log.emit(f"""시장가 매도 체결 결과\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                        """)
                                        self.Balance.emit(res_balance)
                                        self.TotalPnL.emit(res_balance - start_balance)
                                        df = pyupbit.get_ohlcv(Ticker, "minute5")
                                        five_bong = df.iloc[-1]
                                        sell_five_bong = five_bong.name                                    
                                        break

                                    # 지정가 매도 성공시
                                    if len(state) == 0:
                                        res_balance = upbit.get_balance("KRW")
                                        time.sleep(1)
                                        total_gain = total_gain + (res_balance - balance)
                                        util.SendMsg(
                                        f"""지정가 매도 체결 결과\nSell price : {sell_price}\nBought price : {buy_price}\nPnL : {format((sell_price - buy_price)/buy_price * 100, '.2f')} %\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                        """)
                                        self.Log.emit(f"""지정가 매도 체결 결과\nSell price : {sell_price}\nBought price : {buy_price}\nPnL : {format((sell_price - buy_price)/buy_price * 100, '.2f')} %\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                        """)
                                        self.Balance.emit(res_balance)
                                        self.TotalPnL.emit(res_balance - start_balance)

                                        df = pyupbit.get_ohlcv(Ticker, "minute5")
                                        five_bong = df.iloc[-1]
                                        sell_five_bong = five_bong.name
                                        break
                                
                                # 시장가 또는 지정가 매도가 체결 된 후 profit 인지 loss 인지 판단 & 알림
                                if sell_price > buy_price:
                                    profit_time = profit_time + 1
                                    total_profit_time = total_profit_time + 1
                                    
                                    util.SendMsg(f"Profit count : [ {total_profit_time} ]")
                                    self.Log.emit(f"Profit count : [ {total_profit_time} ]")

                                elif sell_price <= buy_price:
                                    loss_time = loss_time + 1
                                    total_loss_time = total_loss_time + 1

                                    util.SendMsg(f"loss count : [ {loss_time} ]")
                                    self.Log.emit(f"loss count : [ {loss_time} ]")

                                # 매도가 일어날때마다 다시 티커찾기
                                GetTicker = False

                                self.ProfitTime.emit(total_profit_time)
                                self.LossTime.emit(total_loss_time)                            

                                waiting_five_scalping = True
                                # 매도시의 5분봉과 같은 5분봉에서 재매수 방지
                                while True:
                                    if datetime.datetime.now() - sell_five_bong > datetime.timedelta(minutes=5):
                                        util.SendMsg("Find signals in new Five scalping\n")
                                        self.Log.emit("Find signals in new Five scalping\n")
                                        break

                                    elif waiting_five_scalping is True:
                                        waiting_five_scalping = False
                                        self.Log.emit("Waiting new Five scalping\n")
                                break
                        except:
                            print("error..")
                            #continue 
                break



    #def resume(self):
    #    self.running = True

    #def pause(self):
    #    self.running = False