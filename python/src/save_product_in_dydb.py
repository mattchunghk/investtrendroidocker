# import os
import pandas as pd
from requests_html import HTMLSession
from datetime import datetime
# import boto3
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

def get_yfinance_crypto_list(number_of_crypto: int):
    session = HTMLSession()
    num_currencies = number_of_crypto
    resp = session.get(f"https://finance.yahoo.com/crypto?offset=0&count={num_currencies}")
    tables = pd.read_html(resp.html.raw_html)
    df = tables[0].copy()
    symbols_yf_list = df.Symbol.tolist()[0:]
    Name_yf_list = df.Name.tolist()[0:]
    return symbols_yf_list, Name_yf_list

def update_dynamodb_table(symbols: list, names: list, table):
    for symbol, name in zip(symbols, names):
        try:
            response = table.get_item(Key={'symbol': symbol})
            if 'Item' not in response:
                table.put_item(
                    Item={
                        'category': 'Cryptocurrency',
                        'updated_at': datetime.utcnow().isoformat(timespec='milliseconds'),
                        'created_at': datetime.utcnow().isoformat(timespec='milliseconds'),
                        'name': name,
                        'symbol': symbol
                    }
                )
        except Exception as e:
            print(f"An error occurred while updating the table for symbol {symbol}: {str(e)}")
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