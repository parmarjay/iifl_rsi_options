# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 22:03:50 2021

@author: JAY
"""

'''
# TODO:
- Monitor (Show Net positions, total MTM)

- Logging / Create logs
'''

from iifl_broker import IIFL
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import talib as ta
import time
import traceback
import pytz
from datetime import time as t

# TODO: Retry failed requests

# Define parameters
config_file_path = './config.ini'

# Define execution frequency
# 1T = 1 Minute, 3T = 3 Minutes, 5T = 5 Minutes
_frequency = '15T'

# Define candle size. This should be in-line with trading frequency
interval = '15m'

# Define lookback
lookback = 4

# Define threshold
threshold = 60

# Define intraday variable
_is_intraday = False

# Define start and end dates for fetching historical data

tz = pytz.timezone('Asia/Kolkata')

end_date = datetime.now(tz)
end_date = (end_date.replace(second=0, microsecond=0)).strftime('%Y-%m-%d')
start_date = (datetime.now(tz) - timedelta(minutes=5760))  # fetch last 4 days of data from current time
start_date = (start_date.replace(second=0, microsecond=0)).strftime('%Y-%m-%d')

# start_date = '2021-07-02'
# end_date = '2021-07-02'

# Define the last execution time
market_close_time = datetime.today()
market_close_time = market_close_time.replace(hour=15, minute=28, second=0)

# Define the last candle time which needs to be removed from the historical data
last_candle_time = t(15 , 30 , 0)

app = IIFL(config_file_path)

token_authorized, login_id = app.login()

print("Login Successful:", login_id)

scrips = [{'scrip': '39498', 'exchange': 'n', 'exchange_type': 'd', 
           'position': 0, 'net_qty':0, 'name': 'NIFTY 08 Jul 2021 CE 15800.00', 'trade_qty': 75, 
           'market_orders': False, 'hist_download':True}, 
          {'scrip': '39501', 'exchange': 'n', 'exchange_type': 'd', 
           'position': 0, 'net_qty': 0, 'name': 'NIFTY 08 Jul 2021 PE 15800.00', 'trade_qty': 75,
           'market_orders': False, 'hist_download':True}      
          ]

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
    
    print('\nScrip name:', scrip_name)
    
    scrip['current_price'] = app.get_current_price(scrip['scrip'],
                                                   scrip['exchange'].upper(),
                                                   scrip['exchange_type'].upper())
    
    # Variable to check whether we placed an order or not
    order_placed = False
    
    # Define default order side
    order_side = ''
    
    if scrip['hist_download'] == True:
        
        # Fetch historical data
        scrip['hist_data'] = app.get_historical_data(scrip['scrip'], 
                                            scrip['exchange'], 
                                            scrip['exchange_type'],
                                            interval,
                                            start_date,
                                            end_date)
        
        row_to_delete = scrip['hist_data'][scrip['hist_data'].index.time == last_candle_time]
        
        scrip['hist_data'].drop(index=row_to_delete.index, inplace=True)
        
        scrip['hist_download'] = False
    else:
        
        print('The current price for', scrip_name, 'is', 
              round(scrip['current_price'], 2))
            
        new_data = {
            'open': 0,
            'high': 0,
            'low': 0,
            'close': scrip['current_price'],
            'volume': 0
            }
        
        scrip['hist_data'] = scrip['hist_data'].append(new_data, ignore_index=True)
        
        if scrip['market_orders'] == True:
            scrip['current_price'] = 0

    
    # Generate trading signals if historical data is available
    if len(scrip['hist_data']) <= lookback:
        print('Not enough data to compute RSI: ', scrip_name)
    else:
        
        # Compute RSI indicator
        scrip['hist_data']['rsi'] = ta.RSI(scrip['hist_data']['close'], 
                                           timeperiod=lookback)
        
        # Get current and the previous RSI values
        scrip['current_rsi'] = round(scrip['hist_data']['rsi'].iloc[-1], 2)
        scrip['prev_rsi'] = round(scrip['hist_data']['rsi'].iloc[-2], 2)
        
        print(f"For {scrip_name} current rsi - {scrip['current_rsi']}, \
              prev rsi - {scrip['prev_rsi']}")
        
        # Check for short enter condition
        if (scrip['current_rsi'] < threshold) & (scrip['prev_rsi'] > threshold):
            
            # Check if we have an open position. If not, open it.
            if scrip['position'] == 0:
                
                print('Enter short position for scrip: ', scrip_name)
                print('Current price of ', scrip_name, 'is', 
                      round(scrip['current_price'], 2))
                
                order_side = 'sell'
                
                scrip['broker_order_id'], scrip['remote_order_id'], message = app.place_order(scrip['scrip'],
                                                                                     scrip['exchange'],
                                                                                     scrip['exchange_type'], 
                                                                                     price=scrip['current_price'], 
                                                                                     side=order_side,                                   
                                                                                     qty=scrip['trade_qty'], 
                                                                                     mkt_order=scrip['market_orders'], 
                                                                                     is_intraday=_is_intraday,
                                                                                     new_or_modify='P',
                                                                                     exchange_order_id=0)
                
                order_placed = True
                
                print('New entry order placed for scrip:', scrip_name, 
                      'with broker order id', scrip['broker_order_id'], 'at', scrip['current_price'])
                print('Msg from Broker:', message)
                
                # Update the scrip positions
                scrip['position'] = -1
                
        # Check for short exit condition
        elif (scrip['current_rsi'] > threshold) & (scrip['prev_rsi'] < threshold):
            
            # Fetch current net_positions
            num_positions, pos_df = app.net_position()
            
            if num_positions > 0:
                filtered_pos = pos_df[pos_df['ScripCode'] == float(scrip['scrip'])]
                
                if len(filtered_pos) > 0:
                    
                    scrip_pos = filtered_pos['NetQty'].iloc[-1]   
                                              
                    # Check if we have a short position. If yes, close it.
                    # if scrip['position'] == -1:
                    if scrip_pos < 0:
                        
                        # if scrip['market_orders'] == False:
                        #     scrip['current_price'] = app.get_current_price(scrip['scrip'],
                        #                                        scrip['exchange'].upper(),
                        #                                        scrip['exchange_type'].upper())
                        # else:
                        #     scrip['current_price'] = 0
                        
                        print('Exit short position for scrip: ', scrip_name)
                        
                        order_side = 'buy'
                        
                        scrip['broker_order_id'], scrip['remote_order_id'], message = app.place_order(scrip['scrip'], 
                                                                                             scrip['exchange'], 
                                                                                             scrip['exchange_type'], 
                                                                                             price=scrip['current_price'], 
                                                                                             side=order_side,                                
                                                                                             qty=scrip['trade_qty'], 
                                                                                             mkt_order=scrip['market_orders'], 
                                                                                             is_intraday=_is_intraday,
                                                                                             new_or_modify='P',
                                                                                             exchange_order_id=0)
                        
                        order_placed = True
                        
                        print('New exit order placed for scrip:', scrip_name, 
                              'with order id', scrip['broker_order_id'], 'at', scrip['current_price'])
                        print('Msg from Broker:', message)
                        
                        # Update the scrip position
                        scrip['position'] = 0
            else:
                print('No short positions exists for scrip: ', scrip_name)
            
        else:
            print('No change in position for scrip: ', scrip_name)
        
        while order_placed:
            # If order is placed, wait for 3 seconds before checking its status
            time.sleep(5)
            try:
                # Check status
                scrip['order_status'] = app.get_order_status(scrip['remote_order_id'],
                                                             scrip['exchange'],
                                                             scrip['exchange_type'],
                                                             scrip['scrip'])
                
                print('Order Status for', scrip_name, 'is', 
                      scrip['order_status']['Status'], 'and pending qty is', 
                      scrip['order_status']['PendingQty'])
                
                # if isinstance(scrip['order_status'], str):
                #     print('Cannot fetch order status')
                # elif isinstance(scrip['order_status'], dict):
                    
                pending_qty = scrip['order_status']['PendingQty']
                
                # If the order is not executed or partially executed, modify the order
                if pending_qty > 0:
                    scrip['current_price'] = app.get_current_price(scrip['scrip'],
                                                                   scrip['exchange'].upper(),
                                                                   scrip['exchange_type'].upper())
                    
                    # Place modified order
                    scrip['broker_order_id'], scrip['remote_order_id'], message = app.place_order(scrip['scrip'], 
                                                                                         scrip['exchange'], 
                                                                                         scrip['exchange_type'], 
                                                                                         price=scrip['current_price'],
                                                                                         side=order_side,
                                                                                         qty=pending_qty,
                                                                                         mkt_order=scrip['market_orders'],
                                                                                         is_intraday=_is_intraday,
                                                                                         new_or_modify='M',
                                                                                         exchange_order_id=scrip['order_status']['ExchOrderID'])
                    
                    print('Modified order placed for ', scrip_name, 'at', 
                          scrip['current_price'], 'with exchange order id', 
                          scrip['order_status']['ExchOrderID'])
                    print('Msg from Broker:', message)
                
                if pending_qty == 0:
                    order_placed = False
            except:
                order_place= False
        
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

# Define the default time format
tf = '%Y-%m-%d %H:%M:%S'

# Define start and end date and time for algo execution
_start_time = datetime.today()
_end_time = datetime.today()

_start_time = _start_time.replace(hour=9, minute=15, second=0).strftime(tf)
_end_time = _end_time.replace(hour=15, minute=30, second=0).strftime(tf)

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
            break
        
        # Run for the last time before the market closes
        elif datetime.strptime(current_time, tf) == datetime.strptime(market_close_time.strftime(tf), tf):
            print('\n')
            print('='*20)
            print('Running for the last time.')
            print('Executing algorithm:', current_time)
            run_strategy()
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