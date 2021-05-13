
import sys
import pyupbit
import time
import datetime
import math
import telegram
import pandas as pd

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QProgressBar, QTableWidgetItem
from PyQt5 import uic
from functions import Utils


class OrderbookWorker(QThread):

    dataSent = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.alive = True

    def run(self):

        access = "frGzp5hUEaQBNQ1uuO60Dx3QGkSm5ugsEVdfrpnr"
        #secret = lines[1].strip()
        secret = "L4wHqPfrfc7x8NYWHaL8IoUxbV8MBuhoxZG2ZHJa"
        upbit = pyupbit.Upbit(access, secret)

        Ticker = "KRW-DOGE"
        while self.alive:
            orderbook = pyupbit.get_orderbook(Ticker)
            time.sleep(0.1)
            self.dataSent.emit(orderbook)

    def close(self):
        self.alive = False

    def restart(self):
        self.alive = True



main_ui = uic.loadUiType("autoUpbit_v2.ui")[0]


class MainWindows(QMainWindow, main_ui):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        for i in range(10):
            # 매도호가
            item_0 = QTableWidgetItem(str(""))
            item_0.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.orderbook.setItem(10 + i, 2, item_0)

            item_1 = QTableWidgetItem(str(""))
            item_1.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.orderbook.setItem(10 + i, 1, item_1)

            item_2 = QTableWidgetItem(str(""))
            item_2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.orderbook.setItem(9 - i, 1, item_2)

            item_3 = QTableWidgetItem(str(""))
            item_3.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.orderbook.setItem(9 - i, 0, item_3)
            #item_2 = QProgressBar(self.orderbook)
            #item_2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            #item_2.setStyleSheet("""
            #     QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
            #     QProgressBar::Chunk {background-color : rgba(255, 0, 0, 50%);border : 1}
            # """)
            #self.orderbook.setCellWidget(i, 2, item_2)

        self.ow = OrderbookWorker()
        self.ow.dataSent.connect(self.SetOrderBook)
        self.start_orderbook.clicked.connect(self.RestartOrderbook)
        self.stop_orderbook.clicked.connect(self.StopOrderbook)
        self.ow.start()

    def SetOrderBook(self, data):
        for i in range(10):
            # ask 매도
            # bid 매수
            bid_price = data[0]["orderbook_units"][i]["bid_price"]
            bid_size = data[0]["orderbook_units"][i]["bid_size"]
            ask_price = data[0]["orderbook_units"][i]["ask_price"]
            ask_size = data[0]["orderbook_units"][i]["ask_size"]
            item_0 = self.orderbook.item(10+i, 2)
            item_0.setText(f"{bid_size}")
            item_1 = self.orderbook.item(10+i, 1)
            item_1.setText(f"{bid_price}")

            item_2 = self.orderbook.item(9-i, 1)
            item_2.setText(f"{ask_price}")
            item_3 = self.orderbook.item(9-i, 0)
            item_3.setText(f"{ask_size}")

    def RestartOrderbook(self):
        self.ow.restart()
    
    def StopOrderbook(self):
        self.ow.close()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    mainUi = MainWindows()
    mainUi.show()
    app.exec_()
