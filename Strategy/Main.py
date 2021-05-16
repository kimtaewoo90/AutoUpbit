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
global_balance = 0
global_pnl = 0
global_profit_time = 0
global_loss_time = 0
#------------------------------------------------ #

# Test branch

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
    Balance = pyqtSignal(float)
    TotalPnL = pyqtSignal(float)
    ProfitTime = pyqtSignal(int)
    LossTime = pyqtSignal(int)

    # Targets
    GetTicker = pyqtSignal(int, str)
    GetCurPrice = pyqtSignal(int, float)
    GetBuyCnt = pyqtSignal(int, str)  # 매수여부
    GetSignals = pyqtSignal(int, str)
    GetPnL = pyqtSignal(int, str)


                          
    def __init__(self,targetNum, targetTicker):
        super().__init__()
        self.GlobalTicker = "KRW-BTC"
        self.targetNum = targetNum
        self.targetTicker = targetTicker
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
        global global_balance
        global global_pnl
        global global_profit_time
        global global_loss_time
        
        start_msg = True  # To send msg for first running bot

        # declare user imports
        util = Utils.UtilClass()
        conn = Utils.Connection()
        upbit = conn.ConnectToUpbit()
    

        #signals = Signals.Signals()
        start_balance = upbit.get_balance("KRW")
        global_balance = start_balance
        
        # start
        while True:

            if loss_time == 3:
                sleep_time = 3600
                util.SendMsg(f"Target Coin: {self.targetTicker}\nloss count : {loss_time}\nsleep time : {sleep_time} sec")
                time.sleep(sleep_time)
                loss_time = 0
                #start_orderbook = False

            # Monitoring the price for Buy coin
            while True:
                    

                self.Log.emit(f"Found Ticker, Target Coin is {self.targetTicker}")

                if start_msg is True:
                    util.SendMsg(f"Monitoring price of {self.targetTicker}")
                    self.Log.emit(f"Monitoring price of {self.targetTicker}")
                    start_msg = False
                    
                try:
                    res = util.GetTarget(self.targetTicker)
                    five_closed = res["close"]
                    five_open = pyupbit.get_ohlcv(self.targetTicker, "minute5")
                    five_open = five_open.iloc[-1]
                    five_open = five_open["open"]
                    five_temp = five_closed
                    cur_price = pyupbit.get_current_price(self.targetTicker)
                    time.sleep(0.5)
                except:
                    five_closed = five_temp

                if not type(cur_price) == float:
                    time.sleep(0.2)
                    cur_price = pyupbit.get_current_price(self.targetTicker)
                    self.Log.emit("Error with Get current price")

                buy_price = 0
                sell_price = 0
                balance = upbit.get_balance("KRW")
                judge_ma = util.GetMA(self.targetTicker, cur_price, 10, 5)
                
                target_price = round(five_closed * 1.005)

                # Signals Class instance
                signals = Signals.Signals()

                # Get signals
                signal1 = signals.signal1(cur_price, target_price)
                signal2 = signals.signal2(five_open, five_closed)
                signal3 = signals.signal3(judge_ma)

                # Display
                self.GetTicker.emit(self.targetNum, self.targetTicker)
                self.GetCurPrice.emit(self.targetNum, cur_price)
                #self.GetTargetPrice.emit(self.targetNum, round(five_closed * 1.005))
                #self.GetFiveClose.emit(self.targetNum, five_closed)
                #self.GetFiveOpen.emit(self.targetNum, five_open)
                self.GetSignals.emit(self.targetNum, str(signal1 and signal2 and signal3))
                self.GetBuyCnt.emit(self.targetNum, "False")
                self.Balance.emit(global_balance)
                #elf.Log.emit(f"{self.targetTicker} of balance is {balance}")

                # 1시간동안 매수가 없으면 티커 다시 찾기
                #if bot_start - datetime.datetime.now() > datetime.timedelta(hours=1):
                #    noMoreVol = False

                # Buy the coin
                if signal1 is True and signal2 is True and signal3 is True:
                    
                    buy_amt = global_balance - math.ceil(global_balance * 0.05)
                    buy_amt = buy_amt / 5
                    buy_price = cur_price
                    #resp = upbit.buy_market_order(Ticker, buy_amt)
                    upbit.buy_market_order(self.targetTicker, buy_amt)
                    print(f"Success to Buy {self.targetTicker} at {buy_price}")

                    # 매수여부 Display
                    self.GetBuyCnt.emit(self.targetNum, "True")

                    profit_price = round(buy_price * 1.02)
                    loss_price = math.ceil(buy_price * 0.95)

                    util.SendMsg(
                    f"""!Success to Buy!\nTicker : {self.targetTicker}\nBuy Price : {buy_price}\nTargetPrice : {profit_price}\nLossCut Price : {loss_price}
                    """)
                    self.Log.emit( f"""!Success to Buy!\nTicker : {self.targetTicker}\nBuy Price : {buy_price}\nTargetPrice : {profit_price}\nLossCut Price : {loss_price}
                    """)

                    
                    # Monitoring the price for Sell coin
                    while True:
                        try:
                            time.sleep(0.5)
                            profit_rate = 1.02
                            losscut_rate = 0.95
                            cur_price_to_sell = pyupbit.get_current_price(self.targetTicker)
                            #print(f"[{datetime.datetime.now()}]: Ticker : {self.targetTicker} / Buy_Price : {buy_price} / Current_Price : {cur_price_to_sell} / Target_Sell_Price : {profit_price} / LosCut_Sell_Price : {math.ceil(buy_price*losscut_rate)} / PnL : {format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %" )
                            #self.Log.emit(f"[{datetime.datetime.now()}]: Ticker : {Ticker} / Buy_Price : {buy_price} / Current_Price : {cur_price_to_sell} / Target_Sell_Price : {round(buy_price * 1.02)} / LosCut_Sell_Price : {math.ceil(buy_price*0.975)} / PnL : {format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %" )

                            monitoring_pnl = f"{format((cur_price_to_sell - buy_price)/buy_price * 100, '.2f')} %"
                            self.GetCurPrice.emit(self.targetNum, cur_price_to_sell)
                            #self.BuyPrice.emit(self.targetNum, buy_price)
                            #self.TargetPrice.emit(self.targetNum, round(buy_price * 1.02))
                            #self.LossCutPrice.emit(self.targetNum, math.ceil(buy_price * losscut_rate))
                            self.GetPnL.emit(self.targetNum, monitoring_pnl)

                            # Sell the coin
                            if cur_price_to_sell >= math.ceil(buy_price * 1.02) or cur_price_to_sell <= math.ceil(buy_price * losscut_rate):# or sell_timing is True:
                                remained_coin = upbit.get_balance(self.targetTicker)
                                resp_sell = upbit.sell_limit_order(self.targetTicker, cur_price_to_sell, remained_coin)
                                sell_price = cur_price_to_sell
                                uuid = resp_sell["uuid"]
                                print(uuid)
                                util.SendMsg("waiting for Limit Short Orders")
                                print("waiting for Limit Short Orders")
                                self.Log.emit(self.targetNum, "waiting for Limit Short Orders")

                                sell_start_time = time.time()
                                while True:
                                    state = upbit.get_order(self.targetTicker)
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
                                        upbit.sell_market_order(self.targetTicker, remained_coin)
                                        self.Log.emit( "시장가 매도 후 잔고 변경중(5sec)")
                                        time.sleep(5)
                                        res_balance = upbit.get_balance("KRW")
                                        total_gain = total_gain + (res_balance - balance)
                                        util.SendMsg(
                                        f"""시장가 매도 체결 결과\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                        """)
                                        self.Log.emit(f"""시장가 매도 체결 결과\nStart Balance : {round(balance)}\nEnd Balance : {round(res_balance)}\nGain : {round(res_balance - balance)}\nTotal PnL : {round(total_gain)}
                                        """)
                                        self.Balance.emit(res_balance)
                                        global_pnl = res_balance - start_balance
                                        self.TotalPnL.emit(global_pnl)
                                        df = pyupbit.get_ohlcv(self.targetTicker, "minute5")
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

                                        global_balance = res_balance
                                        global_pnl = global_balance - start_balance
                                        self.Balance.emit(global_balance)
                                        self.TotalPnL.emit(global_pnl)

                                        df = pyupbit.get_ohlcv(self.targetTicker, "minute5")
                                        five_bong = df.iloc[-1]
                                        sell_five_bong = five_bong.name
                                        break
                                
                                # 시장가 또는 지정가 매도가 체결 된 후 profit 인지 loss 인지 판단 & 알림
                                if sell_price > buy_price:
                                    profit_time = profit_time + 1
                                    total_profit_time = total_profit_time + 1
                                    global_profit_time = global_profit_time + 1
                                    
                                    util.SendMsg(f"Profit count : [ {global_profit_time} ]")
                                    self.Log.emit(f"Profit count : [ {global_profit_time} ]")

                                elif sell_price <= buy_price:
                                    loss_time = loss_time + 1
                                    total_loss_time = total_loss_time + 1
                                    global_loss_time = global_loss_time + 1
                                    util.SendMsg(f"loss count : [ {global_loss_time} ]")
                                    self.Log.emit( f"loss count : [ {global_loss_time} ]")


                                self.ProfitTime.emit(global_profit_time)
                                self.LossTime.emit(global_loss_time)
                            

                                # 매도시의 5분봉과 같은 5분봉에서 재매수 방지
                                while True:
                                    if datetime.datetime.now() - sell_five_bong > datetime.timedelta(minutes=5):
                                        util.SendMsg("Find signals in new Five scalping\n")
                                        self.Log.emit(self.targetNum, "Find signals in new Five scalping\n")
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

