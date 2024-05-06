from decimal import Decimal
import os
from dotenv import load_dotenv
import boto3
from flask_cors import CORS
from flask import Flask, request, jsonify
from uuid import uuid4
from datetime import datetime, timedelta
from itertools import groupby


import pandas as pd
import numpy as np
import yfinance as yf
import math
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

BASE_ROUTE = "/highestreturn"
table = dynamodb.Table('higestreturnOneYear-dev')

app = Flask(__name__)
CORS(app)

ONE_YEAR_ROUTE = "/oneyear"
@app.route(BASE_ROUTE+ONE_YEAR_ROUTE, methods=['GET'])
def get_latest_items_by_symbol():
    # Scan the table
    response = table.scan()

    # Get the items
    items = response['Items']

    # Convert 'created_at' from string to datetime and sort items by symbol and date
    items.sort(key=lambda x: (x['symbol'], dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f")))

    # Group items by symbol and select the most recent item in each group
    latest_items_by_symbol = {}
    for key, group in groupby(items, lambda x: x['symbol']):
        latest_items_by_symbol[key] = max(list(group), key=lambda x: x['created_at'])

    # Sort the latest items by symbol by ROI in descending order
    latest_items_sorted_by_roi = sorted(latest_items_by_symbol.values(), key=lambda x: x['roi'], reverse=True)
    print('latest_items_sorted_by_roi: ', latest_items_sorted_by_roi)
    
    result = []
    for item in latest_items_sorted_by_roi:
        print(f"Symbol: {item['symbol']}, Name: {item['name']}, Roi: {item['roi']}")
        result.append({
                    "symbol": item['symbol'],
                    "name":item['name'],
                    "roi": item['roi'],
                    "created_at":item['created_at']
                })
    print(result)
    return result

# if __name__ == "__main__":
#    app.run(host='0.0.0.0',port=5050)

get_latest_items_by_symbol()

