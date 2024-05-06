
import os
from os.path import join, dirname
from dotenv import load_dotenv
import boto3

from uuid import uuid4
from datetime import datetime, timedelta
from itertools import groupby
import schedule
import time
from boto3.dynamodb.conditions import Key

import datetime as dt
import matt_supertrend as mst
from get_product_in_dydb import get_items_from_dynamodb
from save_product_in_dydb import update_dynamodb_table

# Load environment variables from .env file
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)



def lambda_handler(event, context):
    
    investment = event.get('investment', 100000000)
    lot_size = event.get('lot_size', 0.1)
    sl_size = event.get('sl_size', 5000)
    tp_size = event.get('tp_size', 5000)
    commission = event.get('commission', 0)
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    interval = event.get('interval', '1d')
    test_period = event.get('test_period', '1Y')
    db_table = event['db_table']
    symbols = event.get('symbols', [])
    names = event.get('names', [])


    print('db_table: ', db_table)
    table = dynamodb.Table("db_table")

    
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
    backtest = mst.backtest
    
    # symbols, names = get_items_from_dynamodb(pd_table)
    results = []
    # print('len(symbols): ', len(symbols))
    for i in range(len(symbols)):
        # if symbols[i] == "BTC-USD":
        try:
            print(i)
            symbol = symbols[i]
            # symbol = "ETH-USD"
            name = names[i]
            fy_df = mst.get_yf_df(symbol, start_date, end_date, interval)
            # print('start_date: ', start_date)
            # print('end_date: ', end_date)

            print(symbol)
            atr_period, multiplier, ROI = mst.find_optimal_parameter(fy_df, strategy, backtest, investment, lot_size, sl_size, tp_size,commission,None,None)
            print("Best parameter set: ATR Period={}, Multiplier={}, ROI={}%" .format(atr_period, multiplier, ROI))
            # best_df = mst.get_yf_df_with_best_parameters(symbol, start_date, end_date, interval,atr_period, multiplier)
            # mst.backtest(best_df, investment, lot_size, sl_size, tp_size, commission)
            print(" ")

            results.append({
                "symbol": symbol,
                "name":name,
                "ROI": round(ROI/100,4),
                "start_date": start_date,
                "end_date": end_date,
            })
            with table.batch_writer() as batch:
                for result in results:
                    # print('result: ', result)
                    try:    
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
                        print("item inserted")
                        results = []
                    except Exception as e:
                                print(e)
            
            
        except Exception as e:
                    print(e)
    print('Backtest completed successfully!')       

