
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
    print('response: ', response)

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
    delete_old_data(table,0)
    
    
                    
        
        
             
            




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
    
    # update_dynamodb_table(symbols, names, pd_table)
    # print("DONE update_dynamodb_table")
    
    perform_backtest(pd_table, investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1Y", "test_roi")
    # perform_backtest(pd_table, investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1Y", "higestreturnOneYear")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "3M", "higestreturnThreeMonth")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1M", "highestreturnOneMonth")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, interval, "1W", "higestreturnOneWeek")
    # perform_backtest(pd_table,investment, lot_size, sl_size, tp_size, commission, start_date, end_date, "1h", "1D", "higestreturnOneDay")
    

day_job()
