# -*- coding: utf-8 -*-
"""
Created on Fri Aug 20 10:26:15 2021

@author: JAY
"""

from iifl_broker import IIFL
import pandas as pd
import time
import threading


# Define parameters
config_file_path = './config.ini'

app = IIFL(config_file_path)

token_authorized, login_id = app.login()

print("Login Successful:", login_id)

market_orders = False
_is_intraday = False


def close_position(scrip_name, scrip_code, net_qty, exchange, exchange_type):
    
    if net_qty < 0:
        order_side = 'buy'
    elif net_qty > 0:
        order_side = 'sell'
        
    if market_orders:
        current_price = 0
    else:
        current_price = app.get_current_price(scrip_code, 
                                              exchange, 
                                              exchange_type)
        
    # Place new order
    broker_order_id, remote_order_id, message = app.place_order(scrip_code,
                                                                exchange,
                                                                exchange_type, 
                                                                price=current_price, 
                                                                side=order_side,                                   
                                                                qty=abs(net_qty), 
                                                                mkt_order=market_orders, 
                                                                is_intraday=_is_intraday,
                                                                new_or_modify='P',
                                                                exchange_order_id=0)
        
    print('New exit order placed for scrip:', scrip_name, 
          'with order id', broker_order_id, 'at', current_price)
    print('Msg from Broker:', message)
        
    order_placed = True
        
    while order_placed:
        
        time.sleep(5)
        
        try:
            order_status = app.get_order_status(remote_order_id,
                                                exchange,
                                                exchange_type,
                                                scrip_code)
            
            print('Order Status for', scrip_name, 'is', 
                  order_status['Status'], 'and pending qty is', 
                  order_status['PendingQty'])
            
            pending_qty = order_status['PendingQty']
            
            if pending_qty > 0:
                current_price = app.get_current_price(scrip_code,
                                                      exchange,
                                                      exchange_type)
                
                # Place modified order
                broker_order_id, remote_order_id, message = app.place_order(scrip_code,
                                                                            exchange,
                                                                            exchange_type, 
                                                                            price=current_price,
                                                                            side=order_side,
                                                                            qty=pending_qty,
                                                                            mkt_order=market_orders,
                                                                            is_intraday=_is_intraday,
                                                                            new_or_modify='M',
                                                                            exchange_order_id=order_status['ExchOrderID'])
                
                print('Modified order placed for ', scrip_name, 'at', 
                      current_price, 'with exchange order id', 
                      order_status['ExchOrderID'])
                print('Msg from Broker:', message)
                
            if pending_qty == 0:
                order_placed = False
            
        except:
            order_place= False
            
    if order_place == False:
        print('Finished execution for scrip:', scrip_name)


# Fetch net positions
num_positions, pos_df = app.net_wise_net_positions()

if num_positions > 0:
    
    print('Total', int(num_positions), 'existing positions found.')
    
    threads = list()
    
    for row in range(len(pos_df)):
        
        scrip_name = pos_df.iloc[row]['ScripName']
        scrip_code = int(pos_df.iloc[row]['ScripCode'])
        net_qty = int(pos_df.iloc[row]['NetQty'])
        exchange = pos_df.iloc[row]['Exch']
        exchange_type = pos_df.iloc[row]['ExchType']
        
        print('Scrip Code:', scrip_code, 'Net Qty:', net_qty)
        
        x = threading.Thread(target=close_position, args=(scrip_name,
                                                      scrip_code,
                                                      net_qty,
                                                      exchange,
                                                      exchange_type))
        threads.append(x)
        x.start()
        
    for index, thread in enumerate(threads):
        thread.join()
    
    print('All positions closed!')
        
        
else:
    print('No existing positions found.')    