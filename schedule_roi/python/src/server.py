
import os
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
load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)

pd_table = dynamodb.Table('investment_products_local')
symbols, names = get_items_from_dynamodb(pd_table)
    
# dynamodb = boto3.resource('dynamodb', 
#                           aws_access_key_id="AKIAWFODOPGFGGIEVY7C", 
#                           aws_secret_access_key="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", 
#                           region_name="ap-southeast-1")


def delete_old_data(table, days_old=14):

    # Define the timestamp to compare with (14 days ago)
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d')

    
    # Use the DynamoDB query operation to find items with 'end_date' older than the cutoff date
    response = table.query(

        IndexName='end_date-index',  # Assuming 'end_date-index' is a global secondary index (GSI)
        KeyConditionExpression=Key('end_date').eq(cutoff_timestamp)  # lt stands for 'less than'
    )

    # Delete these items
    if response['Count'] > 0:
        with table.batch_writer() as batch:
            for item in response.get('Items', []):
                batch.delete_item(
                    Key={
                        'id': item['id']  # Assuming 'id' is the primary key
                    }
                )

        # If your table has a lot of items, handle query pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='end_date-index',
                KeyConditionExpression=Key('end_date').lt(cutoff_timestamp),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )

            with table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'id': item['id']
                        }
                    )


def perform_backtest(pd_table=dynamodb.Table('investment_products-dev'), investment=100000000,lot_size=0.1, sl_size=5000,tp_size=5000,
                     commission=0, start_date=None, end_date=None, interval='1d', test_period="1Y", db_table=""):


    print('db_table: ', db_table)
    table = dynamodb.Table(db_table)
    
    # Delete data older than 14 days before starting the backtest
    delete_old_data(table,14)
    
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

    strategy = mst.Supertrend
    backtest = mst.backtest
    
    
    
    results = []
    print('len(symbols): ', len(symbols))
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
            
                    
        
        
             
            




# Define the job function to be scheduled

def day_job():
    print("Performing backtest...")
    symbol_list_length=250
    investment=100000
    lot_size=1
    sl_size=0
    tp_size=0
    commission=0
    start_date=None
    end_date=None
    interval='1d'
    # test_period="1Y"
    # print_result=True
    # print_detail=True
    symbols, names = mst.get_yfinance_crypto_list(symbol_list_length)
    # pd_table = dynamodb.Table('investment_products-dev')
    pd_table = dynamodb.Table('investment_products_local')
    
    update_dynamodb_table(symbols, names, pd_table)
    print("DONE update_dynamodb_table")
    
    # perform_backtest(pd_table, investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1Y", "test_roi")
    perform_backtest(pd_table, investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1Y", "higestreturnOneYear")
    perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "3M", "higestreturnThreeMonth")
    perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1M", "highestreturnOneMonth")
    perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1W", "higestreturnOneWeek")
    perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, "1h", "1D", "higestreturnOneDay")
    

day_job()
