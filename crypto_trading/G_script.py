# This script will take in some parameters and output your G so you can determine the feasibility of your strategy.
# Adjust data, then execute the script and see what happens!
# Note that you are expected to have read the Universal Growth Rate Model paper determining G - everything is there, this is just a tool that calculates it for you.
import math

def calculateG(mean_wr, trades, sigma, reward, stake, leverage, f_entry, f_exit, capital):
    sigma_new = math.sqrt((mean_wr * (1 - mean_wr)) / trades)

    G_one = ((mean_wr * stake * capital * reward * leverage) - ((1 - mean_wr) * stake * capital * leverage) - (f_entry + f_exit) * stake * capital * leverage) / capital
    G_two = (sigma ** 2) / (2 * (capital ** 2))
    
    delta = stake * capital * leverage * (reward + 1)
    G_three = ((sigma_new ** 2) * (delta ** 2)) / (2 * (capital ** 2))
    
    G = G_one - G_two - G_three
    return G

################################################
################# MODIFY THESE #################
################################################

mean_wr = 0.6
trades = 30
sigma = 15
capital = 1000
stake = 0.1
f_entry = 0.002
f_exit = 0.002
leverage = 2
reward = 2

#################################################
#################################################

print("The G for the strategy is:", round(calculateG(mean_wr, trades, sigma, reward, stake, leverage, f_entry, f_exit, capital), 3))
