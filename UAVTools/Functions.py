import os, sys
import pandas as pd
import arcpy



# Send a message to the console or ArcGIS Messgae box
def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)



# Get the tools parameters [plot_lyr, img_list, output_folder, buffer_distance]
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


# convert the plot vector layer into a raster and add the assocated data into a dictonary 
def create_plot_raster(plot_lyr, plot_id_field, out_raster_file, debug=False):
	tweet("MSG: Creating Plot Raster \n {0}".format(out_raster_file), ap=arcpy)
	if(not debug):
		arcpy.FeatureToRaster_conversion(plot_lyr, plot_id_field, out_raster_file)				## need to set the cells size to taht of the classRas
	plotData = {
		'lyr' : plot_lyr,
		'raster': arcpy.Raster(out_raster_file),
		'name' : arcpy.Raster(out_raster_file).name,
		'id_field' : plot_id_field.value,
		'path' : out_raster_file,
		'df' : table_to_data_frame(out_raster_file)
	}
	return(plotData)



# Set information about a classifed raster 
def set_classifed_raster_data(classified_raster):
	_img_dsc = arcpy.Describe(classified_raster)
	_class_img = {
		'lyr': classified_raster,
		'raster': arcpy.Raster(_img_dsc.nameString), 
		'name' : arcpy.Raster(_img_dsc.nameString).name, 
		'name_base': os.path.splitext(arcpy.Raster(_img_dsc.nameString).name)[0],
		'path': os.path.join(_img_dsc.path,_img_dsc.nameString),
		'num_bands': _img_dsc.bandCount,
		'has_vat': arcpy.Raster(_img_dsc.nameString).hasRAT
	}
	if(_class_img['has_vat']):
		_class_img['df'] = table_to_data_frame(_class_img['path'])
		
	return(_class_img)



# Set information about an image
def set_image_data(image):
    _imgDsc = arcpy.Describe(image)
    _img_dict = {
        'lyr': image,
        'raster': arcpy.Raster(_imgDsc.nameString),
        'name': arcpy.Raster(_imgDsc.nameString).name,
        'name_base': os.path.splitext(arcpy.Raster(_imgDsc.nameString).name)[0],
        'path': os.path.join(_imgDsc.path, _imgDsc.nameString),
        'num_bands': _imgDsc.bandCount,
        'has_vat': arcpy.Raster(_imgDsc.nameString).hasRAT
    }
    return(_img_dict)



# Set information about a raster layer 
def set_raster_data(raster):
	_img_dsc = arcpy.Describe(raster)
	_raster_data = {
		'lyr': raster,
		'raster': arcpy.Raster(_img_dsc.nameString), 
		'name' : arcpy.Raster(_img_dsc.nameString).name, 
		'name_base': os.path.splitext(arcpy.Raster(_img_dsc.nameString).name)[0],
		'path': os.path.join(_img_dsc.path,_img_dsc.nameString),
		'num_bands': _img_dsc.bandCount,
		'has_vat': arcpy.Raster(_img_dsc.nameString).hasRAT
	}
	if(_raster_data['has_vat']):
		_raster_data['df'] = table_to_data_frame(_raster_data['path'])
	return(_raster_data)



# Set information about a vector layer 
def set_layer_data(layer):
	_layer_description = arcpy.Describe(layer)
	_layer_data = {
		'lyr': layer,
		'name' : _layer_description.nameString,
		'path': os.path.join(_layer_description.path,_layer_description.nameString),
		'feature_class': _layer_description.featureClass
	}
	return(_layer_data)



# set information about a layer in memory
def set_memory_layer_data(memory_layer):
	_memory_layer_data = {
		'lyr': memory_layer,
		'name' : memory_layer.nameString
	}
	return(_memory_layer_data)



# get the full paths names to each band and assign a varable to use in the Raster Calculator
def get_image_bands(uav_imgage, band_order):
    _imgDsc = arcpy.Describe(uav_imgage)
    _img = {}
    for i, band in enumerate(_imgDsc.children):
        _img[i] = {
            'path': os.path.join(_imgDsc.catalogPath, band.name),
            'raster': arcpy.Raster(os.path.join(_imgDsc.catalogPath, band.name)),
            'name': band.name,
            'color': band_order[i]
        }
    return(_img)



# check the number of bands in a raster
def check_bands(img, band_number):
	_bands = arcpy.Describe(img).bandCount
	if(_bands == band_number):
		return(True)
	else:
		return(False)	



### convert a table into a pandas dataframe
def table_to_data_frame(in_table, input_fields=None, where_clause=None):
    OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_table)]
    data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    return(fc_dataframe.rename(columns=str.lower))



### clean up tey data frame by removeing pixel counts and other unneeded columns
# def clean_zonestat_df(zs_df):
# 	dropCol = ['value_y','count_x', 'count_y', 'red', 'green', 'blue']
# 	zs_df.drop(columns=dropCol, inplace=True)
# 	zs_df.sort_values(by=['value'], inplace=True)



# clean up a data frame by removeing certain columns 
def clean_zonestat_df(zs_df, drop_columns=['value_y','count_x', 'count_y', 'red', 'green', 'blue'], sort_by=None):
	zs_df.drop(columns=drop_columns, axis=1, errors='ignore', inplace=True)
	if(sort_by is not None):
		zs_df.sort_values(by=sort_by, inplace=True)



### Merge two dataframes (from vats) to create a new lookup table for the plot and classifed raster combinations
def merge_dataframes(plot_df, plot_id_field, classifed_raster_df, classifed_id_field, zoneraster_df):
	tweet("MSG: Merging dataframes to create zonal stats lookup table...", ap=arcpy)
	_zone_plot_merge_df = pd.merge(zoneraster_df, plot_df, left_on=plot_id_field.lower(), right_on='value')
	_zone_plot_merge_df.rename(columns={'value_x': 'value'}, inplace=True)
	_zone_classras_merge_df = pd.merge(_zone_plot_merge_df, classifed_raster_df, left_on=classifed_id_field.lower(), right_on='value')
	_zone_classras_merge_df.rename(columns={'value_x': 'value'}, inplace=True)
	clean_zonestat_df(_zone_classras_merge_df)
	return(_zone_classras_merge_df)



### combine datafarmes intro a single dataframe
def combine_dataframes(df_list):
	_df_all = pd.DataFrame()
	for df in df_list:
		_df_all = _df_all.append(df)
	return(_df_all)



# Make a new directory for storing tiff,
def make_dir(new_dir):
    tweet('MSG: Making directory \n  - {0}'.format(new_dir), ap=arcpy)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
        return(new_dir)
    else:
        return(None)



# Set the band order based on the number of bands in the image (taking a best guess here)
def set_band_order(num_bands=3):
	if(num_bands == 3):
		return(['R', 'G', 'B'])						# assuming p4 RGB image
	if(num_bands == 5):
		return(['B', 'G', 'R', 'RE', 'NIR'])		# assuming rededge 
	if(num_bands == 6):
		return(['B', 'G', 'R', 'RE', 'NIR', 'LWIR']) 		# assuming altum
	return(None)



# look for a 8 digit date in a string (i.e. filename) that is separated by underscores
def find_date(filename):
	str_list = filename.split('_')
	for i in str_list:
		if(len(i) == 8 and i.isdecimal()):
			return(i)
	return(filename)


# print a dictioary nicely 
def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))