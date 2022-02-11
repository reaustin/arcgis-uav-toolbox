import os, sys
import pandas as pd
import arcpy


def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)



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



def set_classifed_raster(classified_raster):
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
def clean_zonestat_df(zs_df):
	dropCol = ['value_y','count_x', 'count_y', 'red', 'green', 'blue']
	zs_df.drop(columns=dropCol, inplace=True)
	zs_df.sort_values(by=['value'], inplace=True)



### Merge two dataframes (from vats) to create a new lookup table for the plot and classifed raster combinations
def merge_dataframes(plot_df, plot_id_field, classifed_raster_df, classifed_id_field, zoneraster_df):
	tweet("MSG: Merging dataframes to create zonal stats lookup table...", ap=arcpy)
	_zone_plot_merge_df = pd.merge(zoneraster_df, plot_df, left_on=plot_id_field.lower(), right_on='value')
	_zone_plot_merge_df.rename(columns={'value_x': 'value'}, inplace=True)
	_zone_classras_merge_df = pd.merge(_zone_plot_merge_df, classifed_raster_df, left_on=classifed_id_field.lower(), right_on='value')
	_zone_classras_merge_df.rename(columns={'value_x': 'value'}, inplace=True)
	clean_zonestat_df(_zone_classras_merge_df)
	return(_zone_classras_merge_df)

