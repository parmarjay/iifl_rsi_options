# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 22:03:50 2021

@author: JAY
"""

'''
# TODO:
- Create a strategy object
- Connect
- fetch historical data
- Compute RSI
- Check for signals
- Place orders
- Monitor (Show Net positions, total MTM)
- Load scrips

- Logging / Create logs
- Store historical data

'''

from iifl_broker import IIFL
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import talib as ta
import time
import traceback


config_file_path = './config.ini'

app = IIFL(config_file_path)

token_authorized, login_id = app.login()

print("Login Successful:", login_id)

# margin_dict = app.margin()

# print(margin_dict)

# num_positions, pos_df = app.net_position()

# scrip = 35006
# exchange = 'n'
# exchange_type = 'd'
# interval = '1m'
# from_date = '2021-06-21'
# end_date = '2021-06-21'

# if token_authorized:
#     hist_data = app.get_historical_data(scrip, exchange, exchange_type, interval, 
#                         from_date, end_date)
    
#     print(hist_data)
# else:
#     print('Token Not authorized')
    
# TODO: Fetch orderbook, tradebook, placeorder, orderstatus, livefeed

# num_orders, orderbook = app.get_orderbook()

# num_trades, tradebook = app.get_tradebook()

# current_price = app.get_current_price(2885, 'N','C')

###############################################################################
# Define parameters
config_file_path = './config.ini'

# Define execution frequency
# 1T = 1 Minute, 3T = 3 Minutes, 5T = 5 Minutes
_frequency = '1T'

# Define candle size. This should be in-line with trading frequency
interval = '1m'

# Define lookback
lookback = 5

# Define threshold
threshold = 40

# Define start and end dates for fetching historical data
start_date = '2021-06-22'
end_date = '2021-06-22'

app = IIFL(config_file_path)

token_authorized, login_id = app.login()

print("Login Successful:", login_id)

scrips = [{'scrip': '51354', 'exchange': 'n', 'exchange_type': 'd', 
           'position': 0, 'net_qty':0, 'name': '15800 PE', 'trade_qty': 75, 
           'market_orders': False}, 
          {'scrip': '35062', 'exchange': 'n', 'exchange_type': 'd', 
           'position': 0, 'net_qty': 0, 'name': '15900 CE', 'trade_qty': 75,
           'market_orders': False}]
          #   ,
          # {'scrip': '772', 'exchange': 'n', 'exchange_type': 'c', 
          #  'position': 0, 'net_qty': 0, 'name': 'DABUR', 'trade_qty': 1}],
          # {'scrip': '51348', 'exchange': 'n', 'exchange_type': 'd', 
          #  'position': 0, 'net_qty': 0, 'name': '15650 PE', 'trade_qty': 75}]

# Fetch net positions
num_positions, pos_df = app.net_position()

# Update net positions for each scrip
if num_positions > 0:
    try:
        for row in range(0, len(pos_df)):
            
            current_scrip = pos_df.iloc[row]['ScripCode']
            
            for i in range(0, len(scrips)):
                
                current_item = scrips[i]
                
                if current_item['scrip'] == str(current_scrip):
                    if pos_df.iloc[row]['NetQty'] < 0:
                        current_item['position'] = -1
                    elif pos_df.iloc[row]['NetQty'] > 0:
                        current_item['position'] = 1
    except:
        print('Error in iiflb - get_tradebook!\n', traceback.print_exc())

# This method contains the trading logic
def execute_logic(scrip):
    
    # Get the scrip name
    scrip_name = scrip['name']
    
    # Variable to check whether we placed an order or not
    order_placed = False
    
    # Define default order side
    order_side = ''
    
    # Fetch historical data
    scrip['hist_data'] = app.get_historical_data(scrip['scrip'], 
                                        scrip['exchange'], 
                                        scrip['exchange_type'],
                                        interval,
                                        start_date,
                                        end_date)
    
    print('\nScrip name:', scrip_name)
    
    # Generate trading signals if historical data is available
    if len(scrip['hist_data']) <= lookback:
        print('Not enough data to compute RSI: ', scrip_name)
    else:
        
        # Compute RSI indicator
        scrip['hist_data']['rsi'] = ta.RSI(scrip['hist_data']['close'], 
                                           timeperiod=lookback)
        
        # Get current and the previous RSI values
        scrip['current_rsi'] = round(scrip['hist_data']['rsi'][-1], 2)
        scrip['prev_rsi'] = round(scrip['hist_data']['rsi'][-2], 2)
        
        print(f"For {scrip_name} current rsi - {scrip['current_rsi']}, prev rsi - {scrip['prev_rsi']}")
        
        if not scrip['market_orders']:
            scrip['current_price'] = app.get_current_price(scrip['scrip'],
                                                           scrip['exchange'].upper(),
                                                           scrip['exchange_type'].upper())
        else:
            scrip['current_price'] = 0
        
        # Check for short enter condition
        if (scrip['current_rsi'] < threshold) & (scrip['prev_rsi'] > threshold):
            
            # Check if we have an open position. If not, open it.
            if scrip['position'] == 0:
                print('Enter short position for scrip: ', scrip_name)
                
                order_side = 'sell'
                
                scrip['broker_order_id'], scrip['remote_order_id'] = app.place_order(scrip['scrip'],
                                                                                     scrip['exchange'],
                                                                                     scrip['exchange_type'], 
                                                                                     price=scrip['current_price'], 
                                                                                     side=order_side,                                   
                                                                                     qty=scrip['trade_qty'], 
                                                                                     mkt_order=scrip['market_orders'], 
                                                                                     is_intraday=False,
                                                                                     new_or_modify='P',
                                                                                     exchange_order_id=0)
                
                order_placed = True
                
                print('New entry order placed for scrip:', scrip_name, 
                      'with order id', scrip['broker_order_id'])
                
                # Update the scrip positions
                scrip['position'] = -1
                
        # Check for short exit condition
        elif (scrip['current_rsi'] > threshold) & (scrip['prev_rsi'] < threshold):
            
            # Fetch current net_positions
            num_positions, pos_df = app.net_position()
            
            if num_positions > 0:
                scrip_pos = pos_df[pos_df['ScripCode'] == float(scrip['scrip'])]['NetQty'].iloc[-1]   
                                          
                # Check if we have a short position. If yes, close it.
                # if scrip['position'] == -1:
                if scrip_pos < 0:
                    print('Exit short position for scrip: ', scrip_name)
                    
                    order_side = 'buy'
                    
                    scrip['broker_order_id'], scrip['remote_order_id'] = app.place_order(scrip['scrip'], 
                                                                                         scrip['exchange'], 
                                                                                         scrip['exchange_type'], 
                                                                                         price=scrip['current_price'], 
                                                                                         side=order_side,                                
                                                                                         qty=scrip['trade_qty'], 
                                                                                         mkt_order=scrip['market_orders'], 
                                                                                         is_intraday=False,
                                                                                         new_or_modify='P',
                                                                                         exchange_order_id=0)
                    
                    order_placed = True
                    
                    print('New exit order placed for scrip:', scrip_name, 
                          'with order id', scrip['broker_order_id'])
                    
                    # Update the scrip position
                    scrip['position'] = 0
            else:
                print('No short positions exists for scrip: ', scrip_name)
            
        else:
            print('No change in position for scrip: ', scrip_name)
        
        while order_placed:
            # If order is placed, wait for 3 seconds before checking its status
            time.sleep(3)
            
            # Check status
            scrip['order_status'] = app.get_order_status(scrip['remote_order_id'],
                                                         scrip['exchange'],
                                                         scrip['exchange_type'],
                                                         scrip['scrip'])
            
            if isinstance(scrip['order_status'], str):
                print('Cannot fetch order status')
            elif isinstance(scrip['order_status'], dict):
                
                pending_qty = scrip['order_status']['pending_qty']
                
                # If the order is not executed or partially executed, modify the order
                if pending_qty > 0:
                    scrip['current_price'] = app.get_current_price(scrip['scrip'],
                                                                   scrip['exchange'].upper(),
                                                                   scrip['exchange_type'].upper())
                    
                    # Place modified order
                    scrip['broker_order_id'], scrip['remote_order_id'] = app.place_order(scrip['scrip'], 
                                                                                         scrip['exchange'], 
                                                                                         scrip['exchange_type'], 
                                                                                         price=scrip['current_price'],
                                                                                         side=order_side,
                                                                                         qty=pending_qty,
                                                                                         mkt_order=scrip['market_orders'],
                                                                                         is_intraday=False,
                                                                                         new_or_modify='M',
                                                                                         exchange_order_id=scrip['order_status']['ExchOrderID'])
                    
                    print('Modified order placed for scrip: ', scrip_name)
                elif pending_qty == 0:
                    order_placed = False
                
        
    print('Finished execution for scrip:', scrip_name)

# This function will be called every time a strategy needs to be run.
# It will call execute_logic function for each scrip in a separate thread.
def run_strategy():
    
    with ThreadPoolExecutor(len(scrips)) as executor:
        
        # executor.map(execute_logic, scrips)
        
        for i in range(0, len(scrips)):
            fut = executor.submit(execute_logic, scrips[i])
            print(fut.result())
            time.sleep(0.5)
            
def show_info():
    
    num_positions, pos_df = app.net_position()
    
    if num_positions > 0:
        print(pos_df[['ScripName', 'BookedPL', 'MtoM', 'NetQty']])
    
    margin = app.margin()
    print('Available Margin:', margin['AvailableMargin'])

###############################################################################

# The following code executes things iteratively

# Define start and end date and time for algo execution
_start_time = '2021-06-22 09:15:00'
_end_time = '2021-06-22 15:30:00'

# Define the default time format
tf = '%Y-%m-%d %H:%M:%S'

# Generate timestamps
timestamps = pd.date_range(start=_start_time, 
                           end=_end_time, 
                           freq=_frequency).strftime(tf)

#  Run infinite loop that iterates over the timestamps generated above
try:
    while True:
        
        # Get current time
        current_time = datetime.now().strftime(tf)
        
        # If the current time is less than the strategy start time, then wait
        if datetime.strptime(current_time, tf) < datetime.strptime(_start_time, 
                                                                   tf):
            print('Wait', current_time)
            time.sleep(1)
            continue
        
        # If the current time is within strategy run time, execute the 
        # algorithm
        elif current_time in timestamps:
            print('\n')
            print('='*20)
            print('Executing algorithm:', current_time)
            run_strategy()
            
        # If the current time is greater than the strategy run time, 
        # then exit the execution
        elif datetime.strptime(current_time, tf) > datetime.strptime(_end_time, 
                                                                     tf):
            print('Finish. Disconnecting the application:', current_time)
            app.disconnect()
            break
        
        elif datetime.strptime(current_time, tf).minute % 2 == 0:
            # Show current positions, MTM and Margin
            pass
        
        #  print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        time.sleep(1)
        
except:
    print('Error occurred in execution.\n', traceback.print_exc())
finally:
    print('App disconnected.')