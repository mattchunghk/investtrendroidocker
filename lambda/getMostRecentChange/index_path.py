import boto3
from boto3.dynamodb.conditions import Key
from itertools import groupby
import datetime as dt
import json

def lambda_handler(event, context):
    print(event)
    # Assuming event["body"] is a JSON string, parse it into a dictionary
    # new_event = event["path"]
    period = event["path"]
    print(period)

    table_mapping = {
        "/getMostRecentChange/oneyear": "higestreturnOneYear",
        "/getMostRecentChange/threemonth": "higestreturnThreeMonth",
        "/getMostRecentChange/onemonth": "highestreturnOneMonth",
        "/getMostRecentChange/oneweek": "higestreturnOneWeek",
        "/getMostRecentChange/oneday": "higestreturnOneDay",
        "/getMostRecentChange/test": "test_roi"
    }

    db_table = table_mapping.get(period)
        
        
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(db_table)
    pd_table = dynamodb.Table('investment_products_local')
    # Get the current date in 'YYYY-MM-DD' format
    yesterday_date = (dt.datetime.now() - dt.timedelta(days=1)).strftime('%Y-%m-%d')
    print('yesterday_date: ', yesterday_date)
    two_day_date = (dt.datetime.now() - dt.timedelta(days=2)).strftime('%Y-%m-%d')

    response_yesterday = table.query(
        IndexName='end_date-index',
        KeyConditionExpression=Key('end_date').eq(yesterday_date)
    )

    # Query for today's data
    response_today = table.query(
        IndexName='end_date-index',
        KeyConditionExpression=Key('end_date').eq(str(two_day_date))
    )

    # Combine the items from both queries
    items = response_yesterday.get('Items', []) + response_today.get('Items', [])


    # Convert 'created_at' from string to datetime and sort items by symbol and date
    items.sort(key=lambda x: (x['symbol'], dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f")))

    # Get current date and time and subtract one day (24 hours)
    now = dt.datetime.now()
    today = dt.datetime(now.year, now.month, now.day, 0, 0, 0)
    yesterday = today - dt.timedelta(days=1)
    two_day = today - dt.timedelta(days=2)

    # Group items by symbol and select the latest item from yesterday and two_day
    latest_item_today_and_yesterday_by_symbol = {}
    for key, group in groupby(items, lambda x: x['symbol']):
        sorted_group = sorted(list(group), key=lambda x: dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f"), reverse=True)

        # Filter to get the latest item from yesterday
        latest_item_today = next((x for x in sorted_group if dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f") >= yesterday), None)
        
        # Filter to get the latest item from two_day
        latest_item_yesterday = next((x for x in sorted_group if dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f") < yesterday and dt.datetime.strptime(x['created_at'], "%Y-%m-%d %H:%M:%S.%f") >= two_day), None)

        if latest_item_today and latest_item_yesterday:
            latest_item_today_and_yesterday_by_symbol[key] = [latest_item_today, latest_item_yesterday]

    # Calculate the variation in roi between the latest item of today and two_day for each symbol
    roi_variations = {}
    for key, items in latest_item_today_and_yesterday_by_symbol.items():
        variation = float(items[0]['roi']) - float(items[1]['roi'])
        roi_variations[key] = {
            "roi_variation": variation,
            "name": items[0]['name'],
            "latest_roi": items[0]['roi'],
            "yesterday_latest_roi": items[1]['roi'],
            "latest_created_at": items[0]['created_at'],
            "yesterday_latest_created_at": items[1]['created_at']
        }

    # Sort the variations in descending order
    sorted_roi_variations = sorted(roi_variations.items(), key=lambda x: x[1]['roi_variation'], reverse=True)

    results = []

    for item in sorted_roi_variations:
        results.append({
            "symbol": item[0],
            "name": item[1]['name'],
            "roi_variation": str(round(item[1]['roi_variation'], 4)),
            "latest_roi": item[1]['latest_roi'],
            "yesterday_latest_roi": item[1]['yesterday_latest_roi'],
            "latest_created_at": item[1]['latest_created_at'],
            "yesterday_latest_created_at": item[1]['yesterday_latest_created_at']
        })

        
    # Manually serialize 'result_sorted' to JSON
    serialized_result = json.dumps(results)
    print('serialized_result: ', serialized_result)

    # Return the sorted results
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': serialized_result  # This is now a JSON string of the sorted results
    }
    
if __name__ == "__main__":
    event = {'path':'/getMostRecentChange/oneyear'}
    # event = {'path':'/getHighestReturn/oneyear'}
    lambda_handler(event, None)