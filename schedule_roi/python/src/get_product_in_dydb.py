import boto3
from botocore.exceptions import ClientError
import os
# from dotenv import load_dotenv
# # Load environment variables from .env file
# load_dotenv()

# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# region_name = os.getenv('AWS_REGION')

# dynamodb = boto3.resource('dynamodb', 
#                           aws_access_key_id=aws_access_key_id, 
#                           aws_secret_access_key=aws_secret_access_key, 
#                           region_name=region_name)

# table = dynamodb.Table('investment_products-dev')

def get_items_from_dynamodb(table):
    response = table.scan()
    data = response['Items']

    # Retrieve more results if there are any
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    symbols_yf_list = [item['symbol'] for item in data]
    Name_yf_list = [item['name'] for item in data]

    return symbols_yf_list, Name_yf_list

# symbols, names = get_items_from_dynamodb(table)


# def get_all_data_from_dynamo():
    
#     table = dynamodb.Table('investment_products-dev')

#     try:
#         response = table.scan()
#     except ClientError as e:
#         print(e.response['Error']['Message'])
#     else:
#         items = response['Items']
#         return items

# data = get_all_data_from_dynamo()
# print(len(data))
# # for item in data:
# #     print(item)