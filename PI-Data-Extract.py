#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This function uses PIConnect (https://pypi.org/project/PIconnect/) to extract 
'calculated' or 'sampled' data from a tag or a CSV file of tags within a OSI 
PI Historian database into a pandas DataFrame.

To use this function, you need to install PIConnect: pip install PIconnect
               
Example 1:
    Extract 10-minute hourly average data for a flow meter during the calendar 
    year of 2019.
        PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-FIC-11/PV.CV', 'P1-Flow')

Example 2:
    In this example we will calculate maximum monthly peak demand.
        PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-kW-11/PV.CV', 'P1-kW-Max', summaryType='maximum') 
        The function outputs a dataframe with the variable renamed 'P1-kW-Max'.
    
Example 3: 
    Extract data from a csv file list of tags and var_names for a pump station.
    PI_Call('1/1/2020  7:30:00', '2/1/2021  11:47:00', '60s', 'sample-PI-Data-Extract.csv', dataType='summary', summaryType='average')

@Author: Nicholas Zibin
@Date: August 10, 2020
@License: MIT

"""


import PIconnect as PI
import pandas as pd
from csv import reader
from PIconnect.PIConsts import SummaryType

def PI_Call(start, end, interval, csvFile, dataType='summary', summaryType='average'):
    '''Extract data from a CSV file of tags within a OSI PI Historian database 
       into a pandas DataFrame.
       
       Args:
           start (str): Start date. E.g., 8/21/2020  7:30:00 [MM/DD/YYY HH:MM:SS]
           end (str): End date.   E.g., 8/21/2021  7:30:00 [MM/DD/YYY HH:MM:SS]
           interval: (str): Time interval. E.g., 60s (one minute), 10m (ten 
                            minutes), 1h (one hour),1d (one day), 1m (one month), etc.
           csvFile (str): CSV file containing column of PI tags and one column
                          and your variable name of choice for each tag.
           dataType (str): Either 'summary' (defualt), or 'sampled'
           summaryType (str): Summary type calculation:
                                  -average (default)
                                  -maximum
                                  -minimum
                                  -total (i.e.,summation)
                                  -standard deviation (std_dev)
                                  -range
                                  -count
                                  -mean
                                  
        Returns:
             Pandas DataFrame:
                Index: Time interval [datetime64]
                Header: Variable name(s)
                Columns: 'summary' data float64
                         'sampled' data float64 or string depending on PI tag           
                   
    '''
    
    #Import the data in csv file with the format of: PI tag, variable name
    with open(csvFile, 'r') as read_obj:
        csv_reader = reader(read_obj)
        query, var_names = zip(*csv_reader)
        query = list(query)
        var_names = list(var_names)

    #Load the data from PI
    with PI.PIServer() as server:
        points = server.search(query)
        data = []
        for point in points:
            if dataType == 'sampled':
                tmp = point.interpolated_values(start, end, interval)
            elif dataType == 'summary':
                if summaryType == 'average':
                    tmp = point.summaries(start, end, interval, SummaryType.AVERAGE)            
                elif summaryType == 'maximum':
                    tmp = point.summaries(start, end, interval, SummaryType.MAXIMUM)
                elif summaryType == 'minimum':
                    tmp = point.summaries(start, end, interval, SummaryType.MINIMUM)
                elif summaryType == 'total':
                    tmp = point.summaries(start, end, interval, SummaryType.TOTAL)
                elif summaryType == 'range':
                    tmp = point.summaries(start, end, interval, SummaryType.RANGE)  
                elif summaryType == 'count':
                    tmp = point.summaries(start, end, interval, SummaryType.COUNT)
                elif summaryType == 'std_dev':
                    tmp = point.summaries(start, end, interval, SummaryType.STD_DEV)                   
                else:    
                    print('ERROR: Summary type not valid.')
                    return
                tmp.columns = [point.tag]                
                data.append(tmp)
            
            else:
                print('ERROR: Data type not valid.')
                return
            
        data = pd.concat(data, axis=1)    
        data = data.tz_convert('Canada/Pacific').tz_localize(None) #Have to convert to timezone
        data.columns = var_names #Rename the columns to match the variable names
        
        ### Optional - If you want to pre-process any data you can do that here:
        #if dataType == 'sampled':
            #data = data.replace({'RUNNING': 1, 'STOPPED': 0, 'FAIL': 0})
            #data = data.drop(data.tail(1).index)
        #data = data.apply(pd.to_numeric, errors='coerce') #converts any errors to NaN
        #data = data.replace('[-11059] No Good Data For Calculation', np.nan)

    return data

def PI_Call_Tag(start, end, interval, query, var_name, dataType='summary', summaryType='average'):
    '''Extract data from a PI tag list within a OSI PI Historian database into a 
       pandas DataFrame.
       
       Args:
           start (str): Start date. E.g., 8/21/2020  7:30:00 [MM/DD/YYY HH:MM:SS]
           end (str): End date.   E.g., 8/21/2021  7:30:00 [MM/DD/YYY HH:MM:SS]
           interval: (str): Time interval. E.g., 60s (one minute), 10m (ten 
                            minutes), 1h (one hour),1d (one day), 1m (one month), etc.
           query (list): The PI Tag [list of strings]
           var_name (list): You can choose how to name the PI tag as they sometimes
                            don't have much meaning (e.g., 'P1-Flow') [list of strings]
           dataType (str): Either 'summary' (defualt), or 'sampled'
           summaryType (str): Summary type calculation:
                                  -average (default)
                                  -maximum
                                  -minimum
                                  -total (i.e.,summation)
                                  -standard deviation (std_dev)
                                  -range
                                  -count
                                  -mean
                                  
        Returns:
             Pandas DataFrame:
                Index: Time interval [datetime64]
                Header: Variable name(s)
                Columns: 'summary' data float64
                         'sampled' data float64 or string depending on PI tag
                         
        '''
        
    with PI.PIServer() as server:
        point = server.search(query)[0]
        data = []
        if dataType == 'sampled':
            data = point.interpolated_values(start, end, interval)
        elif dataType == 'summary':                
            if summaryType == 'average':
                data = point.summaries(start, end, interval, SummaryType.AVERAGE)            
            elif summaryType == 'maximum':
                data = point.summaries(start, end, interval, SummaryType.MAXIMUM)
            elif summaryType == 'minimum':
                data = point.summaries(start, end, interval, SummaryType.MINIMUM)
            elif summaryType == 'total':
                data = point.summaries(start, end, interval, SummaryType.TOTAL)
            elif summaryType == 'range':
                data = point.summaries(start, end, interval, SummaryType.RANGE)  
            elif summaryType == 'count':
                data = point.summaries(start, end, interval, SummaryType.COUNT)
            elif summaryType == 'std_dev':
                data = point.summaries(start, end, interval, SummaryType.STD_DEV)                   
            else:    
                print('ERROR: Summary type not valid.')
                return
            data.columns = [var_name]
            data = data.tz_convert('Canada/Pacific').tz_localize(None) #Have to convert to timezone
        
        else:
            print('ERROR: Data type not valid.')
            return
        
        #### Optional - If you want to pre-process any data you can do that here:
        #if dataType == 'sampled':
            #data = data.replace({'RUNNING': 1, 'STOPPED': 0, 'FAIL': 0})
            #data = data.drop(data.tail(1).index)
        #data = data.apply(pd.to_numeric, errors='coerce') #converts any errors to NaN
        #data = data.replace('[-11059] No Good Data For Calculation', np.nan)
        #data.columns[0] = var_name

    return data
