# -*- coding: utf-8 -*-
"""
Set of functions to read and analyse parkrun data. 
See http://www.parkrun.org.uk/ for more information about parkrun.
:author: Joseph Barraud
:license: BSD License
"""
import os.path,datetime
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# Age categories
allCats = ['JM10', 'JM11-14', 'JM15-17', 'JW10', 'JW11-14', 'JW15-17',
       'SM18-19', 'SM20-24', 'SM25-29', 'SM30-34', 'SW20-24', 'SW25-29',
       'SW30-34', 'VM35-39', 'VM40-44', 'VM45-49', 'VM50-54', 'VM55-59',
       'VM60-64', 'VM65-69', 'VM70-74', 'VW35-39', 'VW40-44', 'VW45-49',
       'VW50-54', 'VW55-59', 'VW60-64', 'VW65-69', 'VW70-74']
selectCats = ['SM25-29', 'SM30-34', 
              'SW25-29', 'SW30-34', 
              'VM35-39', 'VM40-44', 'VM45-49', 'VM50-54', 'VM55-59', 
              'VW35-39', 'VW40-44', 'VW45-49', 'VW50-54', 'VW55-59']
              
#==============================================================================
# Converter functions for csv import
#==============================================================================
convertDate = lambda x : datetime.datetime.strptime(x, "%d/%m/%Y")
convertPercent = lambda x: float(x.strip("%"))/100.
def timeString_to_minutes(x):
    '''
    Convert time from a string 'hh:mm:ss' to number of minutes as a float
    '''
    xlist = map(int,x.split(':'))
    try:
        time = 60*xlist[0]+xlist[1]+xlist[2]/60. # rare case when time is larger than one hour
    except:
        time = xlist[0]+xlist[1]/60.
    return time
    
def minutes_to_timeString(x):
    '''
    Return time in minutes to string formatted as 'mm:ss'
    '''
    return '{}:{:02.0f}'.format(int(x),round((x-int(x))*60)) 
    
def timeFormat(x,pos):  
    '''
    Return time formatted as a string 'mm:ss'
    pos is not used but necessary because this function can be used in 
    matplotlib.ticker.FuncFormatter(func)
    '''
    return '{}:{:02.0f}'.format(int(x),round((x-int(x))*60)) 
    
#==============================================================================
#  importResults
#==============================================================================
def importResults(infile,skiprows=13,skipfooter=36,removeUnknowns=True,report=False):
    '''
    Import results table from a text file into a pandas dataframe
    '''
    colNames=['Position','Runner','Time','Age Cat','Age Grade','Gender','Gender Pos',
            'Club','Note','Total Runs','Badges']
            
    # read input file (skipfooter requires python engine)
    results = pd.read_csv(infile,sep='\t',skiprows=13,skipfooter=36,header=None,  
                      engine='python',names=colNames,index_col='Position',
                      converters={'Time': timeString_to_minutes, 'Age Grade':convertPercent})
    
    # drop less interesting columns
    results = results.drop(['Club','Note','Badges'],axis=1)
    
    # a few parameters
    totalRunners = len(results)
    totalUnknowns = len(results[results['Runner'] == 'Unknown'])
    validEntries = totalRunners - totalUnknowns
    maleRunners = np.sum(results['Gender']=='M')
    
    # apply correct dtypes (can't apply before because of the python engine)
    results[['Time','Age Grade']] = results[['Time','Age Grade']].astype('float')
    
    # remove unknown entries (NaN)
    if removeUnknowns:
        results = results[results['Runner'] != 'Unknown']
        # convert two columns to integers (would otherwise remain as floats)
        results[['Gender Pos','Total Runs']] = results[['Gender Pos','Total Runs']].astype('int')
    
    # report
    if report:
        print('\nImport of file '+os.path.basename(infile))
        print('Number of runners = {}'.format(totalRunners))
        print('Number of valid entries = {}'.format(validEntries))
        print('Number of unknowns = {} ({:.1f}%)'.format(totalUnknowns,
                                                         100*float(totalUnknowns)/totalRunners))
        print('Number of male runners = {} ({:.1f}%)'.format(maleRunners,
                                                         100*float(maleRunners)/validEntries))
                      
        
    return results
    
#==============================================================================
# print_stats  
#==============================================================================
def print_stats(results,feature='Time'):
    '''
    Print a few statistical quantities and format the results depending on
    the type of data (time or not).
    '''
    
    print('Basic statistics on {}:'.format(feature))
    print('Runners,Male %,Mean,Std,Min,25%,Median,75%,Max')
    totalRunners = len(results)
    totalUnknowns = len(results[results['Runner'] == 'Unknown'])
    validEntries = totalRunners - totalUnknowns
    maleRunners = np.sum(results['Gender']=='M')
    stats = results[feature].describe()
    
    if feature == 'Time':
        formatted_stats = map(minutes_to_timeString,stats.tolist()[1:])
    elif feature == 'Age Grade':
        formatted_stats = map(lambda x:'{:.1f}'.format(x),(stats*100).tolist()[1:])
    else:
        formatted_stats = stats.tolist()[1:]
        
    stats_list = [totalRunners,100*float(maleRunners)/validEntries]
    stats_list = stats_list + formatted_stats
                      
    print('{},{:.1f}%,{},{},{},{},{},{},{}'.format(*stats_list))
    
