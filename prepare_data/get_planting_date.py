# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 18:17:00 2023
Calculates the planting date for the provided crops for the catchments provided as a shapefile
Can also be used for other variables available in the Crop Calendar Dataset

@author: Raphaël Payet-Burin
"""


import geopandas as gpd
import pandas as pd
import rioxarray
from rasterstats import zonal_stats
import os
folder = os.path.abspath(os.path.dirname(__file__))

#%% INPUTS
#data path
#planting date data from https://sage.nelson.wisc.edu/data-and-models/datasets/crop-calendar-dataset/ (Netcdf data, need to be unpacked .nc files)
planting_folder=os.path.join(folder,'..','background_data','planting_date') #folder with planting date data
#shapefile - path to shapefile data - REPLACE with actual shapefile name
catchments_path=os.path.join(folder,'..','data','WHATIF_ZamZim_EPSG4326.shp')
catchID='ncatch' #unique id field of catchments in shapefile
#crop file with crops to be modelled - and the corresponding crop name in the planting date database
crop_path=os.path.join(folder,'..','data','crops.csv')
#name of output .csv file
output=os.path.join(folder,'..','data','catchments_planting_date.csv') 
#projection CRS - preferably do not change
bCRS='EPSG:4326' 
#variable to be calculated 'plant' = average plant date, see planting date dataset
VARIABLE='plant' 

#%%Functions
#reads nc data and creates temporary tif file with data
def read_ncdata(nc_path,output='tempfile.tif',variable='plant'):
    with rioxarray.open_rasterio(nc_path,decode_times=False) as ncdata:
        ncdata.rio.write_crs('EPSG:4326', inplace=True)
        ncdata=ncdata[variable] #layer with average planting date
        ncdata.rio.to_raster(output)
        return output
#converts day number to date with month and day in format 'day/month'    
date_year=pd.date_range(start='2021-01-01', periods=365, freq='D')
def number2date(day):
    date=date_year[round(day)-1]
    date_dm ='%s/%s' % (date.month, date.day)
    return date_dm
        
#%%Get planting date per catchment and crop
#Load data
crops=pd.read_csv(crop_path).set_index('crop')
#catchments
catchments=gpd.read_file(catchments_path).to_crs(bCRS)
catchments=catchments[[catchID,'geometry']]

#planting date
for crop in crops.index:
    pcrop = crops.loc[crop,'planting_data']
    if pcrop == pcrop:
        raster_name=os.path.join(planting_folder,pcrop+'.crop.calendar.fill.nc')
        raster_path=read_ncdata(raster_name,variable=VARIABLE)
        catchments[crop]=pd.DataFrame(zonal_stats(vectors=catchments, raster=raster_path, all_touched=False, stats='mean'))
        #Convert day number to aquacrop date format
        if VARIABLE not in ['tot.days']:
            catchments[crop]=catchments[crop].apply(number2date)
#export
catchments.drop('geometry',axis=1).to_csv(output,index=False)