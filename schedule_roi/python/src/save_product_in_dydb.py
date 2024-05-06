# import os
import pandas as pd
from requests_html import HTMLSession
from datetime import datetime
import boto3
import os
from boto3.dynamodb.conditions import Key
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"
import yfinance as yf
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)

# table = dynamodb.Table('investment_products-dev')
table = dynamodb.Table('test_roi')

def get_yfinance_crypto_list(number_of_crypto: int):
    # yf.set_tz_cache_location("/temp/")
    session = HTMLSession()
    num_currencies = number_of_crypto
    resp = session.get(f"https://finance.yahoo.com/crypto?offset=0&count={num_currencies}")
    tables = pd.read_html(resp.html.raw_html)
    df = tables[0].copy()
    symbols_yf_list = df.Symbol.tolist()[0:]
    Name_yf_list = df.Name.tolist()[0:]
    return symbols_yf_list, Name_yf_list

def empty_dynamodb_table(table):
    # Perform a scan to retrieve all items
    response = table.scan()
    items = response['Items']
    print('items: ', items)

    # Loop through the items and delete each one
    with table.batch_writer() as batch:
        for item in items:
            print('item: ', item['id'])
            batch.delete_item(
                
                    {'id':str(item['id']),
                     'roi':str(item['roi'])}
                
            )
    print("Table emptied.")

# empty_dynamodb_table(table)

def get_dynamodb_items(table):
    response = table.query(
        IndexName='end_date-index',
        KeyConditionExpression=Key('end_date').eq('2024-01-28')
    )
    print('response: ', response)
    
    if 'Items' in response:
        items = response['Items']
        for item in items:
            print('Result: ', item)
            # Access individual attributes of the item
            # symbol = item['symbol']
            # Do something with the attributes
        
    else:
        print('No items found')
    # response = table.scan()
    # items = response['Items']
    # print('items: ', items)
    # for item in items:
    #     if item['end_date'] == '2024-01-27':
    #         print(item[item])
    


def update_dynamodb_table(symbols: list, names: list, table):
    
    # # Empty the table first
    # empty_dynamodb_table(table)
    
    for symbol, name in zip(symbols, names):
        try:
            # response = table.get_item(Key={'symbol': symbol})
            response = table.query(KeyConditionExpression=Key('symbol').eq((str(symbol))))
            # print('response: ', response)
            # print('response: ', response["symbol"])
            if response["Count"] == 0:
                table.put_item(
                    Item={
                        'category': 'Cryptocurrency',
                        'updated_at': datetime.utcnow().isoformat(timespec='milliseconds'),
                        'created_at': datetime.utcnow().isoformat(timespec='milliseconds'),
                        'name': str(name),
                        'symbol': str(symbol)
                    }
                )
                print(f"Added/Updated item for symbol: {symbol}")
            # else:
            #     print(f"{symbol} already in db")
        except Exception as e:
            print(f"An error occurred while updating the table for symbol {symbol}: {str(e)}")
            
            
if __name__ == "__main__":
    get_dynamodb_items(table)
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# region_name = os.getenv('AWS_REGION')

# dynamodb = boto3.resource('dynamodb', 
#                           aws_access_key_id=aws_access_key_id, 
#                           aws_secret_access_key=aws_secret_access_key, 
#                           region_name=region_name)

# table = dynamodb.Table('investment_products-dev')

# # Get the list of cryptocurrencies
# symbols, names = get_yfinance_crypto_list(250)

# # Update the dynamodb table
# update_dynamodb_table(symbols, names, table)

# print("Done")