import boto3
import datetime as dt
import json

def lambda_handler(event, context):
    print(event)
    # Assuming event["body"] is a JSON string, parse it into a dictionary
    new_event = json.loads(event["body"])
    period = new_event["period"]

    table_mapping = {
        "1Y": "higestreturnOneYear-dev",
        "3M": "higestreturnThreeMonth-dev",
        "1M": "highestreturnOneMonth-dev",
        "1W": "higestreturnOneWeek-dev",
        "1D": "higestreturnOneDay-dev"
    }

    db_table = table_mapping.get(period)

    if db_table is None:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Please enter the right period 1Y/3M/1M/1W/1D'})  # This is now a JSON string
        }
   
        
        
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(db_table)

    # Perform the scan operation
    response = table.scan()

    # Get the items
    items = response['Items']

    # Convert 'created_at' from string to datetime
    for item in items:
        item['created_at_datetime'] = dt.datetime.strptime(item['created_at'], "%Y-%m-%d %H:%M:%S.%f")

    # Find the latest 'created_at' date (not datetime)
    latest_created_at_date = max(item['created_at_datetime'].date() for item in items)
    print('latest_created_at_date: ', latest_created_at_date)

    # Filter items to keep only those with a 'created_at' date that matches the latest date
    latest_items_by_date = [item for item in items if item['created_at_datetime'].date() == latest_created_at_date]

    
    # Prepare the results without the temporary 'created_at_datetime' field
    result = [{
        "symbol": item['symbol'],
        "name": item['name'],
        "roi": item['roi'],
        "created_at": item['created_at']
    } for item in latest_items_by_date]

    # Sort the results by 'roi' in descending order
    result_sorted = sorted(result, key=lambda x: float(x['roi']), reverse=True)

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