
import os
from dotenv import load_dotenv
import boto3
from flask_cors import CORS
from flask import Flask, request, jsonify
from itertools import groupby
import operator

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

def get_roi_variation(table_name):
    table = dynamodb.Table(table_name)

    # Scan the table
    response = table.scan()

    # Get the items
    items = response['Items']

    # Convert 'created_at' from string to datetime and sort items by symbol and date
    items.sort(key=lambda x: (x['symbol'], dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f")))

    # Group items by symbol and select the two most recent items in each group
    latest_two_items_by_symbol = {}
    for key, group in groupby(items, lambda x: x['symbol']):
        sorted_group = sorted(list(group), key=lambda x: x['created_at'], reverse=True)
        if len(sorted_group) >= 2:
            latest_two_items_by_symbol[key] = sorted_group[:2]

    # Calculate the variation in roi between the latest and second latest item for each symbol
    roi_variations = {}
    for key, items in latest_two_items_by_symbol.items():
        variation = float(items[0]['roi']) - float(items[1]['roi'])
        roi_variations[key] = {
            "roi_variation": variation,
            "name": items[0]['name'],
            "latest_roi": items[0]['roi'],
            "second_latest_roi": items[1]['roi'],
            "created_at": items[0]['created_at']
        }

    # Sort the variations in descending order
    sorted_roi_variations = sorted(roi_variations.items(), key=lambda x: x[1]['roi_variation'], reverse=True)

    result = []
    for item in sorted_roi_variations:
        result.append({
            "symbol": item[0],
            "name": item[1]['name'],
            "roi_variation": str(item[1]['roi_variation']),
            "latest_roi": item[1]['latest_roi'],
            "second_latest_roi": item[1]['second_latest_roi'],
            "created_at": item[1]['created_at']
        })

    return jsonify(result)

BASE_ROUTE = "/mostrecentchange"

ONE_YEAR_ROUTE = "/oneyear"
@app.route(BASE_ROUTE+ONE_YEAR_ROUTE, methods=['GET'])
def run_get_roi_variation_one_year():
    return get_roi_variation('higestreturnOneYear-dev')

THREE_MONTH_ROUTE = "/threemonth"
@app.route(BASE_ROUTE+THREE_MONTH_ROUTE, methods=['GET'])
def run_get_roi_variation_three_month():
    return get_roi_variation('higestreturnThreeMonth-dev')



ONE_MONTH_ROUTE = "/onemonth"
@app.route(BASE_ROUTE+ONE_MONTH_ROUTE, methods=['GET'])
def run_get_roi_variation_one_month():
    return get_roi_variation('highestreturnOneMonth-dev')


ONE_WEEK_ROUTE = "/oneweek"
@app.route(BASE_ROUTE+ONE_WEEK_ROUTE, methods=['GET'])
def run_get_roi_variation_one_week():
    return get_roi_variation('higestreturnOneWeek-dev')



ONE_DAY_ROUTE = "/oneday"
@app.route(BASE_ROUTE+ONE_DAY_ROUTE, methods=['GET'])
def run_get_roi_variation_one_day():
    return get_roi_variation('higestreturnOneDay-dev')


if __name__ == "__main__":
   app.run(host='0.0.0.0',port=5050)
