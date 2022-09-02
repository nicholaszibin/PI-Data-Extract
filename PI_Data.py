#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This function uses PIConnect (https://pypi.org/project/PIconnect/) to extract 
'calculated' or 'sampled' data from a tag or a CSV file of tags within a OSI 
PI Historian database into a pandas DataFrame.

To use this function, you need to install PIConnect: pip install PIconnect

INPUTS:
    1. 'Start Date' E.g., 8/21/2020  7:30:00 [MM/DD/YYY HH:MM:SS]
    2. 'End Date'   E.g., 8/21/2021  7:30:00 [MM/DD/YYY HH:MM:SS]
    3. 'Time Interval' E.g., 60s (one minute), 10m (ten minutes), 1h (one hour), 
                       1d (one day), 1m (one month), etc.
    4. 'PI Tag' or 'csv file of PI tags' (e.g., 'P1-FIC-11-024/PV.CV'). A
        sample csv files is provided.
    5. 'Variable Name' Often times, the PI tags are meaningless so you could
        use 'P1-Flow' for an example. The csv file uses the second column for
        the variable name.
    6. 'Data Type' This can be either 'summary' (default) or 'sampled'.
            -Summary works only with numeric data and can be used with 'Summary 
             Type' below.
            -Sampled works with either numerical or non-numerical data. This 
             just grabs the data point at the time/interval selected.
    7. 'Summary Type' is the type of calculation done for 'Summary' data type.
        This can be selected from the following:
          -average (default)
          -maximum
          -minimum
          -total (i.e.,summation)
          -standard deviation (std_dev)
          -range
          -count
          -mean

OUTPUTS:
    Pandas DataFrame:
        Index: Time interval [datetime64]
        Header: Variable name(s)
        Columns: 'summary' data float64
                 'sampled' data float64 or string depending on PI tag
               
Example 1:
    In this example, we will extract 10-minute hourly average data for a flow 
    meter during the calendar year of 2019.
        PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-FIC/PV.CV', 'P1-Flow')

Example 2:
    In this example we will calculate maximum monthly peak demand.
        PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-FIC-11-024/PV.CV', 'P1-kW-Max', summaryType='maximum')
   
    The function outputs a dataframe with the variable renamed 'P1-kW-Max'.
    
Example 3: 
    Let's extract data from a power meter with the PI tag: P1-KW-11-024/PV.CV
    We want data range between 1/1/2019 to 1/1/2020
    We want the the maximum data over a 1 month time interval
    The function would be:
        PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-FIC-11-024/PV.CV', 'P1-kW-Max', summaryType='maximum')
   
    The function outputs a dataframe with the variable renamed 'P1-kW-Max'.

TO DO:
-Add functionality to use multiple different summary types within a csv file

@Author: Nicholas Zibin
@Date: August 10, 2020
@License: MIT

"""


import PIconnect as PI
import pandas as pd
import numpy as np
from csv import reader
from PIconnect.PIConsts import SummaryType

def PI_Call(start, end, interval, csvFile, dataType='summary', summaryType='average'):
    '''Extract 'calculated' or 'sampled' data from a tag or a CSV file of tags 
       within a OSI PI Historian database into a pandas DataFrame.
       
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
    # For example, the variable name could be 'Flow'
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
                tmp = tmp.rename(columns={'AVERAGE': point.tag})                
                data.append(tmp)
            else:
                print('ERROR: Data type not valid.')
                return
        data = pd.concat(data, axis=1)    
        data = data.tz_convert('Canada/Pacific').tz_localize(None) #Have to convert to timezone
        if dataType == 'sampled':
            data = pd.DataFrame(data)
            data = data.tz_convert('Canada/Pacific').tz_localize(None)
            data = data.replace({'RUNNING': 1, 'STOPPED': 0, 'FAIL': 0})
            data = data.rename(columns = {query: var_name})
            data = data.drop(data.tail(1).index)
        data = data.apply(pd.to_numeric, errors='coerce') #converts any errors to NaN
        data = data.replace('[-11059] No Good Data For Calculation', np.nan)
        data.columns = var_names

    return data

def PI_Call_Tag(start, end, interval, query, var_name, dataType='summary', summaryType='average'):
    
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
            data = data.rename(columns={'AVERAGE': var_name}) 
            data = data.tz_convert('Canada/Pacific').tz_localize(None) #Have to convert to timezone
        else:
            print('ERROR: Data type not valid.')
            return
        if dataType == 'sampled':
            data = pd.DataFrame(data)
            data = data.tz_convert('Canada/Pacific').tz_localize(None)
            data = data.replace({'RUNNING': 1, 'STOPPED': 0, 'FAIL': 0})
            data = data.rename(columns = {query: var_name})
            data = data.drop(data.tail(1).index)
        data = data.apply(pd.to_numeric, errors='coerce') #converts any errors to NaN
        data = data.replace('[-11059] No Good Data For Calculation', np.nan)
        #data.columns[0] = var_name

    return data


df = PI_Call_Tag('2022-08-01 00:00:00', '2022-09-01 00:00:00', '5m', 'SSPP-P-200/RUN.CV', 'P200_ON', dataType='sampled')

#Test below
#t20 = PI_Call('8/21/2020  7:30:00', '8/21/2020  11:47:00', '60s', 'Cape_Horn_tags.csv')
#t20_sampled = PI_Call('8/21/2020  7:30:00', '8/21/2020  11:47:00', '60s', 'Cape_Horn_sampled_tags.csv', dataType='sampled')
#t20 = pd.concat([t20, t20_sampled], axis=1)
#print(t20.V226[140]) 
    
#t20 = PI_Call_Tag('8/21/2020  7:30:00', '8/21/2020  11:47:00', '60s', 'WWHL-LI-051/VOLUME/PV.CV', 'CH_Vol', dataType='summary', summaryType='average')