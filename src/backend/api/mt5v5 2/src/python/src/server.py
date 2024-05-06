import full_bot_process_mac as full
import os
from dotenv import load_dotenv
import boto3
from flask import Flask, jsonify, request
from flask_cors import CORS
from boto3 import resource
from boto3.dynamodb.conditions import Key
import pytz 
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
# import mt5_tradingbot_mac as ft
import json
from mt5linux import MetaTrader5
mt5 = MetaTrader5(
    # host = 'localhost',
    host = '18.141.245.200',
    port = 18812      
)  

app = Flask(__name__)
CORS(app)

# Load environment variables from .env file

test_instances = []

timeframe_minutes = {
    'M1': mt5.TIMEFRAME_M1,
    'M2': mt5.TIMEFRAME_M2,
    'M3': mt5.TIMEFRAME_M3,
    'M4': mt5.TIMEFRAME_M4,
    'M5': mt5.TIMEFRAME_M5,
    'M6': mt5.TIMEFRAME_M6,
    'M10': mt5.TIMEFRAME_M10,
    'M12': mt5.TIMEFRAME_M12,
    'M15': mt5.TIMEFRAME_M15,
    'M20': mt5.TIMEFRAME_M20,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H2': mt5.TIMEFRAME_H2,
    'H3': mt5.TIMEFRAME_H3,
    'H4': mt5.TIMEFRAME_H4,
    'H6': mt5.TIMEFRAME_H6,
    'H8': mt5.TIMEFRAME_H8,
    'D1': mt5.TIMEFRAME_D1,
    'W1': mt5.TIMEFRAME_W1,
    'MN!': mt5.TIMEFRAME_MN1
}

load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key, 
                          region_name=region_name)

table = dynamodb.Table('test_by_users-dev')



@app.route("/create_test", methods=["POST"])
def create_test():
    global test_instances
    table = dynamodb.Table('test_by_users-dev')
    
    # Extract test_id from the request data
    test_id = request.json.get("test_id")
    user = request.json.get("user")
    if test_id is None:
        return jsonify({"error": "Missing test_id"}), 400
    
    # Check if the test_id already exists in DynamoDB table
    response = table.get_item(Key={'test_id': test_id})
    if 'Item' in response:
        return jsonify({"error": "Test instance already exists in DynamoDB"}), 400
    else:
        # Save test_id into the table with create_time = now(), user = "test", active = false
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')  # ISO 8601 format in UTC
        table.put_item(
            Item={
                'test_id': test_id,
                'user': user,
                'active': False,
                'create_time': current_time
            }
        )
    
    # Check if the test_id already exists
    if any(inst["test_id"] == test_id for inst in test_instances):
        return jsonify({"error": "Test instance already exists"}), 400
    
    # Extract other data from the request JSON
   
    bt_symbol = request.json.get("bt_symbol")
    bt_start_date = request.json.get("bt_start_date")
    bt_end_date = request.json.get("bt_end_date")
    bt_time_frame_backward = request.json.get("bt_time_frame_backward")
    bt_investment = request.json.get("bt_investment")
    bt_lot_size = request.json.get("bt_lot_size")
    bt_sl_size = request.json.get("bt_sl_size")
    bt_tp_size = request.json.get("bt_tp_size")
    ft_symbols = request.json.get("ft_symbols")
    ft_investment = request.json.get("ft_investment")
    ft_lot_size = request.json.get("ft_lot_size")
    ft_sl_size = request.json.get("ft_sl_size")
    ft_tp_size = request.json.get("ft_tp_size")
    
    # Create a new test instance with the provided data
    test_instance = full.Test(
        test_id=test_id,
        bt_symbol=bt_symbol,
        bt_start_date=bt_start_date,
        bt_end_date=bt_end_date,
        bt_time_frame_backward=bt_time_frame_backward,
        bt_investment=bt_investment,
        bt_lot_size=bt_lot_size,
        bt_sl_size=bt_sl_size,
        bt_tp_size=bt_tp_size,
        ft_symbols=ft_symbols,
        ft_time_frame_forward=mt5.TIMEFRAME_M5,
        ft_investment=ft_investment,
        ft_lot_size=ft_lot_size,
        ft_sl_size=ft_sl_size,
        ft_tp_size=ft_tp_size
    )
    
    # Add the test_id and test_instance to the array
    test_instances.append({"test_id": test_id, "test_instance": test_instance})

    return jsonify({"message": "Test instance created"})


