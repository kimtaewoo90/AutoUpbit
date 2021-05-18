import sys
import pyupbit
import time
import datetime
import math
import telegram
import pandas as pd

# PyQt UI imports
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QProgressBar, QTableWidgetItem, QHeaderView
from PyQt5 import uic

# Users package
import Signals
from functions import Utils

# ----------- Global Variables ------------------ #

global_ticker = "KRW-BTC"
#------------------------------------------------ #



class OrderbookWorker(QThread):

    dataSent = pyqtSignal(list)
    GlobalTicker = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.alive = True

    def run(self):

        global global_ticker

        while self.alive:

            self.GlobalTicker.emit(global_ticker)
            orderbook = pyupbit.get_orderbook(str(global_ticker))
            
            time.sleep(0.1)
            try:
                self.dataSent.emit(orderbook)
            except:
                print("None type orderbook")

    def close(self):
        self.alive = False

    def restart(self):
        self.alive = True
        self.start()


class Bot(QThread):

    Log = pyqtSignal(str)
    
    # Informations
    GetTicker = pyqtSignal(str)
    GetCurPrice = pyqtSignal(float)
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


    #TargetTicker = pyqtSignal(str)
    BuyPrice = pyqtSignal(float)
    CurPrice = pyqtSignal(float)            
    TargetPrice = pyqtSignal(float)
    LossCutPrice = pyqtSignal(float)
    PnL = pyqtSignal(str)

                          
    def __init__(self):
        super().__init__()
        self.GlobalTicker = "KRW-BTC"

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

        # Global variables
        global global_ticker
        
        noMoreVol = False # Get Tickers
        #start_tag = True  # For Save result (make DataFrame for first time)
        start_msg = True  # To send msg for first running bot
        #five_mins = True  # To imporve performance

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
                noMoreVol = False
                #start_orderbook = False

            # Monitoring the price for Buy coin
            while True:
                if noMoreVol is False:
                    profit_time = 0
                    self.Log.emit("Getting Target Ticker")
                    global_ticker = util.GetVolume()
                    Ticker = global_ticker
                    self.Log.emit(f"Found Ticker, Target Coin is {Ticker}")
                    start_msg = True
                    bot_start = datetime.datetime.now()


                noMoreVol = True    # GetVolume 중복 실행 방지

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
                signals = Signals.Signals()

                # Get signals
                signal1 = signals.signal1(cur_price, target_price)
                signal2 = signals.signal2(five_open, five_closed)
                signal3 = signals.signal3(judge_ma)

                # Display
                self.GetTicker.emit(Ticker)
                self.GetCurPrice.emit(cur_price)
                self.GetTargetPrice.emit(round(five_closed * 1.005))
                self.GetFiveClose.emit(five_closed)
                self.GetFiveOpen.emit(five_open)
                self.GetSignal1.emit(signal1)
                self.GetSignal2.emit(signal2)
                self.GetSignal3.emit(signal3)
                self.GetMAsignals.emit(judge_ma)
                self.GetBuyCnt.emit("False")
                self.Log.emit(f"[{datetime.datetime.now()}] : Monitoring {Ticker}")
                self.Balance.emit(balance)

                print(f"Target Coin : {Ticker} / Judge MA : {judge_ma} / five_closed : {five_closed} now_five_open : {five_open} / Current_price : {cur_price} / Target_buy_price : {target_price}")

                # 1시간동안 매수가 없으면 티커 다시 찾기
                if bot_start - datetime.datetime.now() > datetime.timedelta(hours=1):
                    noMoreVol = False

                # Buy the coin
                if signal1 is True and signal2 is True and signal3 is True:
                    
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
                            losscut_rate = 0.98
                            cur_price_to_sell = pyupbit.get_current_price(Ticker)
                            print(f"[{datetime.datetime.now()}]: Ticker : {Ticker} / Buy_Price : {buy_price} / Current_Price : {cur_price_to_sell} / Target_Sell_Price : {round(buy_price * 1.02)} / LosCut_Sell_Price : {math.ceil(buy_price*losscut_rate)} / PnL : {format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %" )
                            #self.Log.emit(f"[{datetime.datetime.now()}]: Ticker : {Ticker} / Buy_Price : {buy_price} / Current_Price : {cur_price_to_sell} / Target_Sell_Price : {round(buy_price * 1.02)} / LosCut_Sell_Price : {math.ceil(buy_price*0.975)} / PnL : {format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %" )

                            monitoring_pnl = f"{format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %"
                            self.GetCurPrice.emit(cur_price_to_sell)
                            self.BuyPrice.emit(buy_price)
                            self.TargetPrice.emit(round(buy_price * 1.02))
                            self.LossCutPrice.emit(math.ceil(buy_price * losscut_rate))
                            self.PnL.emit(monitoring_pnl)

                            # Sell the coin
                            if cur_price_to_sell >= math.ceil(buy_price * 1.02) or cur_price_to_sell <= math.ceil(buy_price * losscut_rate):# or sell_timing is True:
                                remained_coin = upbit.get_balance(Ticker)
                                resp_sell = upbit.sell_limit_order(Ticker, cur_price_to_sell, remained_coin)
                                sell_price = cur_price_to_sell
                                uuid = resp_sell["uuid"]
                                print(uuid)
                                util.SendMsg("waiting for Limit Short Orders")
                                print("waiting for Limit Short Orders")
                                self.Log.emit("waiting for Limit Short Orders")

                                sell_start_time = time.time()
                                while True:
                                    state = upbit.get_order(Ticker)
                                    waiting_sell_time = time.time()

                                    # 수동매도 시 break
                                    #if upbit.get_balance(Ticker) == 0:
                                    #    self.Log.emit("수동매도 되었습니다.")
                                    #    break
                                    #print(f"waiting_sell_time - sell_start_time = {waiting_sell_time - sell_start_time}")
                                    
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

                                    noMoreVol = False
                                #SaveResult(profit_time, loss_time, total_gain, start_tag)

                                self.ProfitTime.emit(total_profit_time)
                                self.LossTime.emit(total_loss_time)

                                # 매도 완료시 시그널 False로 초기화.
                                #self.Getsignal1.emit(False)
                                #self.Getsignal2.emit(False)
                                #self.Getsignal3.emit(False)
                                #self.BuyPrice.emit(0.0)
                                #self.TargetPrice.emit(0.0)
                                #self.LossCutPrice.emit(0.0)
                            

                                # 매도시의 5분봉과 같은 5분봉에서 재매수 방지
                                while True:
                                    if datetime.datetime.now() - sell_five_bong > datetime.timedelta(minutes=5):
                                        util.SendMsg("Find signals in new Five scalping\n")
                                        self.Log.emit("Find signals in new Five scalping\n")
                                        break
                                break
                        except:
                            print("error..")
                            #continue 
                break



    #def resume(self):
    #    self.running = True

    #def pause(self):
    #    self.running = False

