import os,sys
import arcpy
import pandas as pd

# convert a table into a pandas dataframe
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


# clean up a data frame by removeing certain columns 
def clean_zonestat_df(zs_df, drop_columns=['value_y','count_x', 'count_y', 'red', 'green', 'blue']):
    zs_df.drop(columns=drop_columns, inplace=True)
    zs_df.sort_values(by=['value'], inplace=True)



class ZonalPlotStat():

    PLOT_NAME = 'in_memory\\plot_ras'
    CLASSIFIED_RASTER_NAME = 'in_memory\\zone_ras'

    def __init__(self, workspace, plot_layer, plot_id_field, classified_raster=None):
        #self.tweet("Init...", ap=arcpy)
        arcpy.env.overwriteOutput = True
        self.workspace = workspace
        self.plotlyr_data = self.set_plotlyr_data(plot_layer, plot_id_field)

        if(classified_raster is not None):
            self.classified_raster_data = self.set_raster_data(classified_raster)
            self.plot_raster_data = self.create_plot_raster()
            self.zone_raster_data = self.combine_rasters()
            self.zone_raster_data.update( { 'lookup_df': self.merge_dataframes() })
        else:
            pass



    def tweet(self, msg, ap=None):
        if(ap is not None):
            ap.AddMessage(msg)
        print(msg)


    # set informtion about the input plot layer (vector)
    def set_plotlyr_data(self, plot_layer, plot_id_field):
        _lyr_description = arcpy.Describe(plot_layer)
        _plot_data = {
            'lyr' : plot_layer,
            'id_field': plot_id_field.value,
            'path': os.path.join(_lyr_description.path, _lyr_description.nameString)
        }
        return(_plot_data)



    # Set information about the classified raster layer 
    def set_raster_data(self, raster): 
        _raster_description = arcpy.Describe(raster)
        _raster_data = {
            'lyr': raster,
            'raster': arcpy.Raster(_raster_description.nameString), 
            'name' : arcpy.Raster(_raster_description.nameString).name, 
            'name_base': os.path.splitext(arcpy.Raster(_raster_description.nameString).name)[0],
            'path': os.path.join(_raster_description.path,_raster_description.nameString),
            'num_bands': _raster_description.bandCount,
            'has_vat': arcpy.Raster(_raster_description.nameString).hasRAT
        }
        if(_raster_data['has_vat']):
            _raster_data['df'] = table_to_data_frame(_raster_data['path'])
        return(_raster_data) 



    # if there is a classifed raster create the zonal raster using the classes and the plots
    def create_plot_raster(self):
        #self.tweet("MSG: Creating Plot Raster from file...".format(self.plotlyr_data['path']), ap=arcpy)
        arcpy.FeatureToRaster_conversion(self.plotlyr_data['lyr'], self.plotlyr_data['id_field'], self.PLOT_NAME)
        _plotraster_data = {
            'raster': arcpy.Raster(self.PLOT_NAME),
            'id_field': self.PLOT_NAME.split("\\")[-1],
            'df' : table_to_data_frame(self.PLOT_NAME)
        } 
        return(_plotraster_data)



    # combine the plot raster with the classified raster to create a unque zone raster 
    def combine_rasters(self):
        _zoneraster_file = os.path.join(self.workspace, "zone_ras")
        #self.tweet("MSG: Combining Plot Raster with Classified Raster to create Zone Raster...".format(_zoneraster_file), ap=arcpy)
        _combine_raster = arcpy.sa.Combine([self.plot_raster_data['raster'], self.classified_raster_data['raster']])
        _combine_raster.save(_zoneraster_file)
        _zone_data = {
            'raster': arcpy.Raster(_zoneraster_file),
            'path': _zoneraster_file,
            'df': table_to_data_frame(_zoneraster_file)
        }
        return(_zone_data)


    # Merge two dataframes (from vats) to create a new lookup table for the plot and classifed raster combinations
    def merge_dataframes(self):
        #self.tweet("\nMSG: Merging dataframes to create zonal stats lookup table...", ap=arcpy)

        _zone_plot_merge_df = pd.merge(self.zone_raster_data['df'], 
                                        self.plot_raster_data['df'], 
                                        left_on=self.plot_raster_data['id_field'].lower(),
                                        right_on='value'
                                        )
        _zone_plot_merge_df.rename(columns={'value_x': 'value'}, inplace=True)

        _zone_classras_merge_df = pd.merge(_zone_plot_merge_df, 
                                            self.classified_raster_data['df'], 
                                            left_on=self.classified_raster_data['name_base'].lower(), 
                                            right_on='value'
                                            )
        _zone_classras_merge_df.rename(columns={'value_x': 'value'}, inplace=True)

        clean_zonestat_df(_zone_classras_merge_df)
        return(_zone_classras_merge_df)



    # Calculate the statistics by zone using the value_raster 
    #  - adds a column and id to the data frame so that when merged they are unique
    def calculate(self, value_raster, out_stat_file, dataframe_column, dataframe_id):
        arcpy.sa.ZonalStatisticsAsTable(self.zone_raster_data['raster'], 'value', value_raster, out_stat_file, "DATA", "ALL")
        _out_stat_df = table_to_data_frame(out_stat_file)
        _out_stat_df[dataframe_column] = dataframe_id                                                   # add a column and data to the dataframe
        _zonestat_merge = pd.merge(_out_stat_df, self.zone_raster_data['lookup_df'], on='value')       # merge the plot/classified raster lookup table
        _zonal_stats = {
            'path': out_stat_file,
            'df': _zonestat_merge
        }        
        return(_zonal_stats)
