import sys
import pyupbit
import time
import datetime
import math
import telegram
import pandas as pd


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

    


                    
                


                