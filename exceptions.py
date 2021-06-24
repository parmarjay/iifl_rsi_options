# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 22:49:22 2021

@author: JAY
"""

class CustomError(Exception):
    
    def __init__(self, message):
        
        self.message = message