
import pandas as pd
import numpy as np
# from datetime import datetime
import yfinance as yf
# import math
# import matplotlib.pyplot as plt

# symbol = "BTC-USD"

# SuperTrend parameters
atr_period = 10
multiplier = 3

# Squeeze_momentum parameters
length = 20
mult = 2
length_KC = 20
mult_KC = 1.5


def get_data(symbol, start_date, end_date, time_frame):
    df = yf.download(symbol, start=start_date,
                     end=end_date, interval=time_frame)
    return df


def add_supertrend(df):

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
    atr = true_range.ewm(alpha=1/atr_period, min_periods=atr_period).mean()
    # df['atr'] = df['tr'].rolling(atr_period).mean()

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = hl2 + (multiplier * atr)
    final_lowerband = hl2 - (multiplier * atr)

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

    df['Supertrend'] = pd.DataFrame(data=supertrend, index=df.index)
    df['Final Lowerband'] = pd.DataFrame(data=final_lowerband, index=df.index)
    df['Final Upperband'] = pd.DataFrame(data=final_upperband, index=df.index)

    return df


def add_squeeze_momentum(df):
    # calculate BB
    m_avg = df["Close"].rolling(window=length).mean()
    m_std = df["Close"].rolling(window=length).std(ddof=0)
    df['upper_BB'] = m_avg + mult * m_std
    df['lower_BB'] = m_avg - mult * m_std

    # calculate true range
    df['tr0'] = abs(df["High"] - df["Low"])
    df['tr1'] = abs(df["High"] - df["Close"].shift())
    df['tr2'] = abs(df["Low"] - df["Close"].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

    # calculate KC
    range_ma = df['tr'].rolling(window=length_KC).mean()
    df['upper_KC'] = m_avg + range_ma * mult_KC
    df['lower_KC'] = m_avg - range_ma * mult_KC

    # calculate bar value
    highest = df["High"].rolling(window=length_KC).max()
    lowest = df["Low"].rolling(window=length_KC).min()
    m1 = (highest + lowest)/2
    df['bar_value'] = (df["Close"] - (m1 + m_avg)/2)
    fit_y = np.array(range(0, length_KC))
    df['bar_value'] = df['bar_value'].rolling(window=length_KC).apply(lambda x: np.polyfit(
        fit_y, x, 1)[0] * (length_KC-1) + np.polyfit(fit_y, x, 1)[1], raw=True)

    df = df.assign(squeeze_momentum_bar_up=lambda x: (
        x['bar_value'] > x['bar_value'].shift()))

    # check for 'squeeze'
    df['squeeze_on'] = (df['lower_BB'] > df['lower_KC']) & (
        df['upper_BB'] < df['upper_KC'])
    df['squeeze_off'] = (df['lower_BB'] < df['lower_KC']) & (
        df['upper_BB'] > df['upper_KC'])

    df["Date"] = df.index

    return df


def backtest_supertrend(df, investment, sl_size, tp_size):

    is_uptrend = df['Supertrend']
    close = df['Close']

    low = df['Low']
    high = df['High']
    open = df['Open']
    date = df['Date']

    # it is the max value of the price of the double peak/double bottom pattern
    price1 = np.nan
    # it is the min value of the price of the double peak/double bottom pattern
    price0 = np.nan
    # It indicates the price of enter after the trigger signal happened.
    # For double bottom, enter only happened when the close price is higher than price1 as shown below.
    # For double peak, enter only happened when the close price is lower than price0 as shown below.
    price2 = np.nan
    # The exit price of the trade
    price3 = np.nan

    squeeze_off = df['squeeze_off']
    # squeeze_bar_value = df['bar_value']
    squeeze_momentum_bar_up = df['squeeze_momentum_bar_up']

    # initial condition
    in_position = False
    equity = investment
    commission = 5
    # Stoploss=stopLoss
    point_size = 1
    stopLoss = sl_size * point_size
    targetProfit = tp_size * point_size
    share = 0
    entry = []
    exit = []

    # Those are the lists used to log all the entries for the open date,close date,open price, close price of the trade
    trade_type = []
    trade_triggerdate = []
    trade_OpenDate = []
    trade_CloseDate = []
    trade_OpenPrice = []
    trade_ClosePrice = []
    trade_ExitReason = []

    for i in range(1, len(df)):

        # if i >0:
        #     if squeeze_bar_value[i] >squeeze_bar_value[i-1]:
        #         squeeze_momentum_bar_up = True
        #     else:
        #         squeeze_momentum_bar_up = False
        # else:
        #     squeeze_momentum_bar_up = False

        # if not in position & price is on uptrend and squeeze off and momentum bar going up-> buy
        if not in_position and is_uptrend[i] and squeeze_off[i] and squeeze_momentum_bar_up[i]:
            # if not in_position and is_uptrend[i]:

            price1 = max(high.iloc[i], high.iloc[i-1])
            price0 = min(low.iloc[i], low.iloc[i-1])
            date_trigger = date.iloc[i]
            price2 = close.iloc[i]

            # trade_type.append(enter_signal)
            trade_triggerdate.append(date_trigger)
            trade_OpenDate.append(date.iloc[i])
            trade_OpenPrice.append(price2)

            # share = math.floor(equity / close[i] / 100) * 100
            share = round((equity / close[i]), 4)
            equity -= share * close[i]
            entry.append((i, close[i]))
            in_position = True
            print(
                f'Buy {share} shares at {round(close[i],2)} on {df.index[i].strftime("%Y/%m/%d")}')
        # if in position & price is not on uptrend -> sell
        elif in_position and not is_uptrend[i]:
            equity += share * close[i] - commission
            exit.append((i, close[i]))
            in_position = False
            trade_CloseDate.append(date.iloc[i])
            print(
                f'Sell at {round(close[i],2)} on {df.index[i].strftime("%Y/%m/%d")}, reason "Not UpTrend"')

        elif stopLoss != 0 and in_position and low.iloc[i] <= price0-stopLoss:
            trade_ExitReason.append("Stop Loss")
            if (open.iloc[i] >= price0-stopLoss):
                price3 = price0-stopLoss
            else:
                price3 = open.iloc[i]
            trade_ClosePrice.append(price3)

            equity += share * price3 - commission
            exit.append((i, price3))
            in_position = False
            trade_CloseDate.append(date.iloc[i])
            print(
                f'Sell at {round(price3,2)} on {df.index[i].strftime("%Y/%m/%d")}, reason "Stop Loss"')

        elif targetProfit != 0 and in_position and high.iloc[i] >= price1+targetProfit:
            trade_ExitReason.append("Profit Target")
            if (open.iloc[i] <= price1+targetProfit):
                price3 = price2+targetProfit
            else:
                price3 = open.iloc[i]
            trade_ClosePrice.append(price3)

            equity += share * price3 - commission
            exit.append((i, price3))
            in_position = False
            trade_CloseDate.append(date.iloc[i])
            print(
                f'Sell at {round(price3,2)} on {df.index[i].strftime("%Y/%m/%d")}, reason "Profit Target"')

    # if still in position -> sell all share
    if in_position:
        equity += share * close[i] - commission

    earning = equity - investment
    roi = round(earning/investment*100, 2)
    print(
        f'Earning from investing $100k is ${round(earning,2)} (ROI = {roi}%)')
    return entry, exit, equity, roi