main_ui = uic.loadUiType("autoUpbit_v2.ui")[0]

class MainWindows(QMainWindow, main_ui):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.bot = Bot()
        self.bot.Log.connect(self.Log)
        self.bot.Balance.connect(self.Balance)
        self.bot.TotalPnL.connect(self.TotalPnL)

        # Buy Monitoring
        self.bot.GetTicker.connect(self.GetTicker)
        self.bot.GetCurPrice.connect(self.GetCurPrice)
        self.bot.GetFiveClose.connect(self.GetFiveClose)
        self.bot.GetFiveOpen.connect(self.GetFiveOpen)
        self.bot.GetMAsignals.connect(self.GetMAsignals)
        self.bot.GetTargetPrice.connect(self.GetTargetPrice)
        self.bot.GetBuyCnt.connect(self.GetBuyCnt)

        # Sell Monitoring
        #self.bot.TargetTicker.connect(self.TargetTicker)
        self.bot.BuyPrice.connect(self.BuyPrice)
        self.bot.CurPrice.connect(self.CurPrice)
        self.bot.TargetPrice.connect(self.TargetPrice)
        self.bot.LossCutPrice.connect(self.LossCutPrice)
        self.bot.PnL.connect(self.PnL)
        self.bot.ProfitTime.connect(self.ProfitTime)
        self.bot.LossTime.connect(self.LossTime)

        # Signals
        self.bot.GetSignal1.connect(self.GetSignal1)
        self.bot.GetSignal2.connect(self.GetSignal2)
        self.bot.GetSignal3.connect(self.GetSignal3)


 
        # -------- Get OrderBook ---------- #
        table = self.orderbook
        header = table.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))
 
        wfactor = twidth / sum(width)
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            header.resizeSection(column, width[column]*wfactor)



        for i in range(10):
            
            # 매수호가량
            #item_0 = QTableWidgetItem(str(""))
            #item_0.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            #self.orderbook.setItem(10 + i, 2, item_0)

            item_0 = QProgressBar(self.orderbook)
            item_0.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_0.setStyleSheet("""
                QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                QProgressBar::Chunk {background-color : rgba(0, 255, 0, 40%);border : 1}
             """)

            self.orderbook.setCellWidget(10+i, 2, item_0)

            # 매수호가
            item_1 = QTableWidgetItem(str(""))
            item_1.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.orderbook.setItem(10 + i, 1, item_1)

            # 매도호가
            item_2 = QTableWidgetItem(str(""))
            item_2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.orderbook.setItem(9 - i, 1, item_2)

   
            item_3 = QProgressBar(self.orderbook)
            item_3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_3.setStyleSheet("""
                 QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                 QProgressBar::Chunk {background-color : rgba(255, 0, 0, 50%);border : 1}
             """)
            self.orderbook.setCellWidget(9 -i, 0, item_3)


        self.ow = OrderbookWorker()
        self.ow.dataSent.connect(self.SetOrderBook)
        self.start_orderbook.clicked.connect(self.RestartOrderbook)
        self.stop_orderbook.clicked.connect(self.StopOrderbook)
        self.ow.GlobalTicker.connect(self.SetGlobalTicker)

        # Thread Start
        self.bot.start()
        self.ow.start()

    def SetGlobalTicker(self, contents):
        self.orderbook_ticker.setText(str(contents))

    def SetOrderBook(self, data):
        
        max_list = list()
        for i in range(10):
            max_list.append(data[0]["orderbook_units"][i]["bid_size"])
            max_list.append(data[0]["orderbook_units"][i]["ask_size"])
        
        maxSize = max(max_list)

        for i in range(10):
            # ask 매도
            # bid 매수
            bid_price = data[0]["orderbook_units"][i]["bid_price"]
            bid_size = data[0]["orderbook_units"][i]["bid_size"]
            ask_price = data[0]["orderbook_units"][i]["ask_price"]
            ask_size = data[0]["orderbook_units"][i]["ask_size"]
            #item_0 = self.orderbook.item(10+i, 2)
            #item_0.setText(f"{bid_size}")
            item_1 = self.orderbook.item(10+i, 1)
            item_1.setText(f"{bid_price}")
            item_2 = self.orderbook.item(9-i, 1)
            item_2.setText(f"{ask_price}")
            #item_3 = self.orderbook.item(9-i, 0)
            #item_3.setText(f"{ask_size}")

            item_0 = self.orderbook.cellWidget(10+i, 2)
            item_0.setRange(0, maxSize)
            item_0.setFormat(f"{bid_size}")
            item_0.setValue(bid_size)
            
            item_3 = self.orderbook.cellWidget(9-i, 0)
            item_3.setRange(0, maxSize)
            item_3.setFormat(f"{ask_size}")
            item_3.setValue(ask_size)

    def RestartOrderbook(self):
        self.ow.restart()
    
    def StopOrderbook(self):
        self.ow.close()
    
    def Log(self, contents):
        self.log_text.appendPlainText(str(contents))
    def Balance(self, contents):
        self.info_balance.setText(str(contents))
    def TotalPnL(self, contents):
        self.info_pnl.setText(str(contents))

    def GetSignal1(self, contents):
        self.sig_signal1.setText(str(contents))
    def GetSignal2(self, contents):
        self.sig_signal2.setText(str(contents))
    def GetSignal3(self, contents):
        self.sig_signal3.setText(str(contents))

    # Buy Monitoring
    def GetTicker(self, ticker):
        self.sig_ticker.setText(ticker)
    def GetCurPrice(self, cur_price):
        self.cur_price.setText(str(cur_price))
    def GetFiveClose(self, five_close):
        self.sig_five_close_1.setText(str(five_close))
        self.sig_five_close_2.setText(str(five_close))
    def GetFiveOpen(self, five_open):
        self.sig_five_open.setText(str(five_open))
    def GetMAsignals(self, signals):
        self.sig_ma.setText(str(signals))
    def GetTargetPrice(self, target_price):
        self.sig_target_price.setText(str(target_price))
    def GetBuyCnt(self, buy_cnt):
        self.sig_buy_cnt.setText(str(buy_cnt))

    # Sell Monitoring
    def TargetTicker(self, contents):
        self.pro_ticker.setText(str(contents))
    def BuyPrice(self, contents):
        self.pro_buy_price.setText(str(contents))
    def CurPrice(self, contents):
        self.cur_price.setText(str(contents))
    def TargetPrice(self, contents):
        self.pro_target_price.setText(str(contents))
    def LossCutPrice(self, contents):
        self.pro_losscut_price.setText(str(contents))
    def PnL(self, contents):
        self.pro_pnl.setText(str(contents))
    def ProfitTime(self, contents):
        self.pro_profit_cnt.setText(str(contents))
    def LossTime(self, contents):
        self.pro_loss_cnt.setText(str(contents))

        # 시작버튼
        #self.start_btn.clicked.connect(self.StartBot)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    mainUi = MainWindows()
    mainUi.show()
    app.exec_()
        

    



