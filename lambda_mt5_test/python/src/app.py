from mt5linux import MetaTrader5
from datetime import datetime
import os
from os.path import join, dirname
import json
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = join(dirname(__file__), '.env')
print('dotenv_path: ', dotenv_path)
load_dotenv(dotenv_path)

mt5 = MetaTrader5(
    # host = 'localhost',
    host = '18.141.245.200',
    port = 18812      
)  

path = "/home/ubuntu/.wine/drive_c/Program Files/Pepperstone MetaTrader 5/terminal64.exe"
# path = "/Users/mattchung/.wine/drive_c/Program Files/Pepperstone MetaTrader 5/terminal64.exe"
server = 'Pepperstone-Demo'
# server = 'VantageInternational-Demo'
# mt5_username = os.getenv('mt5_vantage_demo_2_username')
# password = os.getenv('mt5_vantage_demo_2_password')
mt5_username = os.getenv('mt5_pepperstone_username')
password = os.getenv('mt5_pepperstone_password')

deviation = 10
# start_date = datetim
# def start_mt5(username, password, server, path):
def start_mt5():
    # Ensure that all variables are the correct type
    uname = int(mt5_username)  # Username must be an int
    pword = str(password)  # Password must be a string
    trading_server = str(server)  # Server must be a string
    filepath = str(path)  # Filepath must be a string

    # Attempt to start MT5
    if mt5.initialize(login=uname, password=pword, server=trading_server, path=filepath):
        # Login to MT5
        if mt5.login(login=uname, password=pword, server=trading_server):
            return True
        else:
            print("Login Fail")
            # quit()
            return PermissionError
    else:
        print("MT5 Initialization Failed")
        # quit()
        return ConnectionAbortedError

def lambda_handler(event, context):
    print('event: ', event)
    
    
    start_mt5()
    order = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": event["symbol"],
                "volume": float(event["volume"]),
                "type": mt5.ORDER_TYPE_BUY,
                "price": float(event["price"]),
                "sl": float(event["sl"]),
                "tp": float(event["tp"]),
                "deviation": 10,
                "magic": 234000,
                "comment": event["comment"],
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
    result = mt5.order_send(order)
    print('result: ', result.retcode)
    # response = ""
    # Check the execution result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("order_send failed, retcode =", result.retcode)
        # Request the result as a dictionary and display it
        result_dict = result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field, result_dict[field]))
        print("   last_error={}".format(mt5.last_error()))
    else:
        print("Order executed successfully, ticket =", result.order)

    serialized_result = json.dumps(f'result: {result.comment}')
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': serialized_result  # This is now a JSON string of the sorted results
    }
