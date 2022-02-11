import UAVTools.Functions
import UAVTools.Functions as f
import UAVTools.SpatialAnalysis as sa
import UAVTools.SpatialAnalysis
import UAVTools.VegIndex as vi
from ipaddress import v4_int_to_packed
import os
import sys
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


# Set/Get ArcGIS properties
def set_arcmap_param():
    _prj = arcpy.mp.ArcGISProject("CURRENT")
    param = {
        'project': _prj,
        'maps':  _prj.listMaps()[0],
        'gdb':  _prj.defaultGeodatabase,
        'root':  os.path.dirname(_prj.filePath),
        #'scratch': "C:/temp/scratch/"
        'scratch':  arcpy.env.scratchGDB
    }
    arcpy.env.overwriteOutput = True
    return(param)


# Make a new directory for storing tiff,
def make_dir(new_dir):
    tweet('MSG: Making directory \n  - {0}'.format(new_dir), ap=arcpy)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
        return(new_dir)
    else:
        return(None)


# Set information about a raster or imaage
def set_raster_info(raster):
    _imgDsc = arcpy.Describe(raster)
    img_dict = {
        'lyr': raster,
        'raster': arcpy.Raster(_imgDsc.nameString),
        'name': arcpy.Raster(_imgDsc.nameString).name,
        'name_base': os.path.splitext(arcpy.Raster(_imgDsc.nameString).name)[0],
        'path': os.path.join(_imgDsc.path, _imgDsc.nameString),
        'num_bands': _imgDsc.bandCount,
        'has_vat': arcpy.Raster(_imgDsc.nameString).hasRAT
    }
    if(img_dict['has_vat']):
        img_dict['df'] = table_to_data_frame(img_dict['path'])

    return(img_dict)


