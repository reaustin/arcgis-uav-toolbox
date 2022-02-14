import UAVTools.Functions
import UAVTools.Functions as f
import UAVTools.SpatialAnalysis as sa
import UAVTools.SpatialAnalysis
import UAVTools.VegIndex as vi

import os, sys
import arcpy
from arcpy.sa import ZonalStatisticsAsTable, Combine, ExtractByMask, RasterCalculator
import pandas as pd

from importlib import reload
import UAVTools.VegIndex

reload(UAVTools.VegIndex)
reload(UAVTools.SpatialAnalysis)
reload(UAVTools.Functions)


# ---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
    if(ap is not None):
        ap.AddMessage(msg)
    print(msg)


# Get the tools parameters [plot_lyr, plot_id_field, img, classified_img, veg_index, out_stat_file, tiff_flag]
def get_tool_param():
    param = {}
    for p in arcpy.GetParameterInfo():
        param[p.name] = p.value
    return(param)



if __name__ == '__main__':

    DEBUG = False
    BAND_ORDER = ['R', 'G', 'B']

    # Get the parameters set in the Toolbox and in the current Map
    _toolparam = get_tool_param()
    _mapparam = f.set_arcmap_param()

    # set UAV Image and related data
    _classifed_raster_data = f.set_classifed_raster_data(_toolparam['classified_img'])
    arcpy.env.cellSize = _classifed_raster_data['raster']

    # set the UAV image info and related data
    _uavimg_data = f.set_image_data(_toolparam['img'])
    arcpy.env.cellSize = _uavimg_data['raster']

    # get the bands within the image
    _uavimg_data.update( { 
        'bands' : f.get_image_bands(_toolparam['img'], BAND_ORDER)
    })

    # create a directory for output tiffs
    _vi_directory = os.path.join(_mapparam['root'], 'vi')
    if(_toolparam['tiff_flag']):
        f.make_dir(_vi_directory)

    # Extract out just the plots from the UAV image
    #_img_extract = sa.extract_plots(_toolparam['img'], _toolparam['plot_lyr'])
    #_out_tiff = _uavimg_data['name_base'] + '_extract.tif'
    #_img_extract.save(os.path.join(_vi_directory, _out_tiff))

    # A dictionary to keep track of index rasters
    vi_raster_data = {}

    # Calculate a vegetative index (VARI)
    if(_toolparam['veg_index'] in ['VARI','ALL']):
        _vari = vi.calcVARI(_uavimg_data['bands'], BAND_ORDER)
        vi_raster_data['vari'] = {
            'index' : 'VARI',
            'raster': _vari,
            'out_tiff': _uavimg_data['name_base'] + '_vari.tif'
        }

    # Calculate a vegetative index (GLI)
    if(_toolparam['veg_index'] in ['GLI','ALL']):
        _gli = vi.calcGLI(_uavimg_data['bands'], BAND_ORDER)
        vi_raster_data['gli'] = {
            'index' : 'GLI',
            'raster': _gli,
            'out_tiff': _uavimg_data['name_base'] + '_gli.tif'
        }


    # Calculate a vegetative index (RGBVI)
    if(_toolparam['veg_index'] in ['RGBVI','ALL']):
        _rgbvi = vi.calcRGBVI(_uavimg_data['bands'], BAND_ORDER)
        vi_raster_data['rgbvi'] = {
            'index' : 'RGBVI',
            'raster': _rgbvi,
            'out_tiff': _uavimg_data['name_base'] + '_rgbvi.tif'
        }


    # Calculate a vegetative index (NGRDI)
    if(_toolparam['veg_index'] in ['NGRDI','ALL']):    
        _ngrdi = vi.calcNGRDI(_uavimg_data['bands'], BAND_ORDER)
        vi_raster_data['ngrdi'] = {
            'index' : 'NGRDI',
            'raster': _ngrdi,
            'out_tiff': _uavimg_data['name_base'] + '_ngrdi.tif'
        }


    #-- This section is responsible for the zonal statistics calculated from a zonal raster            --#
    #-- the zonal raster is created by combining the plot layer (as a raster) with a classifed ratser  --#

    # Create Plot Raster
    _plot_raster_file = os.path.join(_mapparam['scratch'], "plot_ras")
    _plot_data = f.create_plot_raster(_toolparam['plot_lyr'], _toolparam['plot_id_field'], _plot_raster_file, debug=DEBUG)

    # Combine the plot ratser and the classifed raster to create unique zones for the zonal statistics
    _zoneraster_file = os.path.join(_mapparam['scratch'], "zone_ras")
    _zoneraster_data = sa.combine_rasters(_plot_data, _classifed_raster_data, _zoneraster_file, debug=DEBUG)

    # combine the data frames from the plots layer classfied raster to create a lookup df to later merge with the zonal stats tables
    _zone_lookup_df = f.merge_dataframes(_plot_data['df'],
                                         _plot_data['name'],
                                         _classifed_raster_data['df'],
                                         _classifed_raster_data['name_base'],
                                         _zoneraster_data['df'])

    # Calculate the zonal statistics for each VI calculated
    for index, vi_data in vi_raster_data.items():
        _out_statfile = os.path.join(_mapparam['scratch'], "ZStat_" + vi_data['index'])
        vi_raster_data[index].update( { 
            'zonalstat_file': sa.calc_zonalstats(_zoneraster_data['raster'], vi_data, _out_statfile, debug=DEBUG),  
            'zonalstat_df' : f.table_to_data_frame(_out_statfile)
            
        } )
        vi_raster_data[index]['zonalstat_df']['index']= index                 # add a new column to the dataframe and and the veg index


    # combine all the data frames into one 
    _df_list = [vi_raster_data[index]['zonalstat_df'] for index, data in vi_raster_data.items()]
    _zonestat_df = f.combine_dataframes(_df_list)


    # join the plot lookup dataframe to the zonal statistics 
    _zonestat_merge = pd.merge(_zonestat_df, _zone_lookup_df, on='value')


    # clean up some columns
    _dropCol = ['variety','majority', 'minority', 'median', 'pct90', 'count_y']
    _zonestat_merge.drop(columns=_dropCol, axis=1, errors='ignore', inplace=True), 
    _zonestat_merge.sort_values(by=['index','value'], inplace=True)


	# Save the zonal statistics to a table
    _zonestat_merge.to_csv(_toolparam['out_stat_file'].value, index=False)


    # Write the tiffs to disk
    if(_toolparam['tiff_flag']):
        for index, data in vi_raster_data.items():
            outFilePath = os.path.join(_vi_directory, data['out_tiff'])
            tweet("MSG: Saving raster for index ({0})\n  - {1}".format(data['index'], outFilePath), ap=arcpy)
            data['raster'].save(outFilePath)

    tweet("ALL DONE WITH YOUR WORK..SUCCA", ap=arcpy)
