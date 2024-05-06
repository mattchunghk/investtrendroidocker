
import os
from dotenv import load_dotenv
import boto3

from uuid import uuid4
from datetime import datetime, timedelta
from itertools import groupby
import schedule
import time


import datetime as dt
import matt_supertrend as mst

# Load environment variables from .env file
load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)

table = dynamodb.Table('higestreturnOneYear-dev')
# table = dynamodb.Table('run5yearshighestreturn-dev')

# app = Flask(__name__)
# CORS(app)



def perform_backtest(symbol_list_length=250, investment=10000000, commission=0, start_date=None, end_date=None, interval='1d', print_result=True, print_detail=True):
    
    # if no start_date or end_date is provided, use default values
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=1*365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    strategy = mst.Supertrend
    backtest = mst.backtest_supertrend

    symbols, names  = mst.get_yfinance_crypto_list(symbol_list_length)
    print('names: ', names)
    print('symbols: ', symbols)

    results = []

    for i in range(len(symbols)):
        symbol = symbols[i]
        name = names[i]
        print('name: ', name)
        fy_df = mst.get_yf_df(symbol, start_date, end_date, interval)

        print(symbol)
        atr_period, multiplier, ROI = mst.find_optimal_parameter(fy_df, strategy, backtest, investment, commission, None, None)
        print(f'Best parameter set: ATR Period={atr_period}, Multiplier={multiplier}, ROI={ROI}%')
        best_df = mst.get_yf_df_with_best_parameters(symbol, start_date, end_date, interval,atr_period, multiplier)
        mst.backtest_supertrend(best_df, investment, commission, True, False)
        print(" ")

        results.append({
            "symbol": symbol,
            "name":name,
            "ROI": round(ROI/100,4),
            "start_date": start_date,
            "end_date": end_date,
        })
        
        for result in results:
            table.put_item(
                Item={
                    'id': str(uuid4()),  # Generate a unique id
                    'symbol': result['symbol'],
                    'name': result['name'],
                    'product_category': 'Cryptocurrency',
                    'roi': str(result['ROI']),
                    "start_date": start_date,
                    "end_date": end_date,
                    'strategy_category': 'Supertrend',
                    'created_at': str(dt.datetime.now()),  # DynamoDB doesn't support datetime, so convert it to string
                    'updated_at': str(dt.datetime.now()),
                }
            )
            




# Define the job function to be scheduled
def job():
    print("Performing backtest...")
    perform_backtest()

# Schedule the job to run every hour
schedule.every(1).hour.do(job)

# Run the scheduler loop
while True:
    perform_backtest()
    schedule.run_pending()
    time.sleep(1)

# def get_latest_items_by_symbol():
#     # Scan the table
#     response = table.scan()

#     # Get the items
#     items = response['Items']

#     # Convert 'created_at' from string to datetime and sort items by symbol and date
#     items.sort(key=lambda x: (x['symbol'], dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f")))

#     # Group items by symbol and select the most recent item in each group
#     latest_items_by_symbol = {}
#     for key, group in groupby(items, lambda x: x['symbol']):
#         latest_items_by_symbol[key] = max(list(group), key=lambda x: x['created_at'])

#     # Sort the latest items by symbol by ROI in descending order
#     latest_items_sorted_by_roi = sorted(latest_items_by_symbol.values(), key=lambda x: x['roi'], reverse=True)
#     print('latest_items_sorted_by_roi: ', latest_items_sorted_by_roi)
    
#     result = []
#     for item in latest_items_sorted_by_roi:
#         print(f"Symbol: {item['symbol']}, Name: {item['name']}, Roi: {item['roi']}")
#         result.append({
#                     "symbol": item['symbol'],
#                     "name":item['name'],
#                     "roi": item['roi'],
#                     "Created_at":item['created_at']
#                 })

#     return result

# get_latest_items_by_symbol()


