# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 16:58:34 2022

@author: Victor lee
"""

from utils.traad_deal_to_json import trade_deals_to_json
from mt5linux import MetaTrader5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import schedule
import pytz

# import talib as ta
# import yfinance as yf

# lot_size = 0.1
# sl_size = 5000
# tp_size = 5000
# pair = ["BTCUSD"]

mt5 = MetaTrader5(
    # host = 'localhost',
    host = '18.141.245.200',
    port = 18812      
)  


path = "/home/ubuntu/.wine/drive_c/Program Files/Pepperstone MetaTrader 5/terminal64.exe"
# path = "/Users/mattchung/.wine/drive_c/Program Files/Pepperstone MetaTrader 5/terminal64.exe"
server = 'Pepperstone-Demo'
username = 61164970
password = "1loveMt5!"

deviation = 10
# start_date = datetime(2023, 6, 13, 0, 0, 0, tzinfo=pytz.timezone('Hongkong'))

# Function to start Meta Trader 5 (MT5)


# def start_mt5(username, password, server, path):
def start_mt5():
    # Ensure that all variables are the correct type
    uname = int(username)  # Username must be an int
    pword = str(password)  # Password must be a string
    trading_server = str(server)  # Server must be a string
    filepath = str(path)  # Filepath must be a string

    # Attempt to start MT5
    if mt5.initialize(login=uname, password=pword, server=trading_server, path=filepath):
        # Login to MT5
        if mt5.login(login=uname, password=pword, server=trading_server):
            return True
        else:
            print("Login Fail")
            # quit()
            return PermissionError
    else:
        print("MT5 Initialization Failed")
        # quit()
        return ConnectionAbortedError


def connect():
    mt5.initialize()


def open_pending_position(symbol1, volume1, order_type, test_id, tp_distance=None, sl_distance=None):

    # filling_type = mt5.symbol_info(symbol1).filling_mode
    filling_type = mt5.ORDER_FILLING_IOC
    type1 = None
    point = mt5.symbol_info(symbol1).point
    price = mt5.symbol_info_tick(symbol1).ask
    if order_type == "BUY":
        # type1 = mt5.ORDER_TYPE_BUY_LIMIT
        type1 = mt5.ORDER_TYPE_BUY
        # price = mt5.symbol_info_tick(symbol).ask
        if sl_distance:
            sl = price - (sl_distance * point)
        if (tp_distance):
            tp = price + (tp_distance * point)

    elif order_type == "SELL":
        # type1 = mt5.ORDER_TYPE_SELL_LIMIT
        type1 = mt5.ORDER_TYPE_SELL
        # price = mt5.symbol_info_tick(symbol).bid
        if sl_distance:
            sl = price + (sl_distance * point)
        if (tp_distance):
            tp = price - (tp_distance * point)

    if tp_distance and sl_distance:
        request = {
            # "action": mt5.TRADE_ACTION_PENDING,
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol1,
            "volume": volume1,
            "type": type1,
            "price": price,
            "sl": sl,
            "tp": tp,
            "comment": test_id,
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
        }
    elif sl_distance:
        request = {
            # "action": mt5.TRADE_ACTION_PENDING,
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol1,
            "volume": volume1,
            "type": type1,
            "price": price,
            "sl": sl,
            "comment": test_id,
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
        }
    elif tp_distance:
        request = {
            # "action": mt5.TRADE_ACTION_PENDING,
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol1,
            "volume": volume1,
            "type": type1,
            "price": price,
            "tp": tp,
            "comment": test_id,
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
        }
    else:
        request = {
            # "action": mt5.TRADE_ACTION_PENDING,
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol1,
            "volume": volume1,
            "type": type1,
            "price": price,
            # "price": mt5.symbol_info_tick(symbol1).ask,
            "comment": test_id,
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC,
        }

    info_order = mt5.order_send(request)
    if info_order.retcode == 10009:
        print("### NEW Order for "+symbol1+" is sent and successful ###")
    else:
        print(f"###Error in sending order for {symbol1} ###")
        print("And the retcode is:"+str(info_order.retcode))
    return info_order


def close_open_position(ticket, symbol, volume, order_type, test_id):
    if order_type == "BUY":
        type = mt5.ORDER_TYPE_BUY
    elif order_type == "SELL":
        type = mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "position": ticket,
        "volume": volume,
        "type": type,
        "price": mt5.symbol_info_tick(symbol).bid,
        "deviation": deviation,
        "comment": test_id,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "type_time": mt5.ORDER_TIME_GTC
    }
    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("### Failed to close order ###")
        print("The failure code is:"+str(result.retcode))
    else:
        print("### Order successfully closed! ###")


def update_position(ticket, size=None, tp_distance=None, stop_distance=None):

    ticket_details = position_get_details(ticket)
    symbol = ticket_details["symbol"]
    if symbol is not None:
        filling_type = mt5.symbol_info(symbol).filling_mode
        point = mt5.symbol_info(symbol).point
        order_type = ticket_details["direction"]
        price = ticket_details["price"]

        if (order_type == 0):
            price = mt5.symbol_info_tick(symbol).ask
            if (stop_distance):
                sl = price - (stop_distance * point)
            if (tp_distance):
                tp = price + (tp_distance * point)

        if (order_type == 1):
            price = mt5.symbol_info_tick(symbol).bid
            if (stop_distance):
                sl = price + (stop_distance * point)
            if (tp_distance):
                tp = price - (tp_distance * point)

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": ticket,
            "sl": sl,
            "tp": tp,
            "type_filling": filling_type,
            "type_time": mt5.ORDER_TIME_GTC}

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("Failed to send order :(")
            print("The failure code is:"+str(result.retcode))
        else:
            print("Order successfully placed!")


def positions_get(symbol=None):
    if (symbol is None):
        res = mt5.positions_get()
    else:
        res = mt5.positions_get(symbol=symbol)

    if (res is not None and res != ()):
        df = pd.DataFrame(list(res), columns=res[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    return pd.DataFrame()


def position_get_details(ticket):
    symbol = None
    price = None
    sl_price = None
    tp_price = None
    direction = None
    for i in mt5.positions_get():
        if i.ticket == ticket:
            symbol = i.symbol
            price = i.price
            sl_price = i.sl
            tp_price = i.tp
            direction = i.type
    D1 = {"ticket": ticket, "symbol": symbol, "direction": direction,
          "price": price, "sl": sl_price, "tp": tp_price}
    return (D1)


def run_trader(pairs, time_frame, lot_size, sl_size, tp_size):
    print("Running trader at", datetime.now())
    # connect()
    start_mt5()
    pair_data = get_data(pairs, time_frame)
    forward_trade(pair_data, lot_size, sl_size, tp_size)


def get_data(pairs, time_frame, start_date):
    print('start_date: ', start_date)
    # pairs = ['XAUUSD','HK50','NAS100','USDJPY']
    pair_data = dict()
    print('pair_data: ', pair_data)
    for pair in pairs:
        timezone = pytz.timezone("Etc/UTC")
        utc_from = start_date - timedelta(days=180)
        
        utc_from = datetime(utc_from.year, utc_from.month, utc_from.day,
                           hour=utc_from.hour, minute=utc_from.minute,tzinfo=timezone)
        utc_form_timestamp = utc_from.timestamp()
        
        # utc_from = datetime(2023, 1, 1, tzinfo=pytz.timezone('Hongkong'))
        date_to = datetime.now().astimezone(pytz.timezone("Etc/UTC"))
        date_to = datetime(date_to.year, date_to.month, date_to.day,
                           hour=date_to.hour, minute=date_to.minute)
        date_to_timestamp = date_to.timestamp()


        # # date_to_unix = int(date_to.timestamp())
        
        # # utc_from_test = datetime(2023, 7, 10, tzinfo=timezone)
        # # utc_from_test_timestamp = utc_from_test.timestamp()
        # # date_from = datetime.fromtimestamp(utc_from_test_timestamp)
        # # utc_to = datetime(2023, 7, 11, hour = 13, tzinfo=timezone)
        rates = mt5.copy_rates_range(pair, time_frame, utc_form_timestamp, date_to_timestamp)
        
        # # set time zone to UTC
        # timezone = pytz.timezone("Etc/UTC")
        # # create 'datetime' objects in UTC time zone to avoid the implementation of a local time zone offset
        # utc_from = datetime(2020, 1, 10, tzinfo=timezone)
        # utc_to = datetime(2020, 1, 11, hour = 13, tzinfo=timezone)
        # # get bars from USDJPY M5 within the interval of 2020.01.10 00:00 - 2020.01.11 13:00 in UTC time zone
        # rates = mt5.copy_rates_range(pair, mt5.TIMEFRAME_M5, utc_from, utc_to)
        rates_frame = pd.DataFrame(rates)
        print('rates_frame: ', rates_frame)
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
        rates_frame.drop(rates_frame.tail(1).index, inplace=True)
        pair_data[pair] = rates_frame
    return pair_data


# def get_data(pairs, time_frame, start_date):
#     print('start_date: ', start_date)
#     pair_data = dict()
#     for pair in pairs:
#         # Calculate the beginning of the time range
#         utc_from = start_date - timedelta(days=180)
#         utc_from = datetime(utc_from.year, utc_from.month, utc_from.day,
#                            hour=utc_from.hour, minute=utc_from.minute)

#         # Get the current date and time in the Hong Kong timezone
#         date_to = datetime(date_to.year, date_to.month, date_to.day,
#                            hour=date_to.hour, minute=date_to.minute) 
#         date_to_unix = int(date_to.timestamp())

#         # Fetch data for the pair in the given time range and time frame
#         rates = mt5.copy_rates_range(pair, time_frame, utc_from, date_to_unix)
        
#         # Convert the fetched data into a DataFrame 
#         rates_frame = pd.DataFrame(rates)
#         # Convert the 'time' column to a datetime format
#         rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
#         # Drop the last row of the DataFrame
#         rates_frame.drop(rates_frame.tail(1).index, inplace=True)
        
#         # Add the DataFrame to the pair_data dictionary
#         pair_data[pair] = rates_frame
    
#     # Return the pair_data dictionary
#     return pair_data



# def check_trades(time_frame, pair_data):
#     for pair, data in pair_data.items():
#         data['EMA1'] = ta.EMA(data["close"], 8)
#         data['EMA2'] = ta.EMA(data["close"], 15)
#         data['EMA3'] = ta.EMA(data["close"], 30)

#         data = add_super_trend_indicator(data)
#         data = add_squeeze_momentum_indicator(data)

#         data["time"] = pd.to_datetime(data["time"], unit="s")
#         data.rename(columns={'time': "date"}, inplace=True)

#         last_row = data.iloc[-1, :]
#         for index, last in last_row.iterrows():
#             if (last["close"] > last['EMA1'] and last["open"] < last['EMA1'] and last["EMA1"] > last["EMA2"]):
#                 res1 = open_pending_position(pair, lot_size, "BUY")
#                 if res1.retcode == 10009:
#                     ticket1 = res1.order
#                     size1 = res1.volume
#                     res2 = update_position(
#                         ticket1, size1, tp_distance=tp_size, sl_distance=sl_size)
#                     if res2.retcode != 10009:
#                         print("Error in update SL and TP for order "+str(ticket1))
#                 else:
#                     print("Failed to send BUY order")
#                     print("The failure code is: "+str(res1.retcode))
#             if (last["close"] < last['EMA1'] and last["open"] > last['EMA1'] and last["EMA1"] < last["EMA2"]):
#                 res1 = open_pending_position(pair, lot_size, "SELL")
#                 if res1.retcode == 10009:
#                     ticket1 = res1.order
#                     size1 = res1.volume
#                     res2 = update_position(
#                         ticket1, size1, tp_distance=tp_size, sl_distance=sl_size)
#                     if res2.retcode != 10009:
#                         print("Error in update SL and TP for order "+str(ticket1))
#                 else:
#                     print("Failed to send SELL order")
#                     print("The failure code is: "+str(res1.retcode))


def get_forward_test_result(pairs, start_date, test_id):
    deal_data = dict()

    def check_test_id(deal):
        if deal.comment == test_id:
            return True
        return False
    for pair in pairs:
        timezone = pytz.timezone("Etc/UTC")
        utc_from = start_date - timedelta(days=180)
        
        utc_from = datetime(utc_from.year, utc_from.month, utc_from.day,
                           hour=utc_from.hour, minute=utc_from.minute,tzinfo=timezone)
        utc_form_timestamp = utc_from.timestamp()
        
        # utc_from = datetime(2023, 1, 1, tzinfo=pytz.timezone('Hongkong'))
        date_to = datetime.now().astimezone(pytz.timezone("Etc/UTC"))+ timedelta(days=1)
        date_to = datetime(date_to.year, date_to.month, date_to.day,
                           hour=date_to.hour, minute=date_to.minute)
        date_to_timestamp = date_to.timestamp()
        
        # utc_from = start_date - datetime.timedelta(days=180)
        # date_to = datetime.now().astimezone(pytz.timezone('Hongkong')) + datetime.timedelta(days=1)
        
        history_deals = mt5.history_deals_get(utc_form_timestamp, date_to_timestamp, group=pair)
        class_history_deals = filter(check_test_id, history_deals)
        class_history_deals = trade_deals_to_json(class_history_deals)

        # class_history_deals = tuple(class_history_deals)

        previous_position_id = None
        # deals_array = ()
        roi = 0
        profit = 0

        entry = []
        exit = []
        over_all = []
        
        for deal in class_history_deals:
   
            
            if previous_position_id != deal["position_id"]:
                # deals = []
                deals = mt5.history_deals_get(position=deal["position_id"])
                deals = trade_deals_to_json(deals)
                # deals_array = deals_array+deals
                for deal_position in deals:
                    profit += deal_position["profit"]
                    over_all.append(deal_position)
                    if deal_position["entry"] == 0:
                        entry.append(deal_position)
                    elif deal_position["entry"] == 1:
                        exit.append(deal_position)
            previous_position_id = deal["position_id"]
        first_entry = entry[0]
        investment = first_entry["price"]*first_entry["price"]
        if investment != 0:
            roi = (profit/investment)*100
        elif investment == 0:
            roi = 0
            

        deal_data[pair] = {"roi": roi,"profit":profit, "entry": entry, "exit": exit, "over_all":over_all}
    return deal_data


def forward_trade(pair_data, lot_size, sl_size, tp_size, start_date, test_id):
    results = {'trades': []}
    for pair, df in pair_data.items():
        df = add_super_trend_indicator(df)
        df = add_squeeze_momentum_indicator(df)

        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.rename(columns={'time': "date"}, inplace=True)

        last_row = df.iloc[-1, :]
        is_uptrend = last_row['Supertrend']
        close = last_row["close"]
        low = last_row["low"]
        high = last_row["high"]
        open = last_row["open"]
        date = last_row["date"]

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

        squeeze_off = last_row['squeeze_off']
        squeeze_momentum_bar_up = last_row['squeeze_momentum_bar_up']
        stop_loss = 0
        target_profit = 0
        had_deal_before = False
        order_type = None
        # initial condition
        order_in_position = mt5.positions_get(symbol=pair)
        open_price = None
        close_price = None

        def check_test_id(deal):
            if deal.comment == test_id:
                return True
            return False

        class_order_in_position = filter(check_test_id, order_in_position)
        class_order_in_position = tuple(class_order_in_position)
        if len(class_order_in_position) != 0:
            in_position = True
            order_type = class_order_in_position[0].type
        else:
            in_position = False
            # from_date=datetime(2023,1,1).timestamp()
            # to_date=datetime(2023,12,1).timestamp()
            timezone = pytz.timezone("Etc/UTC")
            utc_from = start_date - timedelta(days=180)
            
            utc_from = datetime(utc_from.year, utc_from.month, utc_from.day,
                            hour=utc_from.hour, minute=utc_from.minute,tzinfo=timezone)
            utc_form_timestamp = utc_from.timestamp()
            
            # utc_from = datetime(2023, 1, 1, tzinfo=pytz.timezone('Hongkong'))
            date_to = datetime.now().astimezone(pytz.timezone("Etc/UTC"))
            date_to = datetime(date_to.year, date_to.month, date_to.day,
                            hour=date_to.hour, minute=date_to.minute)
            date_to_timestamp = date_to.timestamp()
            
            history_deals = mt5.history_deals_get(utc_form_timestamp, date_to_timestamp, group=pair)
            # history_deals = mt5.history_deals_get(utc_from, date_to, group=pair)
            
            class_history_deals = filter(check_test_id, history_deals)
            class_history_deals = tuple(class_history_deals)
            if len(class_history_deals) != 0:
                had_deal_before = True
                last_position = class_history_deals[-1].position_id
                last_deals = mt5.history_deals_get(position=last_position)
                open_order_id = last_deals[-2].order
                close_order_id = last_deals[-1].order
                open_order = mt5.history_orders_get(ticket=open_order_id)
                if len(open_order) != 0:
                    stop_loss = open_order[0].sl
                    target_profit = open_order[0].tp
                    order_type = open_order[0].type
                    open_price = open_order[0].price_current
                close_order = mt5.history_orders_get(ticket=close_order_id)
                if len(close_order) != 0:
                    close_price = close_order[0].price_current

        # equity = investment
        commission = 5
        # Stoploss=stopLoss
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

        # for i in range(1, len(df)):
        print(f"test_id: {test_id}")
        print(date)
        print(f"in_position: {in_position}")
        print(f"is_uptrend: {is_uptrend}")
        # squeeze_off = True
        print(f"squeeze_off: {squeeze_off}")
        # squeeze_momentum_bar_up = False
        print(f"squeeze_momentum_bar_up: {squeeze_momentum_bar_up}")
        print(f"had_deal_before: {had_deal_before}")
        print(f"order_type: {order_type}")
        print(f"stop_loss: {stop_loss}")
        print(f"target_profit: {target_profit}")
        trade_info = {
            'pair': pair,
            'test_id': test_id,
            'date': str(date),
            'in_position': in_position,
            'is_uptrend': is_uptrend,
            'squeeze_off': squeeze_off,
            'squeeze_momentum_bar_up': squeeze_momentum_bar_up,
            'had_deal_before': had_deal_before,
            'order_type': order_type,
            'stop_loss': stop_loss,
            'target_profit': target_profit,
        }
        if close_price:
            print(f"close_price: {close_price}")
            trade_info['close_price'] = close_price

        # if not in position & had deal before and //was in buy position// & price was below stop loss -> have closed buy, mark Stop loss
        if not in_position and had_deal_before and order_type == 0 and close_price <= stop_loss:

            exit.append((date, close_price))

            print(
                f'Close buy at {stop_loss} on {date.strftime("%Y/%m/%d")}, reason "Buy reached Stop Loss"')

        # if not in position & had deal before and //was in buy position// & price was above Target Profit -> have closed buy, mark Profit Target
        elif not in_position and had_deal_before and order_type == 0 and close_price >= target_profit:

            exit.append((date, close_price))
            print(
                f'Close buy at {target_profit} on {date.strftime("%Y/%m/%d")}, reason "Buy reached Profit Target"')

        # if not in position & had deal before and //was in sell position// & price was above stop loss -> have closed sell, mark Stop loss
        elif not in_position and had_deal_before and order_type == 1 and stop_loss <= close_price:
            exit.append((date, close_price))
            # trade_CloseDate.append(date)
            print(
                f'Close sell at {stop_loss} on {date.strftime("%Y/%m/%d")}, reason "Sell reached Stop Loss"')

        # if not in position & had deal before and //was in sell position// & price was below Target Profit -> have closed sell, mark Profit Target
        elif not in_position and had_deal_before and order_type == 1 and target_profit >= close_price:
            exit.append((date, close_price))
            # trade_CloseDate.append(date)
            print(
                f'Close sell at {target_profit} on {date.strftime("%Y/%m/%d")}, reason "Sell reached Profit Target"')

        # if not in position & price is on uptrend and squeeze off and momentum bar going up-> buy
        if not in_position and is_uptrend and squeeze_off and squeeze_momentum_bar_up:
            res1 = open_pending_position(
                pair, lot_size, "BUY", test_id, tp_distance=tp_size, sl_distance=sl_size)
            if res1.retcode == 10009:
                ticket1 = res1.order
                size1 = res1.volume
                entry.append((date, res1.price))
                # trade_OpenDate.append(date)
                print(
                    f'Buy {size1} lots at {res1.price} on {date.strftime("%Y/%m/%d")}, reason "SuperTrend UpTrend"')
            else:
                print("Failed to send BUY order")
                print("The failure code is: "+str(res1.retcode))

        elif in_position and order_type == 0 and not is_uptrend:

            "Close buy, then sell"
            ticket = class_order_in_position[0].ticket
            close_open_position(ticket, pair, lot_size, "SELL", test_id)

            res1 = open_pending_position(
                pair, lot_size, "SELL", test_id, tp_distance=tp_size, sl_distance=sl_size)
            if res1.retcode == 10009:
                ticket1 = res1.order
                size1 = res1.volume
                entry.append((date, res1.price))
                # trade_OpenDate.append(date)
                print(
                    f'Close Buy {size1} lots at {res1.price} on {date.strftime("%Y/%m/%d")}, reason "SuperTrend Not UpTrend anymore"')

            else:
                print("Failed to send SELL order")
                print("The failure code is: "+str(res1.retcode))

        # if not in position & price is on downtrend and squeeze off and momentum bar going down-> sell
        elif not in_position and not is_uptrend and squeeze_off and not squeeze_momentum_bar_up:
            # "sell"
            res1 = open_pending_position(
                pair, lot_size, "SELL", test_id, tp_distance=tp_size, sl_distance=sl_size)
            if res1.retcode == 10009:
                ticket1 = res1.order
                size1 = res1.volume
                entry.append((date, res1.price))
                # trade_OpenDate.append(date)
                print(
                    f'Sell {size1} lots at {res1.price} on {date.strftime("%Y/%m/%d")}, reason "SuperTrend DownTrend"')
            else:
                print("Failed to send SELL order")
                print("The failure code is: "+str(res1.retcode))
        # if in position & sell & price is on uptrend -> close sell, then buy
        elif in_position and order_type == 1 and is_uptrend:
            "Close sell, then buy"
            ticket = class_order_in_position[0].ticket
            close_open_position(ticket, pair, lot_size, "BUY", test_id)

            res1 = open_pending_position(
                pair, lot_size, "BUY", test_id, tp_distance=tp_size, sl_distance=sl_size)
            if res1.retcode == 10009:
                ticket1 = res1.order
                size1 = res1.volume
                entry.append((date, res1.price))
                # trade_OpenDate.append(date)
                print(
                    f'Sell {size1} lots at {res1.price} on {date.strftime("%Y/%m/%d")}, reason "SuperTrend Not DownTrend anymore"')

            else:
                print("Failed to send BUY order")
                print("The failure code is: "+str(res1.retcode))
        else:
            if not in_position:
                print("Currently: Not in position")
                print("### No indicator triggered action ###")
            else:
                print(f"Currently: In position {order_in_position}")
                print("### No indicator triggered action ###")

################################
##### Trading strategies ######
################################


atr_period = 10
multiplier = 3

# symbol = 'AAPL'
# df = yf.download(symbol, start='2020-01-01')


def add_super_trend_indicator(df):

    high = df["high"]
    low = df["low"]
    close = df["close"]

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

    # return pd.DataFrame({
    #     'Supertrend': supertrend,
    #     'Final Lowerband': final_lowerband,
    #     'Final Upperband': final_upperband
    # }, index=df.index)


# def add_super_trend_indicator(df):
#     supertrend_indicator = super_trend(df)
#     df = df.join(supertrend_indicator)
#     return df


# parameter setup
length = 20
mult = 2
length_KC = 20
mult_KC = 1.5


def add_squeeze_momentum_indicator(df):
    # calculate BB
    m_avg = df["close"].rolling(window=length).mean()
    m_std = df["close"].rolling(window=length).std(ddof=0)
    df['upper_BB'] = m_avg + mult * m_std
    df['lower_BB'] = m_avg - mult * m_std

    # calculate true range
    df['tr0'] = abs(df["high"] - df["low"])
    df['tr1'] = abs(df["high"] - df["close"].shift())
    df['tr2'] = abs(df["low"] - df["close"].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

    # calculate KC
    range_ma = df['tr'].rolling(window=length_KC).mean()
    df['upper_KC'] = m_avg + range_ma * mult_KC
    df['lower_KC'] = m_avg - range_ma * mult_KC

    # calculate bar value
    highest = df["high"].rolling(window=length_KC).max()
    lowest = df["low"].rolling(window=length_KC).min()
    m1 = (highest + lowest)/2
    df['bar_value'] = (df["close"] - (m1 + m_avg)/2)
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

    return df


# def add_squeeze_momentum_indicator(df):
#     squeeze_momentum_indicator = squeeze_momentum(df)
#     df1 = df.join(squeeze_momentum_indicator)
#     return df1


################################
##### Scheduled Tasks ######
################################

def live_trading():
    schedule.every().hour.at(":00").do(run_trader, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":15").do(run_trader, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":30").do(run_trader, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":45").do(run_trader, mt5.TIMEFRAME_M15)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    print("MT5 tradingbot is being executed...")
    live_trading()