@app.route("/start_test", methods=["POST"])
def start_test():
    # Extract test_id and user from the request data
    test_id = request.json.get("test_id")
    user = request.json.get("user")  # Assuming user is also sent in the request

    if test_id is None or user is None:
        return jsonify({"error": "Missing test_id or user"}), 400

    # Query DynamoDB to find the item based on test_id
    response = table.get_item(Key={'test_id': test_id})
    if 'Item' not in response:
        return jsonify({"error": "Test instance not found in DynamoDB"}), 404

    item = response['Item']

    # Check if the end_date key exists or if the test is already active
    if 'end_date' in item or (item.get('active') is True):
        return jsonify({"error": "Test cannot be started as it has an end date or is already active"}), 403

    # Find the test instance in the global list by test_id
    test_instance_data = next(
        (inst for inst in test_instances if inst["test_id"] == test_id), None)

    # If the test instance is not found, return an error
    if test_instance_data is None:
        return jsonify({"error": "Test instance not found"}), 400

    # Retrieve the test_instance from the stored data
    test_instance = test_instance_data["test_instance"]

    # Start the test using a function from the 'full' module
    full.start_forward_test_thread(test_instance)  # Uncomment this line if you have the full module

    # Update the item in DynamoDB to set active to True and add the current start_time
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')  # ISO 8601 format in UTC
    update_response = table.update_item(
        Key={'test_id': test_id},
        UpdateExpression='SET #active = :val1, start_time = :val2',
        ExpressionAttributeNames={
            '#active': 'active'  # Use ExpressionAttributeNames to avoid conflicts with reserved words
        },
        ExpressionAttributeValues={
            ':val1': True,
            ':val2': current_time
        }
    )

    # Check if the update was successful
    if update_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        return jsonify({"error": "Failed to update DynamoDB"}), 500

    # Return a success message indicating the test has started
    return jsonify({"message": "Test started and DynamoDB updated"})

@app.route("/stop_test", methods=["POST"])
def stop_test():
    # Extract test_id and user from the request data
    table = dynamodb.Table('test_by_users-dev')
    test_id = request.json.get("test_id")
    if test_id is None:
        return jsonify({"error": "Missing test_id or user"}), 400

    # Query DynamoDB to find the item based on user and test_id
    response = table.get_item(Key={'test_id': test_id})
    if 'Item' not in response:
        return jsonify({"error": "Test instance not found"}), 404

    # Find the test instance in the global list by test_id
    test_instance_data = next(
        (inst for inst in test_instances if inst["test_id"] == test_id), None)
    
    # If the test instance is not found, return an error
    if test_instance_data is None:
        return jsonify({"error": "Test instance not found"}), 400

    # Retrieve the test_instance from the stored data
    test_instance = test_instance_data["test_instance"]

    # Stop the test using a function from the 'full' module
    full.stop_forward_test_thread(test_instance)

    # Update the item in DynamoDB to set active to False and add the current end_time
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')  # ISO 8601 format in UTC
    update_response = table.update_item(
        Key={'test_id': test_id},
        UpdateExpression='SET active = :val1, end_time = :val2',
        ExpressionAttributeValues={
            ':val1': False,
            ':val2': current_time
        }
    )

    # Check if the update was successful
    if update_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        return jsonify({"error": "Failed to update DynamoDB"}), 500

    # Return a success message indicating the test has stopped
    return jsonify({"message": "Test stopped and DynamoDB updated"})

@app.route("/get_test_instances", methods=["GET"])
def get_test_instances():
    table = dynamodb.Table('test_by_users-dev')

        # Perform the scan operation to retrieve all items from the table
    response = table.scan()

    # Extract the items from the response
    test_instances = response.get('Items', [])

    # Paginate if there are more items to scan
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        test_instances.extend(response.get('Items', []))

    # Return the list of test instances as JSON
    return jsonify(test_instances)

@app.route("/backtesting", methods=["POST"])
def backtesting():
    global test_instances
    start_date = datetime(2020,1,1)
    end_date = datetime(2023,6,1)


    test_id = request.json.get("test_id")
    if test_id is None:
        return jsonify({"error": "Missing test_id"}), 400

    test_instance_data = next(
        (inst for inst in test_instances if inst["test_id"] == test_id), None)
    if test_instance_data is None:
        return jsonify({"error": "Test instance not found"}), 400

    # Retrieve the test_instance from the stored data
    test_instance = test_instance_data["test_instance"]
    test_instance.bt_get_data(start_date, end_date)
    test_instance.backtest_supertrend()
    return jsonify([{"roi": test_instance.bt_roi, "entry": "", "exit": ""}])
    # return test_instance.bt_roi
