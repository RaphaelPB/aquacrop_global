# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 11:31:43 2023
Main function running the aquacrop model once the data has been prepared

@author: Raphaël Payet-Burin
"""
import os
import pandas as pd
import warnings
idx=pd.IndexSlice
import setuptools #only useful to apply a monkeypatch on numpy.distutils for the compiler
os.environ['DEVELOPMENT'] = 'DEVELOPMENT' #related to a bug, probably related to windows, might speed up by removing this in Linux

from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent
#from aquacrop.utils import prepare_weather, get_filepath
folder = os.path.abspath(os.path.dirname(__file__))

#%%INPUT
#Start and end date of simulation
startT=f"{2020}/05/01"
endT=f"{2022}/10/30"
#crops file
crop_path=os.path.join(folder,'data','crops.csv')
#weather data (user input)
weather_path=os.path.join(folder,'data','weather_data_daily.csv')
#soil data (use get_soil_texture.py to generate)
soildata_path=os.path.join(folder,'data','catchments_soil_max.csv')
#planting date data (use get_planting_date.py to generate)
plantingdate_path=os.path.join(folder,'data','catchments_planting_date.csv') 
#name of catchment unique ID in shapefile and other data (e.g. weather, planting date)
catchID='ncatch'
#output file name
output=os.path.join(folder,'outputs','Yields_aquacrop_daily_test.csv')

#%% functions
def prep_weather(weather,scenario,catch):
    weather=weather[(weather[catchID]==catch) & (weather['scenario']==scenario)]
    return weather[[ 'MinTemp', 'MaxTemp', 'Precipitation', 'ReferenceET', 'Date']]

#aquacrop
def aquacrop_yield(weather,scenario,catch,crop):
    #weather
    weather_prep = prep_weather(weather,scenario,catch)
    #soiltype
    soiltype = catchments.loc[catch,'aqua_TEX']
    #planting date
    if crop in plantingdate.columns:
        planting_date = plantingdate.loc[catch,crop]
    else:
        planting_date = cropdata.loc[crop,'planting_date']
    #run aquacrop
    with warnings.catch_warnings(): #delete aquacrop warnings (might remove that step if something does not work...)
        warnings.simplefilter("ignore")
        model_os = AquaCropModel(
                sim_start_time=startT,
                sim_end_time=endT,
                weather_df=weather_prep,
                soil=Soil(soil_type=soiltype),
                crop=Crop(crop, planting_date=planting_date),
                initial_water_content=InitialWaterContent(value=['FC']),
                                    )
        model_os.run_model(till_termination=True)
        model_results = model_os.get_simulation_results()
        return list(model_results['Yield (tonne/ha)'].values)

#%%calculate yields
#load data
cropdata=pd.read_csv(crop_path).set_index('crop')
catchments=pd.read_csv(soildata_path).set_index(catchID)
plantingdate=pd.read_csv(plantingdate_path).set_index(catchID)
weather_data=pd.read_csv(weather_path)
weather_data['Date']=pd.to_datetime(weather_data['Date']) #needs to be redefined as type gets lost in csv
#index
scenarios=weather_data.scenario.unique() #['observed']
years=pd.date_range(start=startT, end=endT, freq='Y').year.values
iterables=[scenarios,years,catchments.index,cropdata.index]
mindex=pd.MultiIndex.from_product(iterables, names=['scenario', 'ayear', 'acatch', 'acrop']) 

#%%yields
Yaqua=pd.DataFrame(index=mindex,columns=['Yield (tonne/ha)'])
for scen in scenarios:
    print(scen)
    for crop in cropdata.index:
        print(crop)
        for catch in catchments.index:      
            aquayield=aquacrop_yield(weather_data,scen,catch,crop)
            if len(aquayield)<len(years): #if a year is missing because of simulation time does not cover crop growth time
                aquayield.append(aquayield[-1])
            Yaqua.loc[idx[scen,:,catch,crop],'Yield (tonne/ha)']=aquayield[:len(years)]
Yaqua['Yield (tonne/ha)']=pd.to_numeric(Yaqua['Yield (tonne/ha)'])

#%%relative yields - average yield by scenario, catchment, and crop
Yaqua_mean=Yaqua.reset_index().groupby(by=['scenario','acatch','acrop']).mean() #average yield
Yaqua_max=Yaqua.reset_index().groupby(by=['scenario','acatch','acrop']).max() #max yield
#Yaqua_rel=Yaqua.copy(deep=True)
for scen in scenarios:    
    for crop in cropdata.index:        
        for catch in catchments.index:     
            refyieldmean=Yaqua_mean.loc[idx['observed',catch,crop],'Yield (tonne/ha)']
            refyieldmax=Yaqua_max.loc[idx['observed',catch,crop],'Yield (tonne/ha)']
            relyieldmean=Yaqua.loc[idx[scen,:,catch,crop],'Yield (tonne/ha)']/refyieldmean
            relyieldmax=Yaqua.loc[idx[scen,:,catch,crop],'Yield (tonne/ha)']/refyieldmax
            Yaqua.loc[idx[scen,:,catch,crop],'YieldFactor_mean']=relyieldmean
            Yaqua.loc[idx[scen,:,catch,crop],'YieldFactor_max']=relyieldmax
#convert to cultures (WHAT-IF)
Yaqua=Yaqua.reset_index()
Yaqua['acrop']=Yaqua['acrop'].apply(lambda x: cropdata.loc[x,'nculture'])
#Export
Yaqua.to_csv(output,index=False)
