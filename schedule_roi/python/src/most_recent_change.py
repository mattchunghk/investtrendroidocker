import yfinance as yf
import matt_supertrend as mst
from backtesting_mac import add_squeeze_momentum, add_supertrend, add_supertrend_chatGPT, get_data
import datetime as dt

def most_recent_to_db(symbols, db_table
                        start_date=None, end_date=None, 
                        interval='1D',test_period='1Y'):
    # tickerSymbol = "BTC-USD"

    table = dynamodb.Table(db_table)

    period = 0    
    
    if test_period == "1Y":
        period = 365
    elif test_period == "3M":
        period = 90
    elif test_period == "1M":
        period = 30
    elif test_period == "1W":
        period = 7
    elif test_period == "1D":
        period = 1
    elif test_period == "1H":
        interval = "1h"
        period = 1
    
    
    
    # if no start_date or end_date is provided, use default values
    if start_date is None:
        # start_date = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=period-2)).strftime('%Y-%m-%d')
    if end_date is None:
        # end_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

    result = []

    table = dynamodb.Table(db_table)

    for symbol in symbols:
        try:
            # Fetch the data for the specified period and daily interval
            data = get_data(symbol, start_date, end_date, interval)

            # Apply the Supertrend indicator
            data = add_supertrend_chatGPT(data, 6, 10)
            # data = add_squeeze_momentum(data)
            # print('data: ', data.tail())

            # Check the specific conditions in the 'Supertrend' column
            last_4th_close = data.iloc[-4]['Close']
            last_close = data.iloc[-1]['Close']
            diff = last_close - last_4th_close
            percent = round(diff / last_4th_close * 100, 1)
            # print('percent:', percent, "%")
            changed = False

            if all(data.iloc[-4:-1]['Supertrend'] == False) and data.iloc[-1]['Supertrend'] == True:
                changed = True
                
            # if all(data.iloc[-4:-1]['squeeze_momentum_bar_up'] == False) and data.iloc[-1]['squeeze_momentum_bar_up'] == True:
            #     changed = True


            # if changed:
            result.append({
                'symbol': symbol,
                'changed': changed,
                'last_close': last_close,
                'percent': percent
            })

            table.put_item(
                            Item={
                            'id': str(uuid4()),  # Generate a unique id
                            'symbol': symbol,
                            "start_date": start_date,
                            "end_date": end_date,
                            'strategy_category': 'Supertrend',
                            'changed': changed,
                            'last_close': last_close,
                            'percent': percent,
                            'period' : test_period,
                            'strategy_category': 'Supertrend',
                            'product_category': 'Cryptocurrency',
                            'created_at': str(dt.datetime.now()),  # DynamoDB doesn't support datetime, so convert it to string
                            }

if __name__ == "__main__" :
    most_recent_to_db ()                  