from re import I
import UAVTools.Functions
import UAVTools.Functions as f

import os, sys
import arcpy
import pprint
pp = pprint.PrettyPrinter(indent=4)

from importlib import reload
reload(UAVTools.Functions)



def get_polygon_centroids(plot_layer, plot_label_field):
	_plot_centers = {}
	for row in arcpy.da.SearchCursor(plot_layer, ['OID@', plot_label_field.value, 'SHAPE@XY']):
		_pts = []
		_plot_centers[row[0]] = { 				## just get the outside polygon (no rings)
			'oid': row[0], 
			'plot_label_field': row[1], 
			'centroid_x' : row[2][0],
            'centroid_y' : row[2][1],
			} 	
	return(_plot_centers)	    



def reorder_by_plot_centers(plot_centers, order):
    if(order == 'North to South'):
        return(sorted(plot_centers.items(), key = lambda x: x[1]['centroid_y'], reverse=True))
    if(order == 'South to North'):    
        return(sorted(plot_centers.items(), key = lambda x: x[1]['centroid_y']))
    if(order == 'East to West'):    
        return(sorted(plot_centers.items(), key = lambda x: x[1]['centroid_x'], reverse=True))
    if(order == 'West to East'):    
        return(sorted(plot_centers.items(), key = lambda x: x[1]['centroid_x']))        




def add_label_to_field(plot_layer, plot_label_field, sorted_labels, increment_tuple):
	_field_type = get_field_type(plot_layer, plot_label_field.value)
	with arcpy.da.UpdateCursor(plot_layer, ['OID@', plot_label_field.value]) as cursor:
		#f.tweet(cursor.fields, ap=arcpy)
		for i, row in enumerate(cursor):
			_oid = row[0]
			_new_plot_label = sorted_labels[_oid]['label']
			if(_field_type == 'String'):
				_new_plot_label = str(_new_plot_label)
			if(_field_type == 'Integer'):
				_new_plot_label = int(_new_plot_label)	
			row[1] = _new_plot_label
			cursor.updateRow(row)
	del cursor	    



# add the new label to the plot centers dictionary
def add_label_values(sorted_labels, increment_tuple):
	_current_label = increment_tuple[0]
	for i, data in enumerate(sorted_labels):
		#f.tweet(data[1], ap=arcpy) 
		data[1]['label'] = _current_label
		_current_label += increment_tuple[1]	


# convert the sorted dictonary (list) back into a dictonary
def unlist_dictionary(d):
	_out = {}
	for i, data in enumerate(d):
		_out[data[1]['oid']] = data[1]
	return(_out)	


# get the field data type
def get_field_type(layer, field_name):
	field = arcpy.ListFields(_toolparam['plot_layer'], _toolparam['plot_label_field'])[0]
	return(field.type)


if __name__ == '__main__':

    # Get the parameters set in the Toolbox/Map 
    #  - [plot_layer, plot_label_field, direction, start_label, increment]
	_toolparam = f.get_tool_param()
	_mapparam = f.set_arcmap_param()    

    # load in the centers of the plot polygons (used to order by location) 
	_plot_centers = get_polygon_centroids(_toolparam['plot_layer'], _toolparam['plot_label_field'])

    # order the plots based on the user input direction
	_plot_centers_sorted = reorder_by_plot_centers(_plot_centers, _toolparam['direction'])

    # add the data to the field indicted by the user
    # for i, data in enumerate(_plot_centers_sorted):
    #      f.tweet(_plot_centers_sorted[i][1]['oid'], ap=arcpy)     
    
	# add the new label to the plot centers dictionary
	_increment_tuple = (_toolparam['start_label'], _toolparam['increment'])
	add_label_values(_plot_centers_sorted, _increment_tuple)
	
	# _out = pretty(_plot_centers_sorted, 2)
	# f.tweet(_out, ap=arcpy) 

	# get ride of the list and get back to a dictionary
	_plot_labels = unlist_dictionary(_plot_centers_sorted)

    # add the label to the user specifed field
	add_label_to_field(_toolparam['plot_layer'], _toolparam['plot_label_field'], _plot_labels, _increment_tuple)

	f.tweet("YOU'RE LABELED...", ap=arcpy) 

