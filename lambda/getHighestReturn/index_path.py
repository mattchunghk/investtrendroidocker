import boto3
from boto3.dynamodb.conditions import Key
import datetime as dt
import json

def lambda_handler(event, context):
    print(event)
    # Assuming event["body"] is a JSON string, parse it into a dictionary
    # new_event = event["path"]
    period = event["path"]
    print(period)

    table_mapping = {
        "/getHighestReturn/oneyear": "higestreturnOneYear",
        "/getHighestReturn/threemonth": "higestreturnThreeMonth",
        "/getHighestReturn/onemonth": "highestreturnOneMonth",
        "/getHighestReturn/oneweek": "higestreturnOneWeek",
        "/getHighestReturn/oneday": "higestreturnOneDay",
        "/getHighestReturn/test": "test_roi"
    }

    db_table = table_mapping.get(period)

    # if db_table is None:
    #     return {
    #         'statusCode': 400,
    #         'headers': {'Content-Type': 'application/json'},
    #         'body': json.dumps({'message': 'Please enter the right period 1Y/3M/1M/1W/1D'})  # This is now a JSON string
    #     }
   
        
        
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(db_table)
    # Get the current date in 'YYYY-MM-DD' format
    # today_date = datetime.now().strftime('%Y-%m-%d')
    yesterday_date = (dt.datetime.now() - dt.timedelta(days=0)).strftime('%Y-%m-%d')

    # Perform the scan operation
    # response = table.scan()
    response = table.query(
        IndexName='end_date-index', 
        KeyConditionExpression=Key('end_date').eq(yesterday_date)
    )

    # Get the items
    items = response['Items']
    print('items: ', items)

  # Convert 'created_at' from string to datetime and group items by 'symbol' and 'name'
    grouped_items = {}
    for item in items:
        item['created_at_datetime'] = dt.datetime.strptime(item['created_at'], "%Y-%m-%d %H:%M:%S.%f")
        key = (item['symbol'], item['name'])
        if key not in grouped_items:
            grouped_items[key] = item
        else:
            # If the current item is newer, replace the older one
            if item['created_at_datetime'] > grouped_items[key]['created_at_datetime']:
                grouped_items[key] = item

    # Extract the latest items from the groups
    latest_items = list(grouped_items.values())

    # Prepare the results without the temporary 'created_at_datetime' field and sort by 'roi'
    result_sorted = sorted(
        [{
            "symbol": item['symbol'],
            "name": item['name'],
            "roi": item['roi'],
            "created_at": item['created_at']
        } for item in latest_items],
        key=lambda x: float(x['roi']),
        reverse=True
    )

    # Print and return the sorted results
    for item in result_sorted:
        print(f"Symbol: {item['symbol']}, Name: {item['name']}, ROI: {item['roi']}, Created At: {item['created_at']}")

    # Manually serialize 'result_sorted' to JSON
    serialized_result = json.dumps(result_sorted)

    # Return the sorted results
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': serialized_result  # This is now a JSON string of the sorted results
    }
    
if __name__ == "__main__":
    # event = {'path':'/getHighestReturn/test'}
    event = {'path':'/getHighestReturn/oneyear'}
    lambda_handler(event, None)