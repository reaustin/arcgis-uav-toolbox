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
