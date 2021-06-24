# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 22:01:31 2021

@author: JAY
"""

class Base_Objects():
    
    # Define base url
    base_url = 'https://dataservice.iifl.in/openapi/prod/'
    
    # Define endpoints
    login_endpoint = 'LoginRequest'
    net_positions_endpoint = 'NetPosition'
    orderbook_endpoint = 'OrderBookV2'
    tradebook_endpoint = 'TradeBook'
    margin_endpoint = 'Margin'
    hist_data_endpoint = 'historical'
    token_val_endpoint = 'JWTOpenApiValidation'
    order_status_endpoint = 'OrderStatus'
    place_order_endpoint = 'OrderRequest'
    market_feed_endpoint = 'MarketFeed'
    
    # Define request codes
    default_rc = 'default'
    login_req_code = 'IIFLMarRQLoginRequestV2'
    net_positions_req_code = 'IIFLMarRQNetPositionV4'
    orderbook_req_code = 'IIFLMarRQOrdBkV2'
    tradebook_req_code = 'IIFLMarRQTrdBkV1'
    margin_req_code = 'IIFLMarRQMarginV3'
    order_status_req_code = 'IIFLMarRQOrdStatus'
    place_order_req_code = 'IIFLMarRQOrdReq'
    market_feed_req_code = 'IIFLMarRQMarketFeed'
    
    
    
    def __init__(self, cred_dict):
        
        self.cred_dict = cred_dict
        self.cred_dict['app_source'] = 3157
        
        self.headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': cred_dict['oas_key']
            }
        
        self.payload = {
            'head': {
                'appName': cred_dict['app_name'],
                'appVer': cred_dict['app_ver'],
                'key': cred_dict['app_key'],
                'osName': cred_dict['os_name'],
                'requestCode': self.default_rc,
                'userId': cred_dict['app_user_id'],
                'password': cred_dict['app_password']
                },
            'body': {
                'ClientCode': cred_dict['client_code']
                }
            }


    def get_request_data(self, req_type):
        
        url = ''
        
        if req_type == 'login':
            
            url = self.base_url + self.login_endpoint

            payload = {
                'head': {
                    'appName': self.cred_dict['app_name'],
                    'appVer': self.cred_dict['app_ver'],
                    'key': self.cred_dict['app_key'],
                    'osName': self.cred_dict['os_name'],
                    'requestCode': self.login_req_code,
                    'userId': self.cred_dict['app_user_id'],
                    'password': self.cred_dict['app_password']
                    },
                'body': {
                    'ClientCode': self.cred_dict['encrypted_client_code'],
                    'Password': self.cred_dict['encrypted_client_password'],
                    'LocalIP': '192.168.0.1',
                    'PublicIP': '192.168.0.1',
                    'HDSerialNumber': '',
                    'MACAddress': '',
                    'MachineID': '',
                    'VersionNo': '1.0',
                    'RequestNo': 1,
                    'My2PIN': self.cred_dict['encrypted_2fa'],
                    'ConnectionType': '1'
                    }
                }
            
            modified_headers = self.headers
        
        elif req_type == 'margin':
            
            url = self.base_url + self.margin_endpoint
            
            payload = self.payload
            payload['head']['requestCode'] = self.margin_req_code
            
            modified_headers = self.headers
            
        elif req_type == 'net_positions':
            
            url = self.base_url + self.net_positions_endpoint
            
            payload = self.payload
            payload['head']['requestCode'] = self.net_positions_req_code
            
            modified_headers = self.headers
            
        elif req_type == 'historical':
            
            url = self.base_url + self.hist_data_endpoint
            
            payload = {}
            
            modified_headers = self.headers
            # del(modified_headers['Content-Type'])
            
        elif req_type == 'validate_token':
            
            url = self.base_url + self.token_val_endpoint
            
            payload = {
                'ClientCode': self.cred_dict['client_code']
                }
            
            modified_headers = self.headers
        
        elif req_type == 'orderbook':
            
            url = self.base_url + self.orderbook_endpoint
            
            payload = self.payload
            payload['head']['requestCode'] = self.orderbook_req_code
            
            modified_headers = self.headers
            
        elif req_type == 'tradebook':
            
            url = self.base_url + self.tradebook_endpoint
            
            payload = self.payload
            payload['head']['requestCode'] = self.tradebook_req_code
            
            modified_headers = self.headers
            
        elif req_type == 'order_status':
            
            url = self.base_url + self.order_status_endpoint
            
            payload = self.payload
            payload['head']['requestCode'] = self.order_status_req_code
            
            modified_headers = self.headers
            
        elif req_type == 'current_price':
            
            url = self.base_url + self.market_feed_endpoint
            
            payload = self.payload
            payload['head']['requestCode'] = self.market_feed_req_code
            
            modified_headers = self.headers
            
        elif req_type == 'place_order':
            
            url = self.base_url + self.place_order_endpoint
            
            modified_headers = self.headers
            
            payload = {
                "_ReqData": {
                    "head": {
                        "requestCode": self.place_order_req_code ,
                        "key": self.cred_dict['app_key'],
                        "appVer": self.cred_dict['app_ver'],
                        "appName": self.cred_dict['app_name'],
                        "osName": self.cred_dict['os_name'],
                        "userId": self.cred_dict['app_user_id'],
                        "password": self.cred_dict['app_password']
                        },
                    "body": {
                        "ClientCode": self.cred_dict['client_code'],
                        "DisQty": 0,
                        "IsStopLossOrder": False,
                        "StopLossPrice": 0,
                        "IsVTD": False,
                        "IOCOrder": False,
                        "PublicIP": '192.168.0.1',
                        "AHPlaced": "N",
                        "iOrderValidity": 0,
                        "OrderRequesterCode": self.cred_dict['client_code'],
                        "TradedQty": 0
                        }
                    },
                "AppSource": self.cred_dict['app_source']
                }
        
        return url, modified_headers, payload