#main_ui = uic.loadUiType("autoUpbit_v2.ui")[0]
main_ui = uic.loadUiType("autoUpbit_v3_test.ui")[0]
class MainWindows(QMainWindow, main_ui):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        util = Utils.UtilClass()
        tickers = util.GetVolumeList()
        # top5 vols
        self.bot1 = Bot(1, tickers[0][0])
        self.bot2 = Bot(2, tickers[1][0])
        self.bot3 = Bot(3, tickers[2][0])
        self.bot4 = Bot(4, tickers[3][0])
        self.bot5 = Bot(5, tickers[4][0])
        
        # bot1
        self.bot1.Balance(self.Balance)
        self.bot1.TotalPnL(self.TotalPnL)
        self.bot1.ProfitTime(self.ProfitTime)
        self.bot1.LossTime(self.LossTime)
        self.bot1.GetTicker(self.GetTicker)
        self.bot1.GetCurPrice(self.GetCurPrice)
        self.bot1.GetBuyCnt(self.GetBuyCnt)
        self.bot1.GetSignals(self.GetSignals)
        self.bot1.GetPnL(self.GetPnL)

        #bot2
        self.bot2.Balance(self.Balance)
        self.bot2.TotalPnL(self.TotalPnL)
        self.bot2.ProfitTime(self.ProfitTime)
        self.bot2.LossTime(self.LossTime)
        self.bot2.GetTicker(self.GetTicker)
        self.bot2.GetCurPrice(self.GetCurPrice)
        self.bot2.GetBuyCnt(self.GetBuyCnt)
        self.bot2.GetSignals(self.GetSignals)
        self.bot2.GetPnL(self.GetPnL)

        #bot3
        self.bot3.Balance(self.Balance)
        self.bot3.TotalPnL(self.TotalPnL)
        self.bot3.ProfitTime(self.ProfitTime)
        self.bot3.LossTime(self.LossTime)
        self.bot3.GetTicker(self.GetTicker)
        self.bot3.GetCurPrice(self.GetCurPrice)
        self.bot3.GetBuyCnt(self.GetBuyCnt)
        self.bot3.GetSignals(self.GetSignals)
        self.bot3.GetPnL(self.GetPnL)
        #bot4
        self.bot4.Balance(self.Balance)
        self.bot4.TotalPnL(self.TotalPnL)
        self.bot4.ProfitTime(self.ProfitTime)
        self.bot4.LossTime(self.LossTime)
        self.bot4.GetTicker(self.GetTicker)
        self.bot4.GetCurPrice(self.GetCurPrice)
        self.bot4.GetBuyCnt(self.GetBuyCnt)
        self.bot4.GetSignals(self.GetSignals)
        self.bot4.GetPnL(self.GetPnL)
        #bot5
        self.bot5.Balance(self.Balance)
        self.bot5.TotalPnL(self.TotalPnL)
        self.bot5.ProfitTime(self.ProfitTime)
        self.bot5.LossTime(self.LossTime)
        self.bot5.GetTicker(self.GetTicker)
        self.bot5.GetCurPrice(self.GetCurPrice)
        self.bot5.GetBuyCnt(self.GetBuyCnt)
        self.bot5.GetSignals(self.GetSignals)
        self.bot5.GetPnL(self.GetPnL)


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
        self.bot1.start()
        self.bot2.start()
        self.bot3.start()
        self.bot4.start()
        self.bot5.start()
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
    
    def ProfitTime(self, contents):
        self.pro_profit_cnt.setText(str(contents))
    def LossTime(self, contents):
        self.pro_loss_cnt.setText(str(contents))
