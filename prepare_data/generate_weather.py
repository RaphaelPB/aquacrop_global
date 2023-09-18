# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 15:01:59 2023
This code is somehow specific to the Zambezi study, it is advised to directly 
provide the data in the recommended format.

@author: Raphaël Payet-Burin
"""

import pandas as pd

#%% INPUTS
#   WARNING   # 
#This code is somehow specific to the Zambezi study, it is advised to directly 
#provide the data in the recommended format.
#   WARNING   # 

#data path
paths={'Precipitation':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\WHAT_IF\Data\wRainFall_zim.csv',
       'ReferenceET':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\WHAT_IF\Data\wET0_zim.csv',
       'MaxTemp':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\WHAT_IF\Data\Tmax_zim.csv'}
#daily data
paths={'Precipitation':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\Data\CLIOPT\zam_zim_daily_25_01_2023\precip_daily_zim.csv',
       'ReferenceET':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\Data\CLIOPT\zam_zim_daily_25_01_2023\pet_daily_zim.csv',
       'MaxTemp':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\Data\CLIOPT\zam_zim_daily_25_01_2023\tmax_daily_zim.csv',
       'MinTemp':r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\Data\CLIOPT\zam_zim_daily_25_01_2023\tmin_daily_zim.csv'}

output=r'C:\Users\RAPY\OneDrive - COWI\Projects\IEc_Zimbabwe\aquacrop\weather_data_daily_test.csv'
startT='2020-01-01'
endT='2023-12-31' #'2059-12-31'
date=pd.date_range(start=startT, end=endT, freq='D')
SPECIALEXTENTOBSERVED=0 #This was used when observed data was not as long as climate projections, to get a dataset of the same size by repeating observed data
scenarios=['observed','mri-esm2-0','access-cm2']

#%%functions
def reformat(wdata_path,wname,m2d=0):
    wdata=pd.read_csv(wdata_path)
    wdata=wdata.set_index(['scenario','ntime'])   
    wdata.columns.name='ncatch'
    wdata=wdata.stack()
    wdata.name=wname
    wdata=wdata.reset_index()
    #propagate observed
    if SPECIALEXTENTOBSERVED ==1:
        tmax=wdata[wdata['scenario']=='observed'].ntime.max()
        for k in range(2):
            b=wdata[wdata['scenario']=='observed']
            b['ntime']=b['ntime'].values+tmax
            wdata=pd.concat([wdata,b])
    #apply date
    nt0=min(wdata['ntime'])
    wdata=wdata[wdata['ntime']<len(date)+nt0]
    wdata=wdata[wdata['scenario'].isin(scenarios)]
    if m2d==0: #input is daily data
        wdata['Date']=pd.to_datetime(wdata['ntime'].apply(lambda k:date.values[k-nt0]))
    else: #input is monthly data
        months=pd.date_range(start=startT, end=endT, freq='M')
        wdata['Date']=pd.to_datetime(wdata['ntime'].apply(lambda k:months.values[k-nt0]))
        #convert monthly to daily
        if wname in ['Precipitation','ReferenceET']:
            wdata[wname]=wdata[wname]/(365/12) #convert monthly value to daily
        #propagate
        wdata=wdata.pivot(index='Date', columns=['scenario','ncatch'])
        wdata=wdata.reindex(date,method='bfill')
        wdata.index.name='Date'
        wdata=wdata.stack(['scenario','ncatch']).reset_index()
    return wdata

#%%process data
weather=reformat(paths['Precipitation'],'Precipitation')
weather['ReferenceET']=reformat(paths['ReferenceET'],'ReferenceET')['ReferenceET']
weather['MaxTemp']=reformat(paths['MaxTemp'],'MaxTemp')['MaxTemp']
weather['MinTemp']=reformat(paths['MinTemp'],'MinTemp')['MinTemp']
#special what-if conversion to get catchment name matching farm name
weather.loc[:,'ncatch']='R_'+weather['ncatch']
#export
weather.round(2).to_csv(output,index=False)