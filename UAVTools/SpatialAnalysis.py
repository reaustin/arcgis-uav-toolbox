import arcpy
from arcpy.sa import ZonalStatisticsAsTable, Combine, ExtractByMask, RasterCalculator 

from UAVTools.Functions import tweet, create_plot_raster, table_to_data_frame




### combine the plot layer with the classified raster to create a unque combination of zones within each plot
def combine_rasters(plot_data, classified_raster_data, output_file, debug=False):
	tweet("MSG: Combining Rasters \n  -{0} \n  -{1}".format(plot_data['path'], classified_raster_data['path']), ap=arcpy)
	if(not debug):
		combineRaster = Combine([plot_data['raster'], classified_raster_data['raster']])
		combineRaster.save(output_file)
	_zone_raster_data = {
		'raster': arcpy.Raster(output_file),
		'path' : output_file,
		'df' : table_to_data_frame(output_file)
	}
	return(_zone_raster_data)



# Calculate the statistics by zone (i.e. the zones are a combination of plots and classified raster)
def calc_zonalstats(zone_raster, vi_raster_data, out_stat_file, debug=False):
    tweet('MSG: Calculating Zonal Statistics ({0}) \n - {1}'.format(vi_raster_data['index'], out_stat_file), ap=arcpy)
    _imgDsc = arcpy.Describe(vi_raster_data['raster'])
    if(not debug):
        ZonalStatisticsAsTable(zone_raster, 'value', vi_raster_data['raster'], out_stat_file, "DATA", "ALL")

    return(out_stat_file)



# create a composite ratser from a lisy of input rasters
def composite_rasters(raster_list, out_ratser):
    arcpy.CompositeBands_management(raster_list, out_ratser)
    return(out_ratser)



# clip out the plot areas from the UAV image 
def extract_plots(uav_image, plot_lyr):
    tweet('MSG: Extracting UAV image using plot layer.. \n  - img:{0} \n  - plots:{1}'.format(uav_image, plot_lyr), ap=arcpy)
    return(ExtractByMask(uav_image, plot_lyr))



# subtract two layers from one another resulting in a difference surface
def calc_volume(base_raster, surface_raster):
    tweet('MSG: Calculating difference between surface rasters..', ap=arcpy)
    _out_ras = RasterCalculator([base_raster, surface_raster], 
                                ['BASE','SURFACE'], 
                                'SURFACE - BASE'
                                )
    return(_out_ras)