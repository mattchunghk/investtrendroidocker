from flask import Flask, request, jsonify
import backend.api.testinvesttrendscheduleroi.src.python.src.matt_supertrend_old as mst

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    result = {
        'Best Parameter Set': "test good"
        }
    

    return jsonify(result)

@app.route('/backtest', methods=['POST'])
def perform_backtest():
    data = request.get_json()
    
    symbol = data.get('symbol', "BTC-USD")
    investment = data.get('investment', 10000000)
    commission = data.get('commission', 0)
    start_date = data.get('start_date', "2023-1-1")
    end_date = data.get('end_date', "2023-10-1")
    interval = data.get('interval', '1d')
    atr = data.get('atr')
    multiplier = data.get('multiplier')

    strategy = mst.Supertrend
    backtest = mst.backtest_supertrend

    fy_df = mst.get_yf_df(symbol, start_date, end_date, interval)

    atr_period, multiplier, ROI = mst.find_optimal_parameter(fy_df, strategy, backtest, investment, commission, atr, multiplier)

    result = {
        'Best Parameter Set': {
            'ATR Period': atr_period,
            'Multiplier': multiplier,
            'ROI': f'{ROI}%'
        }
    }

    return jsonify(result)

import json

def lambda_handler(event, context):
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }



if __name__ == "__main__":
    lambda_handler(None,None)