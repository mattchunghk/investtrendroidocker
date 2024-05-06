from mt5linux import MetaTrader5
import mt5_tradingbot_mac as ft
import backtesting as bt
# import matplotlib.pyplot as plt
from datetime import datetime
import schedule
import time
import threading

mt5 = MetaTrader5(
    host = 'localhost',
    # host = '18.141.245.200',
    port = 18812      
)  


class Test:
    def __init__(self, test_id="TESTING", bt_symbol='BTC-USD', bt_start_date=datetime(2020, 1, 1),
                 bt_end_date=datetime(2023, 6, 1), bt_time_frame_backward='1d', bt_investment=100000,
                 bt_lot_size=1, bt_sl_size=0, bt_tp_size=0, ft_symbols=["BTCUSD"],
                 ft_time_frame_forward=mt5.TIMEFRAME_M3, ft_investment=100000, ft_lot_size=0.1,
                 ft_sl_size=5000, ft_tp_size=5000):
        self.bt_symbol = bt_symbol
        self.bt_start_date = bt_start_date
        self.bt_end_date = bt_end_date
        self.bt_time_frame_backward = bt_time_frame_backward
        self.bt_investment = bt_investment
        self.bt_lot_size = bt_lot_size
        self.bt_sl_size = bt_sl_size
        self.bt_tp_size = bt_tp_size
        # self.bt_stop_loss = bt_stop_loss
        # self.bt_target_profit = bt_target_profit

        # forward-testing parameters
        self.ft_symbols = ft_symbols
        self.ft_start_date = None
        self.ft_end_date = None
        self.ft_time_frame_forward = ft_time_frame_forward
        self.ft_investment = ft_investment
        self.ft_lot_size = ft_lot_size
        self.ft_sl_size = ft_sl_size  # To multiply with point
        self.ft_tp_size = ft_tp_size  # To multiply with point

        self.bt_price_data_with_indicator = None
        self.bt_entry = None
        self.bt_exit = None
        self.bt_equity = None
        self.bt_roi = None

        self.ft_entry = None
        self.ft_exit = None
        self.ft_equity = None
        self.ft_roi = None

        self.test_id = test_id

        self.scheduler = schedule.Scheduler()
        self.stop_flag = False

    def bt_get_data(self, start_date=None, end_date=None):
        self.bt_start_date = start_date
        if end_date:
            if self.ft_start_date:
                if end_date <= self.ft_start_date:
                    self.bt_end_date = end_date
                else:
                    self.bt_end_date = self.ft_start_date
            else:
                self.bt_end_date = end_date
        else:
            self.bt_end_date = datetime.now()
        past_date = bt.get_data(
            self.bt_symbol, self.bt_start_date, self.bt_end_date, self.bt_time_frame_backward)
        df_super = bt.add_supertrend(past_date)
        df_super_squeeze = bt.add_squeeze_momentum(df_super)
        # visualization
        # plt.plot(df_super_squeeze['Close'], label='Close Price')
        # plt.plot(df_super_squeeze['Final Lowerband'],
        #          'g', label='Final Lowerband')
        # plt.plot(df_super_squeeze['Final Upperband'],
        #          'r', label='Final Upperband')
        # plt.show()
        self.bt_price_data_with_indicator = df_super_squeeze

    def backtest_supertrend(self):
        entry, exit, equity, roi = bt.backtest_supertrend(
            self.bt_price_data_with_indicator, self.bt_investment, self.bt_sl_size, self.bt_tp_size)
        self.bt_entry = entry
        self.bt_exit = exit
        self.bt_equity = equity
        self.bt_roi = roi

    def start_forward_test(self):
        # self.bt_end_date = datetime.now()
        self.ft_start_date = datetime.now()
        ft.start_mt5()
        stock_data = ft.get_data(
            self.ft_symbols, self.ft_time_frame_forward, self.ft_start_date)
        ft.forward_trade(stock_data, self.ft_lot_size,
                         self.ft_sl_size, self.ft_tp_size, self.ft_start_date, self.test_id)

    def get_forward_test_result(self):
        self.ft_start_date = datetime.now()
        ft.start_mt5()
        history_orders = ft.get_forward_test_result(
            self.ft_symbols, self.ft_start_date, self.test_id)
        self.ft_roi = history_orders[str(self.ft_symbols[0])]['roi']
        self.ft_entry = history_orders[str(self.ft_symbols[0])]['entry']
        self.ft_exit = history_orders[str(self.ft_symbols[0])]['exit']
        # print(history_orders)

    def live_trading(self):
        print('Live trading')
        # A dictionary that maps MetaTrader 5 timeframes to their corresponding time intervals in minutes
        timeframe_minutes = {
            mt5.TIMEFRAME_M1: 1,
            mt5.TIMEFRAME_M2: 2,
            mt5.TIMEFRAME_M3: 3,
            mt5.TIMEFRAME_M4: 4,
            mt5.TIMEFRAME_M5: 5,
            mt5.TIMEFRAME_M6: 6,
            mt5.TIMEFRAME_M10: 10,
            mt5.TIMEFRAME_M12: 12,
            mt5.TIMEFRAME_M15: 15,
            mt5.TIMEFRAME_M20: 20,
            mt5.TIMEFRAME_M30: 30,
            mt5.TIMEFRAME_H1: 60,
            mt5.TIMEFRAME_H2: 120,
            mt5.TIMEFRAME_H3: 180,
            mt5.TIMEFRAME_H4: 240,
            mt5.TIMEFRAME_H6: 360,
            mt5.TIMEFRAME_H8: 480,
            mt5.TIMEFRAME_D1: 1440,
            mt5.TIMEFRAME_W1: 10080,
            mt5.TIMEFRAME_MN1: 43200
        }

        # Check if the value of self.ft_time_frame_forward is a valid key in the timeframe_minutes dictionary
        if self.ft_time_frame_forward not in timeframe_minutes:
            print("Invalid timeframe!")
        else:
            # Get the time interval in minutes for the selected timeframe
            interval = timeframe_minutes[self.ft_time_frame_forward]

            # Schedule the job to run at a specific interval based on the selected timeframe,
            # plus 3 seconds delay
            if interval >= 43200:  # For intervals greater than or equal to 1 month
                self.scheduler.every().month.at("00:00:03").do(
                    self.start_forward_test).tag('monthly', str(interval))

            elif interval >= 10080:  # For intervals greater than or equal to 1 week, but less than 1 month
                self.scheduler.every(interval // 10080).weeks.at("00:00:03").do(
                    self.start_forward_test).tag('weekly', str(interval))

            elif interval >= 1440:  # For intervals greater than or equal to 1 day, but less than 1 week
                self.scheduler.every(interval // 1440).days.at("00:00:03").do(
                    self.start_forward_test).tag('daily', str(interval))

            elif interval >= 60:  # For intervals between 60 minutes and 1 day
                self.scheduler.every(interval // 60).hours.at("00:00:03").do(
                    self.start_forward_test).tag('hourly', str(interval))

            else:  # For intervals less than 60 minutes
                interval_minutes = interval
                for hour in range(0, 24):
                    for minute in range(0, 60, interval_minutes):
                        self.scheduler.every().day.at("{:02d}:{:02d}:03".format(hour, minute)).do(
                            self.start_forward_test).tag('subhourly', str(interval))

        # Run the scheduled job continuously
        while True:
            while not self.stop_flag:
                self.scheduler.run_pending()
                time.sleep(1)
                # print("Running time frame " + str(self.ft_time_frame_forward))

            # mt5.set_callback(self.start_forward_test,
            # mt5.CALLBACK_TYPE.HISTORY)


def start_forward_test_thread(test_instance):
    test_instance.stop_flag = False
    thread = threading.Thread(target=test_instance.live_trading)
    thread.start()


def stop_forward_test_thread(test_instance):
    test_instance.stop_flag = True
