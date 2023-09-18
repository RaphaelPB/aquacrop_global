# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 11:43:43 2023

Gets the USDA soil texture classification for each catchment provided in the shapefile
Calculates the main soil type for the top soil

@author: Raphaël Payet-Burin
"""

import geopandas as gpd
import pandas as pd
import os
folder = os.path.abspath(os.path.dirname(__file__))

#%% INPUTS
#soil database data path (these files are already processed from the raw database - if you donwloaded the raw database you need to polygonize it)
#data source https://sage.nelson.wisc.edu/data-and-models/datasets/crop-calendar-dataset/netcdf-5-min/
hwsd_path=os.path.join(folder,'..','background_data','HarmonizedSoilWorldDatabase','HWSD_DATA.csv')
#r'C:\Users\RAPY\OneDrive - COWI\Data\HarmonizedSoilWorldDatabase\HWSD_DATA.csv'
hwsd_shape_path=os.path.join(folder,'..','background_data','HarmonizedSoilWorldDatabase','hwsd_polygonized_EPSG4326.shp')
#r'C:\Users\RAPY\OneDrive - COWI\Data\HarmonizedSoilWorldDatabase\hwsd_polygonized_EPSG4326.shp'
#shapefile - path to shapefile data - REPLACE with actual shapefile name
catchments_path=os.path.join(folder,'..','data','WHATIF_ZamZim_EPSG4326.shp')
catchID='ncatch' #unique id field of catchments
#name of output .csv file
output=os.path.join(folder,'..','data','catchments_soil_max.csv')
#projection CRS
bCRS='EPSG:4326' 

#%%Load data
#soil data 
hwsd=pd.read_csv(hwsd_path)
hwsd=hwsd.loc[hwsd.groupby('MU_GLOBAL')['SHARE'].idxmax()] #keep only main soil characteristics
hwsd_shape=gpd.read_file(hwsd_shape_path).to_crs(bCRS) #polygons
hwsd_shape=hwsd_shape[hwsd_shape['DN']!=0] #exclude DN = 0 which is the Ocean

#catchments
catchments=gpd.read_file(catchments_path).to_crs(bCRS)
catchments=catchments[[catchID,'geometry']]

#%%Get soil data per catchment linking shapefile and database
#catchments_soil = catchments.overlay(soildata,how='intersection')
catchments_soil = catchments.overlay(hwsd_shape,how='intersection')
catchments_soil['area']=catchments_soil.to_crs({'proj':'cea'}).area/10**6
catchments_soil['T_USDA_TEX_CLASS']=catchments_soil['DN'].apply(lambda x: hwsd.set_index('MU_GLOBAL').loc[x,'T_USDA_TEX_CLASS'])
catchments_soil = catchments_soil[[catchID,'T_USDA_TEX_CLASS','area']]

#Groupby catchment and soil type
catchments_soil = catchments_soil.groupby([catchID,'T_USDA_TEX_CLASS'],as_index=False).sum()

#Convert to aquacrop format
USDA_tex={1:'Clay',2:'SiltyClay',3:'Clay',4:'SiltyClayLoam',5:'ClayLoam',6:'Silt',
          7:'SiltLoam',8:'SandyClay',9:'Loam',10:'SandyClayLoam',11:'SandyLoam',
          12:'LoamySand',13:'Sand'}
catchments_soil['aqua_TEX']=catchments_soil['T_USDA_TEX_CLASS'].apply(lambda k:USDA_tex[int(k)])

#get majority soil type
catchments_soil_max = catchments_soil.loc[catchments_soil.groupby(catchID)['area'].idxmax()]

#export
catchments_soil_max.to_csv(output,index=False)


