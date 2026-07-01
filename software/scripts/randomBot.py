#import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random

def generateStock(days, volatility, start_price):
    prices = [start_price]
    for i in range(days - 1):
        change = random.uniform(-1*volatility, volatility)
        prices.append(prices[-1] + change)

    return prices

#######################################################################
sims = 100 #number of monte carlo trials
start_price = 150 #initial price of the stock
volatility = 2 #how many $ can the price move daily
days = 100 #number of days the stock was traded for
#######################################################################
profits = []

for sim in range(sims):
    prices = generateStock(days, volatility, start_price) #instantiates the market
    stock_owned = False
    profit = 0

    for x in prices:
        if x > start_price and stock_owned == False: #time to buy
            stock_owned = True
            buy_price = x
        elif x <= start_price and stock_owned == True: #selling
            stock_owned = False
            sell_price = x
            profit += (sell_price - buy_price)
    
    profit = (profit/start_price)

    profits.append(profit)

#print(profits)
avg = sum(profits)/len(profits)
print(f"Average profit: {avg:.2%}")
median = np.median(profits)
print(f"Median profit: {median:.2%}")
maxval = max(profits)
print(f"Maximum profit: {maxval:.2%}")
minval = min(profits)
print(f"Minimum profit: {minval:.2%}")

#plotting mechanism
plot = plt.hist(profits)
plt.savefig("profits_histogram.png")