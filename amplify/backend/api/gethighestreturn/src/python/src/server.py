
import os
from dotenv import load_dotenv
import boto3
from flask_cors import CORS
from flask import Flask, request, jsonify
from itertools import groupby

import datetime as dt

# Load environment variables from .env file
load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)


app = Flask(__name__)
CORS(app)

def get_latest_items_by_symbol(table_name):
    table = dynamodb.Table(table_name)
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
    latest_items_sorted_by_roi = sorted(latest_items_by_symbol.values(), key=lambda x: float(x['roi']), reverse=True)
    
    result = []
    for item in latest_items_sorted_by_roi:
        # print(f"Symbol: {item['symbol']}, Name: {item['name']}, Roi: {item['roi']}")
        result.append({
                    "symbol": item['symbol'],#string
                    "name":item['name'],#string
                    "roi": item['roi'],#string
                    "created_at":item['created_at']#string
                })
    return jsonify(result)

BASE_ROUTE = "/highestreturn"

ONE_YEAR_ROUTE = "/oneyear"
@app.route(BASE_ROUTE+ONE_YEAR_ROUTE, methods=['GET'])
def get_latest_items_by_symbol_oneyear():
   return get_latest_items_by_symbol('higestreturnOneYear-dev')

THREE_MONTH_ROUTE = "/threemonth"
@app.route(BASE_ROUTE+THREE_MONTH_ROUTE, methods=['GET'])
def get_latest_items_by_symbol_threemonth():
    return get_latest_items_by_symbol('higestreturnThreeMonth-dev')
    

ONE_MONTH_ROUTE = "/onemonth"
@app.route(BASE_ROUTE+ONE_MONTH_ROUTE, methods=['GET'])
def get_latest_items_by_symbol_onemonth():
    return get_latest_items_by_symbol('highestreturnOneMonth-dev')
    

ONE_WEEK_ROUTE = "/oneweek"
@app.route(BASE_ROUTE+ONE_WEEK_ROUTE, methods=['GET'])
def get_latest_items_by_symbol_oneweek():
    return get_latest_items_by_symbol('higestreturnOneWeek-dev')


ONE_DAY_ROUTE = "/oneday"
@app.route(BASE_ROUTE+ONE_DAY_ROUTE, methods=['GET'])
def get_latest_items_by_symbol_oneday():
    return get_latest_items_by_symbol('higestreturnOneDay-dev')


if __name__ == "__main__":
   app.run(host='0.0.0.0',port=5050)
