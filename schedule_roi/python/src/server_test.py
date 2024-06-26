
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
from get_product_in_dydb import get_items_from_dynamodb
from save_product_in_dydb import update_dynamodb_table

# Load environment variables from .env file
load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

    
dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)


# table = dynamodb.Table('run5yearshighestreturn-dev')

# app = Flask(__name__)
# CORS(app)



def perform_backtest(pd_table=dynamodb.Table('investment_products-dev'), investment=10000000, commission=0, start_date=None, end_date=None, interval='1d', test_period="1Y", db_table="", print_result=True, print_detail=True):


    print('db_table: ', db_table)
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
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    

        
        

    strategy = mst.Supertrend
    backtest = mst.backtest_supertrend

    # symbols, names  = mst.get_yfinance_crypto_list(symbol_list_length)
    symbols, names = get_items_from_dynamodb(pd_table)

    results = []
    print('len(symbols): ', len(symbols))
    for i in range(len(symbols)):
        
        try:
            print(i)
            symbol = symbols[i]
            name = names[i]
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
        except Exception as e:
                    print(e)
             
            




# Define the job function to be scheduled
def day_job():
    print("Performing backtest...")
    symbol_list_length=250
    investment=10000000
    commission=0
    start_date=None
    end_date=None
    interval='1d'
    test_period="1Y"
    print_result=True
    print_detail=True
    symbols, names = mst.get_yfinance_crypto_list(symbol_list_length)
    pd_table = dynamodb.Table('investment_products-dev')
    
    update_dynamodb_table(symbols, names, pd_table)
    print("DONE update_dynamodb_table")
    
    # perform_backtest(pd_table,investment, commission, start_date, end_date, interval, "1Y", "higestreturnOneYear-dev",print_result, print_detail)
    # perform_backtest(pd_table,investment, commission, start_date, end_date, interval, "3M", "higestreturnThreeMonth-dev",print_result, print_detail)
    # perform_backtest(pd_table,investment, commission, start_date, end_date, interval, "1M", "highestreturnOneMonth-dev",print_result, print_detail)
    # perform_backtest(pd_table,investment, commission, start_date, end_date, interval, "1W", "higestreturnOneWeek-dev",print_result, print_detail)
    perform_backtest(pd_table,investment, commission, start_date, end_date, '1h', "1D", "higestreturnOneDay-dev",print_result, print_detail)
    

# Schedule the job to run every hour
# schedule.every(1).day.do(day_job)
# schedule.every().day.at("00:00").do(day_job)

# # Run the scheduler loop
# while True:
#     day_job()
#     schedule.run_pending()
#     time.sleep(1)


day_job()