# convert a table into a pandas dataframe
def table_to_data_frame(in_table, input_fields=None, where_clause=None):
    OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_table)]
    data = [row for row in arcpy.da.SearchCursor(
        in_table, final_fields, where_clause=where_clause)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    return fc_dataframe


# get the fill paths names to each band and assign a varable to use in the Raster Calculator
def get_img_bands(uav_img, band_order):
    _imgDsc = arcpy.Describe(uav_img)
    img = {}
    for i, band in enumerate(_imgDsc.children):
        img[i] = {
            'path': os.path.join(_imgDsc.catalogPath, band.name),
            'raster': arcpy.Raster(os.path.join(_imgDsc.catalogPath, band.name)),
            'name': band.name,
            'color': band_order[i]
        }
    return(img)


# Set all the picels of the UAV image outside the plot bounadries to null
def extractPlots(uav_image, plot_lyr):
    tweet('MSG: Extracting UAV image using plot layer...', ap=arcpy)
    return(ExtractByMask(uav_image, plot_lyr))


def compositeRasters(raster_list, out_ratser):
    arcpy.CompositeBands_management(raster_list, out_ratser)


# Calculate the statistics by zone (i.e. the zones are a combination of plots and classified raster)
def calc_zonalstats(zone_raster, vi_raster_data, out_stat_file, debug=False):
    tweet('MSG: Calculating Zonal Statistics ({0}) \n - {1}'.format(vi_raster_data['index'], out_stat_file), ap=arcpy)
    _imgDsc = arcpy.Describe(vi_raster_data['raster'])
    if(not debug):
        ZonalStatisticsAsTable(zone_raster, 'value', vi_raster_data['raster'], out_stat_file, "DATA", "ALL")

    return(out_stat_file)


if __name__ == '__main__':

    DEBUG = False
    BAND_ORDER = ['R', 'G', 'B']

    # Get the parameters set in the Toolbox and in the current Map
    _toolparam = get_tool_param()
    _mapparam = set_arcmap_param()

    # set UAV Image and related data
    _classifed_raster_data = f.set_classifed_raster(_toolparam['classified_img'])

    # set the UAV image info and related data
    _uavimg_info = set_raster_info(_toolparam['img'])
    arcpy.env.cellSize = _uavimg_info['raster']

    # get the bands within the image
    _uav_img_info = get_img_bands(_toolparam['img'], BAND_ORDER)

    # create a directory for output tiffs
    _vi_directory = os.path.join(_mapparam['root'], 'vi')
    if(_toolparam['tiff_flag']):
        make_dir(_vi_directory)

    # Extract out just the plots from the UAV image
    #_img_extract = extractPlots(_toolparam['img'], _toolparam['plot_lyr'])
    #_out_tiff = _uavimg_info['name_base'] + '_extract.tif'
    #_img_extract.save(os.path.join(_vi_directory, _out_tiff))

    # A dictionary to keep track of index rasters
    vi_raster_data = {}

    # Calculate a vegetative index (VARI)
    if(_toolparam['veg_index'] in ['VARI','ALL']):
        _vari = vi.calcVARI(_uavimg_info['raster'])
        vi_raster_data['vari'] = {
            'index' : 'VARI',
            'raster': _vari,
            'out_tiff': _uavimg_info['name_base'] + '_vari.tif'
        }

    # Calculate a vegetative index (GLI)
    if(_toolparam['veg_index'] in ['GLI','ALL']):
        _gli = vi.calcGLI(_uav_img_info, BAND_ORDER)
        vi_raster_data['gli'] = {
            'index' : 'GLI',
            'raster': _gli,
            'out_tiff': _uavimg_info['name_base'] + '_gli.tif'
        }


    # Calculate a vegetative index (RGBVI)
    if(_toolparam['veg_index'] in ['RGBVI','ALL']):
        _rgbvi = vi.calcRGBVI(_uav_img_info, BAND_ORDER)
        vi_raster_data['rgbvi'] = {
            'index' : 'RGBVI',
            'raster': _rgbvi,
            'out_tiff': _uavimg_info['name_base'] + '_rgbvi.tif'
        }


    # Calculate a vegetative index (NGRDI)
    if(_toolparam['veg_index'] in ['NGRDI','ALL']):    
        _ngrdi = vi.calcNGRDI(_uav_img_info, BAND_ORDER)
        vi_raster_data['ngrdi'] = {
            'index' : 'NGRDI',
            'raster': _ngrdi,
            'out_tiff': _uavimg_info['name_base'] + '_ngrdi.tif'
        }

    # Create a raster composite of all the vi rasters
    # _vi_rasters_list = [vi_raster[index]['raster'] for index, data in vi_raster.items()]
    # tweet(_vi_rasters_list, ap=arcpy)
    # _out_tiff = os.path.join(_vi_directory, _uavimg_info['name_base'] + '_composite.tif')
    # tweet("MSG: Creating Composite Raster...\n  - {0}".format(_out_tiff), ap=arcpy)
    # _composite = compositeRasters(_vi_rasters_list, _out_tiff)

    # This section is responsible for the zonal statistics based on a zonal raster

    # Create Plot Raster
    _plot_raster_file = os.path.join(_mapparam['scratch'], "plot_ras")
    _plot_data = f.create_plot_raster(_toolparam['plot_lyr'], _toolparam['plot_id_field'], _plot_raster_file, debug=DEBUG)

    
    #arcpy.env.cellSize = classImg['raster']

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
        tweet(vi_data['index'], ap=arcpy)
        _out_statfile = os.path.join(_mapparam['scratch'], "ZStat_" + vi_data['index'])
        _out_zonestat = calc_zonalstats(_zoneraster_data['raster'], vi_data, _out_statfile, debug=DEBUG)        



    #### Convert the geodatbase tables into pandas dataframes and add a 'df' key to the zone stats dictionary
	#createDataFrames(zoneStat)


    # Write the tiffs to disk
    if(_toolparam['tiff_flag']):
        for index, data in vi_raster_data.items():
            outFilePath = os.path.join(_vi_directory, data['out_tiff'])
            tweet("MSG: Saving raster for index ({0})\n  - {1}".format(data['index'], outFilePath), ap=arcpy)
            data['raster'].save(outFilePath)

    tweet("ALL DONE WITH YOUR WORK..SUCCA", ap=arcpy)