#==============================================================================
# resample_AgeCat
#==============================================================================
def resample_AgeCat(results,nsamples=5):
    '''
    Pick a number of samples from each Age Categories
    '''
    newResults = pd.DataFrame()
    
    for cat in selectCats:
        # pick samples randomly
        try:
            newResults = newResults.append(
                results[results['Age Cat']==cat].sample(n=nsamples,replace=False))
        except: # in case the category is empty
            pass
    return newResults
    
#==============================================================================
# resample
#==============================================================================
def resample(results1,results2,nsamples=50,nCats=10):
    '''
    Pick a number of samples from results2 according to distribution in results1
    '''
    
    # create Age Grade categories
    results1['AG_Cat'] = pd.cut(results1['Age Grade']*100,
                bins=range(0,100+100/nCats,100/nCats),labels=range(0,nCats))
    counts = results1['AG_Cat'].value_counts() 
    
    # counts for each category become the weights used for sampling
    results1['weights'] = [counts[x] for x in results1['AG_Cat']]
    
    # do the same for results2 but calculate weights according to results1
    results2['AG_Cat'] = pd.cut(results2['Age Grade']*100,
                bins=range(0,100+100/nCats,100/nCats),labels=range(0,nCats))
                                 
    # the weights are taken from the first distribution
    results2['weights'] = [counts[x] for x in results2['AG_Cat']]
    
    # return resampled data using weights
    return results2.sample(n=nsamples,weights='weights',replace=False)
    
#==============================================================================
# time_hist
#==============================================================================
def time_hist(results,title=None,style='bmh'):
    '''
    Draw an histogram of the time results with basic stats added in the corner
    '''
    # reset style first (if style has been changed before running the script)
    plt.style.use('classic')
    plt.style.use(style)
    plt.style.use(r'.\large_font.mplstyle')
        
    fig, ax = plt.subplots(figsize=(10,8))
    ax.hist(results['Time'],bins=range(15,61))
    ax.set_xlim(15,60)
    ax.set_xlabel('Time (min)',size='x-large')
    ax.set_ylim(0,40)
    ax.set_ylabel('Count',size='x-large')
    plt.title(title)
    
    # add stats in a box in the corner
    stats = results['Time'].describe()
    stats_text = "Count  = {:.0f}\nMean   = {}\nMedian = {}\nMin    = {}\nMax    = {}".format(
                stats['count'],
                minutes_to_timeString(stats['mean']),
                minutes_to_timeString(stats['50%']),
                minutes_to_timeString(stats['min']),
                minutes_to_timeString(stats['max']))
                
    font0 = FontProperties()
    font0.set_family('monospace')
    ax.text(47,30,stats_text,fontsize=14,fontproperties=font0,bbox=dict(facecolor='white'))
    
#==============================================================================
# ageGrade_hist
#==============================================================================
def ageGrade_hist(results,title=None,style='bmh'):
    '''
    Draw an histogram of the Age Grade results with basic stats added in the corner
    '''
    # reset style first (if style has been changed before running the script)
    plt.style.use('classic')
    plt.style.use(style)
    plt.style.use(r'.\large_font.mplstyle')
        
    fig, ax = plt.subplots(figsize=(10,8))
    ax.hist(results['Age Grade']*100,bins=np.arange(0,100,5),color='#A60628')
    #ax.set_xlim(15,60)
    ax.set_xlabel('Age Grade %',size='x-large')
    #ax.set_ylim(0,40)
    ax.set_ylabel('Count',size='x-large')
    plt.title(title)
    
    # add stats in a box
    stats = results['Age Grade'].describe()
    stats.iloc[1:]=stats.iloc[1:]*100
    stats_text = "Count  = {:.0f}\nMean   = {:.1f}%\nMedian = {:.1f}%" +\
                "\nMin    = {:.1f}%\nMax    = {:.1f}%"
    stats_text = stats_text.format(stats['count'],
                                   stats['mean'],stats['50%'],
                                   stats['min'],stats['max'])
    font0 = FontProperties()
    font0.set_family('monospace')
    ax.text(0.72,0.75,stats_text,fontsize=14,fontproperties=font0,
            bbox=dict(facecolor='white'),transform=ax.transAxes)
    
#==============================================================================
# plot_AgeCat
#==============================================================================
def plot_AgeCat(results):
    '''
    Make a bar chart with the number of runners in each age category
    '''
    age_count = results['Age Cat'].value_counts()
    age_count.sort_index(inplace=True) # order categories in alphabetical order
    fig, ax = plt.subplots(figsize=(10,8))
    age_count.plot(kind='barh',ax=ax)
    ax.set_xlabel('Number of runners',size='x-large')
