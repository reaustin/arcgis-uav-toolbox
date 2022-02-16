import UAVTools.Functions
import UAVTools.Functions as f
import UAVTools.SpatialAnalysis
import UAVTools.SpatialAnalysis as sa
import UAVTools.ZonalPlotStat
import UAVTools.ZonalPlotStat as zps

import os, sys
import arcpy
from arcpy.sa import ZonalStatisticsAsTable, Combine, ExtractByMask, RasterCalculator
import pandas as pd

from importlib import reload
reload(UAVTools.SpatialAnalysis)
reload(UAVTools.Functions)
reload(UAVTools.ZonalPlotStat)


# ---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
    if(ap is not None):
        ap.AddMessage(msg)
    print(msg)


# Get the tools parameters [plot_lyr, plot_id_field, dsm_base, dsm_list, classified_raster, out_stat_file, tiff_flag]
def get_tool_param():
    param = {}
    for p in arcpy.GetParameterInfo():
        param[p.name] = p.value
    return(param)




if __name__ == '__main__':
   
    DEBUG = False
    VEG_INDEX_DIR = 'dsm'
    volume_data= {}

    # Get the parameters set in the Toolbox and in the current Map
    _toolparam = get_tool_param()
    _mapparam = f.set_arcmap_param()

    # Set the output directory for the geotiffs
    _dsm_directory = os.path.join(_mapparam['root'], VEG_INDEX_DIR)

    # set the raster information for the base surface model
    _dsm_base_data = f.set_raster_data(_toolparam['dsm_base'])
    tweet("MSG: Baseline Digital Surface Model Set\n  -> {0}".format(_dsm_base_data['path']), ap=arcpy)

    # calculate the volumnes from the set of in-season surface models
    #tweet(_toolparam['dsm_list'], ap=arcpy)
   
    # loop through the arcpy Value table pulling out the mapping objects - note it is a list of lists, thus refer to the first item for the raster layer
    for dsm in _toolparam['dsm_list']:
        dsm_data = f.set_raster_data(dsm[0])
        volume_data[dsm_data['name_base']] = { 
            'raster': sa.calc_volume(_dsm_base_data['raster'],dsm_data['raster']),
            'out_tiff': dsm_data['name_base'] + '_vol.tif'  
        }


    #-- This section is responsible for the zonal statistics calculated from a zonal raster            --#
    #-- the zonal raster is created by combining the plot layer (as a raster) with a classifed ratser  --#    
    zps = zps.ZonalPlotStat(_mapparam['scratch'], _toolparam['plot_lyr'], _toolparam['plot_id_field'], _toolparam['classified_raster'])

    zone_stat_data = {}
    for filename, dsm_data in volume_data.items():
        tweet("MSG: Calculating Zonal Statistics\n -> {0}".format(filename), ap=arcpy)
        _out_stat_file = os.path.join(_mapparam['scratch'], filename + '_zs')
        zone_stat_data[filename] = zps.calculate(dsm_data['raster'], _out_stat_file, 'dataset', f.find_date(filename))
  
        


    # combine all the data frames into one 
    _df_list = [zone_stat_data[filename]['df'] for filename, data in zone_stat_data.items()]
    _zonestat_df_all = f.combine_dataframes(_df_list)



    # clean up some columns
    #_dropCol = ['variety','majority', 'minority', 'median', 'pct90', 'count_y']
    #_zonestat_merge.drop(columns=_dropCol, axis=1, errors='ignore', inplace=True), 
    #_zonestat_merge.sort_values(by=['index','value'], inplace=True)


	# Save the zonal statistics to a table
    tweet("MSG: Saving Zonal Statistics\n  -> {0}".format(_toolparam['out_stat_file'].value), ap=arcpy)
    _zonestat_df_all.to_csv(_toolparam['out_stat_file'].value, index=False)

    #tweet(_zonestat_df_all, ap=arcpy)   

    # Write the tiffs to disk - create output file as needed
    if(_toolparam['tiff_flag']):
        f.make_dir(_dsm_directory)        
        for index, data in volume_data.items():
            outFilePath = os.path.join(_dsm_directory, data['out_tiff'])
            tweet("MSG: Saving raster for index ({0})\n  - {1}".format(index, outFilePath), ap=arcpy)
            data['raster'].save(outFilePath)


    zps.cleanup()
    tweet("FINI...", ap=arcpy)        
