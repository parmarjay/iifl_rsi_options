# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 22:15:04 2021

@author: JAY
"""

import configparser
import json
import traceback
import requests as rq
import pandas as pd
from iifl_base_objects import Base_Objects
from exceptions import CustomError
from datetime import timedelta, datetime

class IIFL():
    
    def __init__(self, file_path):
        
        self.set_credentials(file_path)
        self.validate_credentials()
        
        self.order_id = 0
        
        self.bo = Base_Objects(self.creds)
        
    def set_credentials(self, file_path):
        
        try:
            config = configparser.ConfigParser()
            config.read(file_path)
            
            self.creds = {}
            
            for section in config.sections():
                for key in config[section]:
                    
                    if key == 'app_name':
                        self.app_name = config[section][key]
                    elif key == 'app_ver':
                        self.app_ver = config[section][key]
                    elif key == 'app_key':
                        self.app_key = config[section][key]
                    elif key == 'app_user_id':
                        self.app_user_id = config[section][key]
                    elif key == 'app_password':
                        self.app_password = config[section][key]
                    elif key == 'os_name':
                        self.os_name = config[section][key]
                    elif key == 'oas_key':
                        self.oas_key = config[section][key]
                    elif key == 'encrypted_client_code':
                        self.encrypted_client_code = config[section][key]
                    elif key == 'encrypted_client_password':
                        self.encrypted_client_password = config[section][key]
                    elif key == 'encrypted_2fa':
                        self.encrypted_2fa = config[section][key]
                    elif key == 'client_code':
                        self.client_code = config[section][key]
                        
                    self.creds[key] = config[section][key]
            
        except:
            print('Error in reading config file!\n', traceback.print_exc())
    
    def validate_credentials(self):
        
        msg = ''
        
        if self.app_name == '':
            msg = 'App Name cannot be empty.'
        if self.app_ver == '':
            msg = 'App Version cannot be empty.'
        if self.app_key == '':
            msg = 'App Key cannot be empty.'
        if self.app_user_id == '':
            msg = 'App User Id cannot be empty.'
        if self.app_password == '':
            msg = 'App Password cannot be empty.'
        if self.os_name == '':
            msg = 'OS name cannot be empty.'
        if self.oas_key == '':
            msg = 'OAS key cannot be empty.'
        if self.encrypted_client_code == '':
            msg = 'Encrypted Client Code cannot be empty.'
        if self.encrypted_client_password == '':
            msg = 'Encrypted Client Password cannot be empty.'
        if self.encrypted_2fa == '':
            msg = 'Encrypted 2fa cannot be empty.'
        if self.client_code == '':
            msg = 'Client code cannot be empty.'
        
        if msg != '':
            msg = msg + ' Make sure all fields are mentioned in config file.'
            raise CustomError('CustomError - iifl_broker - validate_credentials:', 
                              msg)
            
    def login(self):
        
        try:
            url, headers, l_payload = self.bo.get_request_data('login')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - login: ' + msg)
            elif l_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - login: ' + msg)
            
            login_res = rq.post(url, headers=headers, 
                                data=json.dumps(l_payload),
                                timeout=5)
            
            parsed_res_text = json.loads(login_res.text)
            
            if login_res.ok & parsed_res_text['body']['Success'] == 0:
                
                self.cookies = login_res.cookies
                self.jwt_token = parsed_res_text['body']['Token']
                
                login_res.close()
                
                is_token_authorized = self.validate_token()
                
                if is_token_authorized:
                    return True, parsed_res_text['body']['ClientName']
                else:
                    return False, parsed_res_text['body']['ClientName']
                
            else:
                sc = login_res.status_code
                login_res.close()
                msg = 'Issue in login. Status code: ' + str(sc)
                print(msg, 'Retrying again.')
                self.login()
                # raise CustomError('CustomError - iiflb - login: ' + msg)
            
        except:
            print('Error in iiflb - login!\n', traceback.print_exc())
            
    def validate_token(self):
        
        try:
            url, headers, vt_payload = self.bo.get_request_data('validate_token')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - validate_token: ' + 
                                  msg)
            else:
                
                vt_payload['JwtCode'] = self.jwt_token
                
                res = rq.post(url, headers=headers, 
                              data=json.dumps(vt_payload), 
                              cookies=self.cookies,
                              timeout=5)
                
                parsed_res = json.loads(res.text)
                
                if res.ok:
                    res.close()
                    if parsed_res['body']['Status'] == 0:
                        return True
                    else:
                        return False
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot validate token. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.validate_token()
            
        except:
            print('Error in ifflb - validate_token.\n', traceback.print_exc())

    def margin(self):
        
        try:
            url, headers, m_payload = self.bo.get_request_data('margin')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - margin: ' 
                                  + msg)
                
            elif m_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - margin: ' 
                                  + msg)
            else:
                res = rq.post(url, headers=headers,
                              data=json.dumps(m_payload),
                              cookies=self.cookies,
                              timeout=5)
    
                parsed_res = json.loads(res.text)
            
                if res.ok & parsed_res['body']['Status'] == 0:  
                    res.close()
                    return parsed_res['body']['EquityMargin'][0]
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch margin. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.margin()
                    # raise CustomError('CustomError - iiflb - margin: ' + msg)
        
        except:
            print('Error in iiflb - margin!\n', traceback.print_exc())
            
    def net_position(self):
        
        try:
            url, headers, np_payload = self.bo.get_request_data('net_positions')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - net_positions: ' 
                                  + msg)
            elif np_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - net_positions: ' 
                                  + msg)
            else:
                res = rq.post(url, headers=headers,
                              data=json.dumps(np_payload),
                              cookies=self.cookies,
                              timeout=5)
                
                parsed_res = json.loads(res.text)
                
                if res.ok:
                    res.close()
                    positions = parsed_res['body']['NetPositionDetail']
                    
                    if len(positions) == 0:
                        return 0, pd.DataFrame()
                    else:
                        pos_df = pd.DataFrame()
            
                        for position in positions:
                            pos_df = pos_df.append(position, ignore_index=True)
                        
                        return len(positions), pos_df
                    
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch net positions. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.net_position()
                    # raise CustomError('CustomError - iiflb - net_positions: '  + msg)
            
        except:
            print('Error in iiflb - net_positions!\n', traceback.print_exc())
            
    def net_wise_net_positions(self):
        
        try:
            url, headers, nwnp_payload = self.bo.get_request_data('net_wise_net_positions')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - net_wise_net_positions: '
                                  + msg)
            elif nwnp_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - net_wise_net_positions: '
                                  + msg)
            else:
                res = rq.post(url, headers=headers,
                              data=json.dumps(nwnp_payload),
                              cookies=self.cookies,
                              timeout=5)
                
                parsed_res = json.loads(res.text)
                
                if res.ok:
                    res.close()
                    net_wise_positions = parsed_res['body']['NetPositionDetail']
                    
                    if len(net_wise_positions) == 0:
                        return 0, pd.DataFrame()
                    else:
                        net_wise_pos_df = pd.DataFrame()
                        
                        for position in net_wise_positions:
                            net_wise_pos_df = net_wise_pos_df.append(position, ignore_index=True)
                            
                        return len(net_wise_positions), net_wise_pos_df
                    
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch net positions. Status code: ' + str(sc)
                    print(msg, 'Retryting again.')
                    self.net_wise_net_positions()
                    
        except:
            print('Error in iiflb - net_wise_net_positions!\n', traceback.print_exc())
    
    def get_historical_data(self, scrip, exchange, exchange_type, 
                            interval, from_date, end_date):
        
        if exchange not in ['n', 'b', 'm']:
            msg = 'Invalid exchange provided. Permissible values are \
            "n" for NSE, "b" for BSE and "m" for MCX.'
            raise CustomError('CustomError - iiflb - get_historical_data: ' 
                              + msg)
            
        if exchange_type not in ['c', 'd', 'u', 'x', 'y']:
            msg = 'Invalid exchange type provided. Permissible values are \
            "c", "d", "u", "x", "y".'
            raise CustomError('CustomError - iiflb - get_historical_data: ' 
                              + msg)
            
        if interval not in ['1m', '5m', '10m', '15m', '30m', '60m', '1d']:
            msg = 'Invalid bar interval provided. Permissible values are \
            "1m", "5m", "10m", "15m", "30m", "60m", "1d".'
            raise CustomError('CustomError - iiflb - get_historical_data: ' 
                              + msg)
            
        try:
            url, headers, hd_payload = self.bo.get_request_data('historical')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - get_historical_data: ' 
                                  + msg)
            
            url = url + '/' + exchange + '/' + exchange_type + '/' + \
                str(scrip) + '/' + interval
            
            headers['x-auth-token'] = self.jwt_token
            headers['x-clientcode'] = self.client_code
            
            data = {
                'from': from_date,
                'end': end_date
                }
            
            res = rq.get(url, params=data, headers=headers, 
                         cookies=self.cookies,
                         timeout=10)
            
            parsed_res = json.loads(res.text)
            
            if res.ok:
                res.close()
                if parsed_res['status'] == 'success':
                    
                    candles = parsed_res['data']['candles']
                    
                    candles_df = pd.DataFrame(columns=['timestamp', 'open', 
                                                       'high', 'low', 'close', 
                                                       'volume'])
                    
                    new_data = {}
                    
                    for candle in candles:                        
                        new_data['timestamp'] = candle[0]
                        new_data['open'] = candle[1]
                        new_data['high'] = candle[2]
                        new_data['low'] = candle[3]
                        new_data['close'] = candle[4]
                        new_data['volume'] = candle[5]
                        
                        candles_df = candles_df.append(new_data, 
                                                       ignore_index=True)
                        
                    candles_df.set_index('timestamp', inplace=True)
                    candles_df.index = pd.to_datetime(candles_df.index)
                    
                    return candles_df
                    
                else:
                    msg = 'Error in fetching historical data. ' 
                    + parsed_res['status']
                    raise CustomError('CustomError - iiflb - get_historical_data: ' 
                                      + msg)
            else:
                sc = res.status_code
                res.close()
                msg = 'Cannot fetch historical data. Status code: ' + str(sc)
                print(msg, 'Retrying again.')
                self.get_historical_data(scrip, exchange, exchange_type, 
                            interval, from_date, end_date)
                # raise CustomError('CustomError - iiflb - get_historical_data: ' + msg)
        except:
            print('Error in iiflb - get_historical_data!\n', 
                  traceback.print_exc())
            
    def get_orderbook(self):
        
        try:
            
            url, headers, ob_payload = self.bo.get_request_data('orderbook')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - get_orderbook: ' 
                                  + msg)
            elif ob_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - get_orderbook: ' 
                                  + msg)
            else:
                
                res = rq.post(url, headers=headers,
                              data=json.dumps(ob_payload),
                              cookies=self.cookies,
                              timeout=5)
                
                parsed_res = json.loads(res.text)
                
                orders = parsed_res['body']['OrderBookDetail']
                
                if res.ok:
                    res.close()
                    if len(orders) == 0:
                        return 0, pd.DataFrame()
                    else:
                        orders_df = pd.DataFrame()
                        
                        for order in orders:
                            orders_df = orders_df.append(order, 
                                                         ignore_index=True)
                            
                        return len(orders), orders_df
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch orderbook. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.get_orderbook()
                    # raise CustomError('CustomError - iiflb - get_orderbook: ' + msg)
            
        except:
            print('Error in iiflb - get_orderbook!\n', traceback.print_exc())
            
    def get_tradebook(self):
        
        try:
            
            url, headers, tb_payload = self.bo.get_request_data('tradebook')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - get_tradebook: ' 
                                  + msg)
            elif tb_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - get_tradebook: ' 
                                  + msg)
            else:
                
                res = rq.post(url, headers=headers,
                              data=json.dumps(tb_payload),
                              cookies=self.cookies,
                              timeout=5)
                
                print(json.loads(res.text))
                
                parsed_res = json.loads(res.text)
                
                trades = parsed_res['body']['TradeBookDetail']
                
                if res.ok:
                    res.close()
                    if len(trades) == 0:
                        return 0, pd.DataFrame()
                    else:
                        trades_df = pd.DataFrame()
                        
                        for trade in trades:
                            trades_df = trades_df.append(trade, 
                                                         ignore_index=False)
                            
                        return len(trades), trades_df
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch tradebook. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.get_tradebook()
                    # raise CustomError('CustomError - iiflb - get_tradebook: ' + msg)
            
        except:
            print('Error in iiflb - get_tradebook!\n', traceback.print_exc())
            
    def get_order_id(self):
        
        # Increment request id with 1 every time the function is called
        self.order_id += 1
        print('Request Id: {}'.format(self.order_id))
        return self.order_id
    
    def get_order_status(self, remote_order_id, exchange, exchange_type, scrip_code):
        
        if remote_order_id == '':
            msg = 'Order id cannot be blank.'
            raise CustomError('CustomError - iiflb - get_order_status: ' + msg)
        if exchange == '':
            msg = 'Exchange cannot be blank.'
            raise CustomError('CustomError - iiflb - get_order_status: ' + msg)
        if exchange_type == '':
            msg = 'Exchange type cannot be blank.'
            raise CustomError('CustomError - iiflb - get_order_status: ' + msg)
        if scrip_code == None or scrip_code == '':
            msg = 'Scrip code cannot be blank.'
            raise CustomError('CustomError - iiflb - get_order_status: ' + msg)
            
        try:
            
            url, headers, ords_payload = self.bo.get_request_data('order_status')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - get_order_status: ' 
                                  + msg)
                
            elif ords_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - get_order_status: ' 
                                  + msg)
            else:
                order_parameters = {
                    'Exch': str(exchange).upper(),
                    'ExchType': str(exchange_type).upper(),
                    'ScripCode': int(scrip_code),
                    'RemoteOrderID': str(remote_order_id)}
                
                ords_payload['body']['OrdStatusReqList'] = [order_parameters]
                
                res = rq.post(url, headers=headers,
                              data=json.dumps(ords_payload),
                              cookies=self.cookies)
                
                parsed_res = json.loads(res.text)
                
                # print('Order Status Payload.\n', json.dumps(ords_payload))
                
                # print(parsed_res)
                
                if res.ok:
                    if parsed_res['body']['Status'] == 0:
                        
                        return parsed_res['body']['OrdStatusResLst'][-1]
                    
                    else:
                        print('Order Status Response\n')
                        print(parsed_res)
                        return "Cannot fetch order status"
                    
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch order status. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.get_order_status(remote_order_id, exchange, exchange_type, scrip_code)
                    # raise CustomError('CustomError - iiflb - get_order_status: ' + msg)
        
        except:
            print('Error in ifflb - get_order_status!\n', traceback.print_exc())
            
    def get_current_price(self, scrip, exchange, exchange_type):
        
        if scrip == '' or scrip == None:
            msg = 'Scrip cannot be blank.'
            raise CustomError('CustomError - iiflb - get_current_price: ' + msg)
            
        try:
            
            url, headers, cp_payload = self.bo.get_request_data('current_price')
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - get_current_price: ' 
                                  + msg)
                
            elif cp_payload['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - get_current_price: ' 
                                  + msg)
            else:
                current_timestamp = str(int(datetime.now().timestamp()))
                
                cp_payload['body']['Count'] = 1 # Number of scrips
                cp_payload['body']['MarketFeedData'] = [{'Exch':exchange,
                                                      'ExchType':exchange_type,
                                                      'ScripCode':scrip}]
                cp_payload['body']['ClientLoginType'] = '0'
                cp_payload['body']['LastRequestTime'] = '/Date('+ current_timestamp + ')/'
                cp_payload['body']['RefreshRate'] = 'H' # Cache refresh rate
                
                res = rq.post(url, headers=headers,
                              data=json.dumps(cp_payload),
                              cookies=self.cookies,
                              timeout=5)
                
                parsed_res = json.loads(res.text)
                
                # print(parsed_res)
                
                if res.ok:
                    if parsed_res['body']['Status'] == 0:
                        return parsed_res['body']['Data'][-1]['LastRate']
                    else:
                        print(parsed_res)
                        return -1
                    
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot fetch live price. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.get_current_price(scrip, exchange, exchange_type)
                    # raise CustomError('CustomError - iiflb - get_current_price: ' + msg)
            
        except:
            print('Error in ifflb - get_current_price!\n', traceback.print_exc())
    
    def place_order(self, scrip, exchange, exchange_type, price, side, qty, 
                    mkt_order, is_intraday, new_or_modify, exchange_order_id):
        
        if scrip == '':
            msg = 'Scrip code cannot be empty.'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        if exchange not in ['n', 'b', 'm']:
            msg = 'Invalid exchange provided. Permissible values are \
            "n" for NSE, "b" for BSE and "m" for MCX.'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        if exchange_type not in ['c', 'd', 'u', 'x', 'y']:
            msg = 'Invalid exchange type provided. Permissible values are \
            "c", "d", "u", "x", "y".'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        if mkt_order not in [True, False]:
            msg = 'Invalid value provided for mkt_order parameter. \
                Permissible values are True or False.'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        if is_intraday not in [True, False]:
            msg = 'Invalid value provided for is_intraday parameter. \
                Permissible values are True or False.'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        if mkt_order != True:
            if price == '':
                msg = 'Price cannot be empty for limit orders.'
                raise CustomError('CustomError - iiflb - place_order: ' + msg)
                
        if side not in ['buy', 'sell']:
            msg = 'Invalid order side provided. Permissible values are \
                "buy" or "sell".'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        if new_or_modify not in ['P', 'C', 'M']:
            msg = 'Invalid value provided for new or modify. Permissible values are \
                "P", "C", or "M".'
            raise CustomError('CustomError - iiflb - place_order: ' + msg)
            
        try:
            
            url, headers, po_payload = self.bo.get_request_data('place_order')
            
            current_timestamp = str(int(datetime.now().timestamp()))
            tomorrows_date = str(int((datetime.today() + timedelta(1)).timestamp()))
            
            custom_order_id = self.get_order_id()
            
            po_payload['_ReqData']['body']['Exchange'] = exchange.upper()
            po_payload['_ReqData']['body']['ExchangeType'] = exchange_type.upper()
            po_payload['_ReqData']['body']['Price'] = float(price)
            po_payload['_ReqData']['body']['OrderID'] = custom_order_id
            po_payload['_ReqData']['body']['OrderType'] = side.upper()
            po_payload['_ReqData']['body']['Qty'] = int(qty)
            po_payload['_ReqData']['body']['OrderDateTime'] = '/Date('+ current_timestamp + ')/'
            po_payload['_ReqData']['body']['ValidTillDate'] = '/Date('+ tomorrows_date + ')/'
            po_payload['_ReqData']['body']['ScripCode'] = int(scrip)
            po_payload['_ReqData']['body']['AtMarket'] = mkt_order
            po_payload['_ReqData']['body']['RemoteOrderID'] = custom_order_id
            po_payload['_ReqData']['body']['IsIntraday'] = is_intraday
            po_payload['_ReqData']['body']['OrderFor'] = new_or_modify.upper()
            po_payload['_ReqData']['body']['ExchOrderID'] = str(exchange_order_id)
            
            if url == '':
                msg = 'Requesting URL cannot be empty.'
                raise CustomError('CustomError - iiflb - place_order: ' 
                                  + msg)
                
            elif po_payload['_ReqData']['head']['requestCode'] == self.bo.default_rc:
                msg = 'Default request code received.'
                raise CustomError('CustomError - iiflb - place_order: ' 
                                  + msg)
            else:
                res = rq.post(url, headers=headers,
                              data=json.dumps(po_payload),
                              cookies=self.cookies,
                              timeout=5)
                
                parsed_res = json.loads(res.text)
                
                if res.ok:
                    res.close()
                    if parsed_res['body']['Status'] == 0:
                        broker_order_id = parsed_res['body']['BrokerOrderID']
                        remote_order_id = custom_order_id
                        message = parsed_res['body']['Message']
                        return broker_order_id, remote_order_id, message
                    else:
                        print('From place_order function!')
                        print(parsed_res)
                        msg = 'Order is not placed.'
                        raise CustomError('CustomError - iiflb - place_order: ' 
                                          + msg)
                else:
                    sc = res.status_code
                    res.close()
                    msg = 'Cannot place order. Status code: ' + str(sc)
                    print(msg, 'Retrying again.')
                    self.place_order(scrip, exchange, exchange_type, price, side, qty, 
                    mkt_order, is_intraday, new_or_modify, exchange_order_id)
                    
                    # raise CustomError('CustomError - iiflb - place_order: ' + msg)
        except:
            print('Error in ifflb - place_order!\n', traceback.print_exc())
            