def process_over_all(over_all):
    # Initialize an empty dictionary to hold the processed data
    processed_data = {}

    # Go through each item in the 'over_all' list
    for item in over_all:
        # Get the prefix based on the 'entry' value
        prefix = "entry_" if item["entry"] == 0 else "exit_"

        # Create a new dictionary with the keys prefixed
        new_item = {f"{prefix}{key}": value for key, value in item.items()}

        # Get the position_id
        position_id = item["position_id"]

        # If this position_id is already in the processed_data dictionary, combine the objects
        if position_id in processed_data:
            processed_data[position_id].update(new_item)
        else:
            processed_data[position_id] = new_item

    # Convert the processed_data dictionary to a list of dictionaries
    processed_list = list(processed_data.values())
    # Remove 'exit_magic' and 'exit_symbol' from all dictionaries in the list
    processed_list = [{k: v for k, v in item.items() if k not in ['exit_magic', 'exit_symbol']} for item in processed_list]

    return processed_list
from datetime import datetime, timedelta

@app.route("/get_test_result", methods=["POST"])
def get_test_result():
    global test_instances

    test_id = request.json.get("test_id")
    if test_id is None:
        return jsonify({"error": "Missing test_id"}), 400

    test_instance_data = next(
        (inst for inst in test_instances if inst["test_id"] == test_id), None)
    if test_instance_data is None:
        return jsonify({"error": "Test instance not found"}), 400

    # Retrieve the test_instance from the stored data
    test_instance = test_instance_data["test_instance"]
    test_instance.get_forward_test_result()

    ft_roi = test_instance.ft_roi
    ft_entry = test_instance.ft_entry
    ft_exit = test_instance.ft_exit
    ft_over_all = test_instance.ft_over_all
    ft_profit = test_instance.ft_profit
    ft_start_date = test_instance.ft_start_date
    ft_end_date = test_instance.ft_end_date

    ft_over_all = process_over_all(ft_over_all)
    lowest_exit_profit = min(item.get("exit_profit", 0) for item in ft_over_all)

    # Convert start date to timestamp
    ft_start_date_timestamp = ft_start_date.timestamp()

    # Calculate period
    if ft_end_date is None:
        ft_end_date = datetime.now()
    ft_end_date_timestamp = ft_end_date.timestamp()
    ft_period = ft_end_date_timestamp - ft_start_date_timestamp

    return jsonify(
        [
            {
                "roi": ft_roi,
                "lowest_exit_profit": lowest_exit_profit,
                "profit": ft_profit,
                "start_date": ft_start_date_timestamp,
                "end_date": ft_end_date_timestamp,
                "period": ft_period,
            }
        ]
    )
    # return jsonify([{"roi": roi, "entry": entry, "exit": exit, "over_all":over_all}])
    
@app.route('/remove_test', methods=['POST'])
def remove_test():
    # Get test_id from the request body
    data = request.json
    test_id = data.get('test_id')

    if not test_id:
        return jsonify({'error': 'test_id is required'}), 400

    try:
        # Delete the item from DynamoDB table
        response = table.delete_item(
            Key={
                'test_id': test_id  # Assuming 'test_id' is the partition key
            }
        )
        # Check if the item was actually deleted
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            return jsonify({'message': 'Test removed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to remove test'}), 500

    except ClientError as e:
        # Handle specific DynamoDB errors or general AWS errors
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_tests_by_user', methods=['Post'])
def get_tests_by_user():
    user = request.json.get("user") 

    if not user:
        return jsonify({'error': 'User is required'}), 400

    try:
        # Perform a scan operation with a filter for the user attribute
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('user').eq(user)
        )
        items = response.get('Items', [])
        
        # Handle pagination if the dataset is large
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('user').eq(user),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        return jsonify(items), 200

    except ClientError as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
   app.run(host='0.0.0.0',port=5050)
    # app.run(port=8000)


#    result =  {
#     "test": [
#       {
#         "testName": "SuperTrend",
#         "backTestRoi": test_instance.bt_roi,
#         "forwardTestRoi": test_instance.ft_roi,
#         "data": {
#           "backTestResult": {
#             "roi": "",
#             "period": "",
#             "investment": "",
#             "maxDrawDown": "",
#             "marketReturn": "",
#             "transactions": [
#               {
#                 "tradeNo": "",
#                 "tradeType": "",
#                 "dateTime": "",
#                 "priceUS": ""
#               }
#             ]
#           },
#           "forwardTestResult": {
#             "roi": test_instance.ft_roi,
#             "period": "",
#             "investment": test_instance.ft_investment,
#             "maxDrawDown": "lowest_exit_profit",
#             "marketReturn": ft_roi,
#             "transactions": [
#               {
#                 "tradeNo": "",
#                 "tradeType": "",
#                 "dateTime": "",
#                 "priceUS": ""
#               }
#             ]
#           }
#         }
#       }
#     ]
#   }