
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
import requests
import datetime as dt
import matt_supertrend as mst
from get_product_in_dydb import get_items_from_dynamodb
from save_product_in_dydb import update_dynamodb_table
import json
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)


# Define the job function to be scheduled
def lambda_handler(event, context):
    
    print("Performing backtest...")
    
    url = "https://rt5m4akfuk.execute-api.ap-southeast-1.amazonaws.com/default/schedule_roi_responder"
    data = {
                "investment": 100000000,
                "lot_size": 0.1,
                "sl_size": 5000,
                "tp_size": 5000,
                "commission": 0,
                "start_date": None,
                "end_date": None,
                "interval": "1d",
                "test_period": "1Y",
                "db_table": "event['db_table']",
                "symbols": [],
                "names": []
                }
    
    json_data = json.dumps(data)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    

    pd_table = dynamodb.Table('investment_products_local')

    symbols, names = get_items_from_dynamodb(pd_table)
    print('symbols: ', len(symbols))
    group = 10
    remaining = len(symbols) % group
    full_groups = len(symbols) // group
    index = 0
    
    for i in range(full_groups):
        print(index, index + group )
        print(symbols[index: index + group ])
        sorted_symbols = symbols[index: index + group ]
        sorted_names = names[index: index + group ]
        data = {
                "investment": 100000000,
                "lot_size": 1,
                "sl_size": 0,
                "tp_size": 0,
                "commission": 0,
                "start_date": None,
                "end_date": None,
                "interval": "1d",
                "test_period": "1Y",
                "db_table": "test_roi",
                "symbols": sorted_symbols,
                "names": sorted_names
                }
    
        json_data = json.dumps(data)
        response = requests.post(url, data=json_data, headers=headers)
        print('response: ', response)

        index += group
    remaining_symbols = symbols[index:index + remaining ]
    remaining_names = names[index:index + remaining ]
    data = {
                "investment": 100000000,
                "lot_size": 1,
                "sl_size": 0,
                "tp_size": 0,
                "commission": 0,
                "start_date": None,
                "end_date": None,
                "interval": "1d",
                "test_period": "1Y",
                "db_table": "test_roi",
                "symbols": remaining_symbols,
                "names": remaining_names
                }
    
    json_data = json.dumps(data)
    response = requests.post(url, data=json_data, headers=headers)
    print('response: ', response)
    

    # perform_backtest(pd_table, investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1Y", "higestreturnOneYear")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "3M", "higestreturnThreeMonth")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1M", "highestreturnOneMonth")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1W", "higestreturnOneWeek")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, "1h", "1D", "higestreturnOneDay")
    