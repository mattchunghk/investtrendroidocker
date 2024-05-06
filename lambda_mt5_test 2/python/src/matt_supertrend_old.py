import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import math
import datetime as dt
import requests
from requests_html import HTMLSession
import json
yf.set_tz_cache_location("/temp/")

def get_yfinance_crypto_list(number_of_crypto: int):
    session = HTMLSession()
    num_currencies = number_of_crypto
    resp = session.get(f"https://finance.yahoo.com/crypto?offset=0&count={num_currencies}")
    tables = pd.read_html(resp.html.raw_html)
    df = tables[0].copy()
    symbols_yf_list = df.Symbol.tolist()[0:]
    Name_yf_list = df.Name.tolist()[0:]
    return symbols_yf_list, Name_yf_list

def Supertrend(df, atr_period, multiplier):
    
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 
    # df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    
    # initialize Supertrend column to True
    supertrend = [True] * len(df)
    
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        
        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]
            
            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)
    
def backtest_supertrend(df, investment,commission,print_result,print_detail):
    
    # Calculate the ATR
    is_uptrend = df['Supertrend']
    close = df['Close']
    
    # initial condition
    in_position = False
    equity = investment
    commission = commission
    share = 0
    entry = []
    exit = []
    
    for i in range(1, len(df)):
        # print(i)
        # print(is_uptrend[i])
        # print(df.index[i])
        # if not in position & price is on uptrend -> buy
        if not in_position and is_uptrend[i]:
            share = math.floor(equity / close[i] / 100) * 100
            equity -= share * close[i]
            entry.append((i, close[i]))
            in_position = True
            if print_detail is True: 
                print(f'Buy {share} shares at {round(close[i],2)} on {df.index[i].strftime("%Y/%m/%d")}')
        # if in position & price is not on uptrend -> sell
        elif in_position and not is_uptrend[i]:
            equity += share * close[i] - commission
            exit.append((i, close[i]))
            in_position = False
            if print_detail is True: 
                print(f'Sell at {round(close[i],2)} on {df.index[i].strftime("%Y/%m/%d")}')
    # if still in position -> sell all share 
    if in_position:
        equity += share * close[i] - commission
    
    earning = equity - investment
    roi = round(earning/investment*100,2)
    if print_result is True: 
        print(f'Earning from investing ${int(investment/1000/1000)}M is ${round(earning,2)} (ROI = {roi}%)')
        print(" ")
    return entry, exit, roi


def find_optimal_parameter(fy_df, strategy, backtest, investment,commission,atr, multiplier ):
    # predefine several parameter sets- ****change
    atr_period=[]
    atr_multiplier = []
    
    if atr is None:
        atr_period = list(range(1, 20))
    elif atr > 0:
        atr_period = [atr]
        
    if multiplier is None:
        atr_multiplier = [i/2 for i in range(2, 41)]
    elif multiplier > 0:
        atr_multiplier = [multiplier]
    
    roi_list = []
    
    # for each period and multiplier, perform backtest
    for period, multiplier in [(x,y) for x in atr_period for y in atr_multiplier]:
        new_df = fy_df
        # supertrend = Supertrend(df, period, multiplier)
        # new_df = df.join(supertrend)
        strategy_df = strategy(fy_df, period, multiplier)
        new_df = fy_df.join(strategy_df)
        new_df = new_df[period:]
        entry, exit, roi = backtest(new_df, investment,commission,False,False)
        roi_list.append((period, multiplier, roi))
    
    # print(pd.DataFrame(roi_list, columns=['ATR_period','Multiplier','ROI']))
    
    # return the best parameter set
    return max(roi_list, key=lambda x:x[2])

def get_yf_df(symbol, start_date, end_date,interval,threads=True):
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    df = yf.download(
        tickers=symbol,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval=interval,
        # auto_adjust=True,
        threads=threads,
    )
        
    return df

def get_yf_df_with_best_parameters(symbols, start_date, end_date,interval, atr_period,multiplier):
    # Convert the dates to datetime objects
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')

    # Add one day to the end date to make sure the last day is included in the range
    end_date += dt.timedelta(days=1)

    # Fetch the data for the given symbol
    df = yf.download(
        tickers=symbols,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval=interval,
        threads=True,
    )

    # Calculate the Supertrend indicator using the ATR period and multiplier
    high = df['High']
    low = df['Low']
    close = df['Close']
    price_diffs = [high - low, high - close.shift(), close.shift() - low]
    tr = pd.concat(price_diffs, axis=1)
    tr = tr.abs().max(axis=1)
    atr = tr.ewm(alpha=1/atr_period, min_periods=atr_period).mean()
    hl2 = (high + low) / 2
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    supertrend = [True] * len(df)
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        else:
            supertrend[curr] = supertrend[prev]
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    supertrend = pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)
    df = df.join(supertrend)
    return df