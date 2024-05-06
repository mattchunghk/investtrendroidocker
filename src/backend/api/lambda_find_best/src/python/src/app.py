
import matt_supertrend as mst




import json

def lambda_handler(event, context):

    data = json.loads(event["body"])
    print('data: ', data)

    symbol = data['symbol']
    investment = data['investment']
    commission = data['commission']
    start_date = data['start_date']
    end_date = data['end_date']
    interval = data['interval']
    lot_size = data['lot_size']
    sl_size = data['sl_size']
    tp_size = data['tp_size']

    atr = data['atr']
    multiplier = data['multiplier']
    
    strategy = mst.Supertrend
    backtest = mst.backtest

    fy_df = mst.get_yf_df(symbol, start_date, end_date, interval)

    atr_period, multiplier, ROI = mst.find_optimal_parameter(fy_df, strategy, backtest, investment, lot_size, sl_size, tp_size,commission,atr,multiplier)

    result = {
            "symbol": symbol,
            'ATR Period': atr_period,
            'Multiplier': multiplier,
            'ROI': ROI
        }
    
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }



if __name__ == "__main__":
    data = {
            "body": {
                "symbol": "BTC-USD",
                "investment": 10000000,
                "commission": 0,
                "start_date": "2023-10-1",
                "end_date": "2023-12-27",
                "interval": "1d",
                "lot_size": 1,
                "sl_size": 5000,
                "tp_size": 5000,
                "atr": 10,
                "multiplier": 5
            }
            }

    print(lambda_handler(data, None))