# target1, cur_price1, signal1, profit1, check_buy1


    def GetSignals(self, Num, contents):
        if Num == 1: self.signal1.setText(str(contents))
        elif Num == 2: self.signal2.setText(str(contents))
        elif Num == 3: self.signal3.setText(str(contents))
        elif Num == 4: self.signal4.setText(str(contents))
        elif Num == 5: self.signal5.setText(str(contents))
        
 

    # Buy Monitoring
    def GetTicker(self, Num, contents):
        if Num == 1: self.target1.setText(str(contents))
        elif Num == 2: self.target2.setText(str(contents))
        elif Num == 3: self.target3.setText(str(contents))
        elif Num == 4: self.target4.setText(str(contents))
        elif Num == 5: self.target5.setText(str(contents))
        
    
    
    def GetCurPrice(self, Num, contents):
        if Num == 1: self.cur_price1.setText(str(contents))
        elif Num == 2: self.cur_price2.setText(str(contents))
        elif Num == 3: self.cur_price3.setText(str(contents))
        elif Num == 4: self.cur_price4.setText(str(contents))
        elif Num == 5: self.cur_price5.setText(str(contents))    
    

    def GetBuyCnt(self, Num, contents):
        if Num == 1: self.check_buy1.setText(str(contents))
        elif Num == 2: self.check_buy2.setText(str(contents))
        elif Num == 3: self.check_buy3.setText(str(contents))
        elif Num == 4: self.check_buy4.setText(str(contents))
        elif Num == 5: self.check_buy5.setText(str(contents)) 

  
    def PnL(self, Num, contents):
        if Num == 1: self.profit1.setText(str(contents))
        elif Num == 2: self.profit2.setText(str(contents))
        elif Num == 3: self.profit3.setText(str(contents))
        elif Num == 4: self.profit4.setText(str(contents))
        elif Num == 5: self.profit5.setText(str(contents)) 
    
    


        # 시작버튼
        #self.start_btn.clicked.connect(self.StartBot)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    mainUi = MainWindows()
    mainUi.show()
    app.exec_()
        

    



