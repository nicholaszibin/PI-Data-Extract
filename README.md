# PI-Data-Extract
This function uses PIConnect (https://pypi.org/project/PIconnect/) to extract 
'calculated' or 'sampled' data from a tag or a CSV file of tags within a OSI 
PI Historian database into a pandas DataFrame.

To use this function, you need to install PIConnect: 
`pip install PIconnect`

#### General Inputs:
1. Start Date: E.g., 8/21/2020  7:30:00 [MM/DD/YYY HH:MM:SS]
2. End Date: E.g., 8/21/2021  7:30:00 [MM/DD/YYY HH:MM:SS]
3. Time Interval: E.g., 60s (one minute), 10m (ten minutes), 1h (one hour), 1d (one day), 1m (one month), etc.
4. PI Tag: or 'csv file of PI tags' (e.g., 'P1-FIC-11-024/PV.CV'). A sample csv files is provided.
5. Variable Name: Often times, the PI tags are meaningless so you could use 'P1-Flow' for an example. The csv file uses the second column for the variable name.
6. Data Type: This can be either 'summary' (default) or 'sampled'.
	 - Summary works only with numeric data and can be used with 'Summary Type' below.
	 - Sampled works with either numerical or non-numerical data. This just grabs the data point at the time/interval selected.
7. Summary Type: is the type of calculation done for 'Summary' data type. This can be selected from the following:
	 - average (default)
   - maximum
   - minimum
   - total (i.e.,summation)
   - standard deviation (std_dev)
   - range
   - count
   - mean

#### Output:
Pandas DataFrame:
- Index: Time interval [datetime64]
- Header: Variable name(s)
- Columns: 
	* 'summary' data float64
	* 'sampled' data float64 or string depending on PI tag
               
#### Example 1:
In this example, we will extract 10-minute hourly average data for a flow meter during the calendar year of 2019.
`PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-FIC/PV.CV', 'P1-Flow')`

#### Example 2:
In this example we will calculate maximum monthly peak demand.
`PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-kW-11/PV.CV', 'P1-kW-Max', summaryType='maximum')`
    
#### Example 3: 
`PI_Call_Tag(1/1/2019, 1/1/2020, 10m, 'P1-FIC-11-024/PV.CV', 'P1-kW-Max', summaryType='maximum')`

There are two functions you can call:
1. `PI_Call` which works with a csv file of tags.
2. `PI_Call_Tag` which works with a list of pi tag and a list of var_names

#### TO DO:
- Combine both functions to use either csv file or list of tags.
