import UAVTools.Functions
import UAVTools.Functions as f
import UAVTools.VegIndex
import UAVTools.VegIndex as vi
import UAVTools.ZonalPlotStat
import UAVTools.ZonalPlotStat as zps

import os, sys
import arcpy
import pandas as pd

from importlib import reload
reload(UAVTools.VegIndex)
reload(UAVTools.Functions)
reload(UAVTools.ZonalPlotStat)

# ---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
    if(ap is not None):
        ap.AddMessage(msg)
    print(msg)


# Get the tools parameters [plot_lyr, plot_id_field, img, classified_raster, veg_index, out_stat_file, tiff_flag]
def get_tool_param():
    param = {}
    for p in arcpy.GetParameterInfo():
        param[p.name] = p.value
    return(param)



if __name__ == '__main__':

    DEBUG = False
    VEG_INDEX_DIR = 'vi'

    # Get the parameters set in the Toolbox and in the current Map
    _toolparam = get_tool_param()
    _mapparam = f.set_arcmap_param()

    # Set the output directory for the geotiffs
    _vi_directory = os.path.join(_mapparam['root'], VEG_INDEX_DIR)


    # set the UAV image and classifed raster data - and related data - assuming multispectrial
    _uavimg_data = f.set_image_data(_toolparam['img'])
    _classifed_raster_data = f.set_classifed_raster_data(_toolparam['classified_raster'])
    arcpy.env.cellSize = _uavimg_data['raster']

    # chck to see that the image has a least 5 bands (this will need re-written at some ponint for 10 band imagary)
    if(_uavimg_data['num_bands'] < 5):
        arcpy.AddError("ERROR: 'UAV Image' must contain 5 (or more) bands\n   -> {0} bands found".format(_uavimg_data['num_bands']))
        sys.exit()


    # get the bands within the image
    _band_order = f.set_band_order(_uavimg_data['num_bands'])
    _uavimg_data.update( { 
        'bands' : f.get_image_bands(_toolparam['img'], _band_order)
    })


     # A dictionary to keep track of index rasters
    vi_raster_data = {}

    # Calculate a vegetative index (NDVI)
    if(_toolparam['veg_index'] in ['NDVI','ALL']):
        _ndvi = vi.calcNDVI(_uavimg_data['bands'], _band_order)
        vi_raster_data['ndvi'] = {
            'index' : 'NDVI',
            'raster': _ndvi,
            'out_tiff': _uavimg_data['name_base'] + '_ndvi.tif'
        }

    # Calculate a vegetative index (RENDVI)
    if(_toolparam['veg_index'] in ['RENDVI','ALL']):
        _rendvi = vi.calcRENDVI(_uavimg_data['bands'], _band_order)
        vi_raster_data['rendvi'] = {
            'index' : 'RENDVI',
            'raster': _rendvi,
            'out_tiff': _uavimg_data['name_base'] + '_rendvi.tif'
        }


    # Calculate a vegetative index (RGBVI)
    if(_toolparam['veg_index'] in ['DVI','ALL']):
        _dvi = vi.calcDVI(_uavimg_data['bands'], _band_order)
        vi_raster_data['dvi'] = {
            'index' : 'DVI',
            'raster': _dvi,
            'out_tiff': _uavimg_data['name_base'] + '_dvi.tif'
        }


    # Calculate a vegetative index (NGRDI)
    if(_toolparam['veg_index'] in ['RVI','ALL']):    
        _rvi = vi.calcRVI(_uavimg_data['bands'], _band_order)
        vi_raster_data['rvi'] = {
            'index' : 'RVI',
            'raster': _rvi,
            'out_tiff': _uavimg_data['name_base'] + '_rvi.tif'
        }     


    # Calculate a vegetative index (GNDVI)
    if(_toolparam['veg_index'] in ['GNDVI','ALL']):    
        _gndvi = vi.calcGNDVI(_uavimg_data['bands'], _band_order)
        vi_raster_data['gndvi'] = {
            'index' : 'GNDVI',
            'raster': _gndvi,
            'out_tiff': _uavimg_data['name_base'] + '_gndvi.tif'
        }  


    # Calculate a vegetative index (REI)
    if(_toolparam['veg_index'] in ['REI','ALL']):    
        _rei = vi.calcREI(_uavimg_data['bands'], _band_order)
        vi_raster_data['gndvi'] = {
            'index' : 'REI',
            'raster': _rei,
            'out_tiff': _uavimg_data['name_base'] + '_rei.tif'
        }  


    #-- This section is responsible for the zonal statistics calculated from a zonal raster            --#
    #-- the zonal raster is created by combining the plot layer (as a raster) with a classifed ratser  --#

    zps = zps.ZonalPlotStat(_mapparam['scratch'], _toolparam['plot_lyr'], _toolparam['plot_id_field'], _toolparam['classified_raster'])

    # Calculate the zonal statistics for each VI calculated
    zone_stat_data = {}
    for index, vi_data in vi_raster_data.items():
        tweet("MSG: Calculating Zonal Statistics for Index\n  -> {0}".format(index), ap=arcpy)
        _out_stat_file = os.path.join(_mapparam['scratch'], index + '_zs')
        zone_stat_data[index] = zps.calculate(vi_data['raster'], _out_stat_file, 'index', index)
  

    # combine all the data frames into one 
    _df_list = [zone_stat_data[index]['df'] for index, data in zone_stat_data.items()]
    _zonestat_df_all = f.combine_dataframes(_df_list)

    # clean up some columns
    _dropCol = ['variety','majority', 'minority', 'median', 'pct90', 'count_y']
    f.clean_zonestat_df(_zonestat_df_all, drop_columns=_dropCol)

	# Save the zonal statistics to a table
    tweet("MSG: Saving Zonal Statistics\n  -> {0}".format(_toolparam['out_stat_file'].value), ap=arcpy)
    _zonestat_df_all.to_csv(_toolparam['out_stat_file'].value, index=False)


    # Write the tiffs to disk - make directory if needed
    if(_toolparam['tiff_flag']):
        f.make_dir(_vi_directory)
        for index, data in vi_raster_data.items():
            outFilePath = os.path.join(_vi_directory, data['out_tiff'])
            tweet("MSG: Saving raster for index ({0})\n  - {1}".format(data['index'], outFilePath), ap=arcpy)
            data['raster'].save(outFilePath)
            

    zps.cleanup()
    tweet("YOU WELCOME...", ap=arcpy)