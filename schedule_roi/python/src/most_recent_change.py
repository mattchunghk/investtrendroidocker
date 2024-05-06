import yfinance as yf
import matt_supertrend as mst
from backtesting_mac import add_squeeze_momentum, add_supertrend, add_supertrend_chatGPT, get_data

# Define the ticker symbol
tickerSymbol = "SEI-USD"

symbols, names = mst.get_yfinance_crypto_list(250)
result = []

for symbol in symbols:
    try:
        # Fetch the data for the specified period and daily interval
        data = get_data(symbol, "2024-04-01", "2024-05-01", "1D")

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
    except:
        print("")

# Sort the results by percent in descending order
result.sort(key=lambda x: x['percent'], reverse=True)

print(result)