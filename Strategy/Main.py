
# Develop Branch

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
from PyQt5.QtGui import QColor

# Users package
import Strategy1
import config
from functions import Utils


class OrderbookWorker(QThread):

    dataSent = pyqtSignal(list)
    GlobalTicker = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.alive = True

    def run(self):

        #global global_ticker

        while self.alive:

            self.GlobalTicker.emit(config.global_ticker)
            
            time.sleep(0.1)
            try:
                if config.global_ticker != "now running":
                    orderbook = pyupbit.get_orderbook(str(config.global_ticker))
                    self.dataSent.emit(orderbook)
            except:
                print("None type orderbook")

    def close(self):
        self.alive = False

    def restart(self):
        self.alive = True
        self.start()


main_ui = uic.loadUiType("autoUpbit_v2.ui")[0]

class MainWindows(QMainWindow, main_ui):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.bot = Strategy1.Bot()
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
        self.bot.TotalAskSize.connect(self.TotalAskSize)
        self.bot.TotalBidSize.connect(self.TotalBidSize)
        self.bot.TotalSize.connect(self.TotalSize)

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
        self.bot.GetSignal4.connect(self.GetSignal4)



 
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
        if contents > 0:
            self.cur_price.setTextColor(QColor(0,0,255))
        elif contents < 0:
            self.cur_price.setTextColor(QColor(255,0,0))
        self.info_pnl.setText(str(contents))

    def GetSignal1(self, contents):
        self.sig_signal1.setText(str(contents))
    def GetSignal2(self, contents):
        self.sig_signal2.setText(str(contents))
    def GetSignal3(self, contents):
        self.sig_signal3.setText(str(contents))
    def GetSignal4(self, contents):
        self.sig_signal4.setText(str(contents))

    # Buy Monitoring
    def GetTicker(self, ticker):
        self.sig_ticker.setText(ticker)

    def GetCurPrice(self, cur_price, target_price):
        self.cur_price.setText(str(cur_price))
        if cur_price > target_price:
            self.cur_price.setTextColor(QColor(0,0,255))
        elif cur_price < target_price:    
            self.cur_price.setTextColor(QColor(255,0,0))
        
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
    
    def TotalAskSize(self, contents):
        self.total_ask_size.setText(str(contents))
        self.total_ask_size.setTextColor(QColor(255,0,0))

    def TotalBidSize(self, contents):
        self.total_bid_size.setText(str(contents))
        self.total_bid_size.setTextColor(QColor(0,0,255))

    def TotalSize(self, contents):
        self.total_size.setText(str(contents))
        if contents > 0:
            self.total_size.setTextColor(QColor(255, 0, 0))
        elif contents < 0:
            self.total_size.setTextColor(QColor(0, 0, 255))

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
        if contents > 0:
            self.cur_price.setTextColor(QColor(0,0,255))
        elif contents < 0:
            self.cur_price.setTextColor(QColor(255,0,0))
        contents = f"{format(contents, '.2f')} %"
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
        

    



