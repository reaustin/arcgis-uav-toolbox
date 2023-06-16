import UAVTools.Functions
import UAVTools.Functions as f

import os, sys
import arcpy
from arcpy import Point, Polygon

from importlib import reload
reload(UAVTools.Functions)


def load_polys(plot_layer, plot_id_field):
	_plot_poly = {}
	for row in arcpy.da.SearchCursor(plot_layer, ['OID@', plot_id_field, 'SHAPE@']):
		_pts = []
		_plot_poly[row[0]] = { 				## just get the outside polygon (no rings)
			'oid': row[0], 
			'plotId': row[1], 
			'pts' : row[2].getPart(0) 
			} 	
	return(_plot_poly)	



### concert at the Points into PointGeometry for addional functionality
def create_point_geometry(poly, sr):
	_pts = []
	for p in poly:
		_pts.append(arcpy.PointGeometry(p, sr))
	return(_pts)



def disBetweenPts(pt1, pt2, mapParam):
	p1Geom = arcpy.PointGeometry(pt1, mapParam['sr'])
	p2Geom = arcpy.PointGeometry(pt2, mapParam['sr'])
	return(p1Geom.distanceTo(p2Geom))



### determine which points in the plot rectangle should be used to slice the plot (rectangle)
# - this is based on the sliceDir parameter [Length or Width]
# - the rray indicates the points and their order to use when creating the new plots 
#    -line segment1 uses points 1,4    line segment2 uses 2,3  (Length and distP1P2 > distP1P4)
def get_corners_to_slice(polygon_pt_geometry, direction):
	distP1P2 = abs(polygon_pt_geometry[0].distanceTo(polygon_pt_geometry[1]))
	distP1P4 = abs(polygon_pt_geometry[0].distanceTo(polygon_pt_geometry[3]))
	#f.tweet("MSG: Distance To Corners: P1 to P2: {0:.2f}, P1 to P4: {1:.2f}".format(distP1P2, distP1P4), ap=arcpy)

	# if the shape is a square use Width (can fixed later to direction of trial)
	_dif_in_length = abs(distP1P4 - distP1P4)
	#f.tweet("MSG: Length Difference: {0:.5f}".format(_dif_in_length), ap=arcpy)
	
	# if it is a squure, always split along the same direction (need to fix this assumption)
	if(_dif_in_length < 0.01):
		return([1,4,2,3])
	
	if(direction == 'Width'):
		if(distP1P2 > distP1P4):
			return([1,4,2,3])
		else:
			return([1,2,4,3])
	else:							# assuming direction='Length'
		if(distP1P2 > distP1P4):
			return([1,2,4,3])
		else:
			return([1,4,2,3])		
	



### get the points alone a line that extends from pt1 to pt2 by the number of slices
# - assumes pts are <PointGeometry> type
def getSlicePoints(pt1, pt2, numSlices):
	slicePts = []
	ang,dist = pt1.angleAndDistanceTo(pt2,'PLANAR')
	#f.tweet("MSG: Angle and Distanace: angle: {0:.2f}, distance: {1:.2f}".format(ang, dist), ap=arcpy)
	distBetPts = dist / numSlices
	
	slicePts.append(pt1.getPart(0))
	for s in range(numSlices):
		fromPt1Dist = (s+1) * distBetPts
		#f.tweet(fromPt1Dist, ap=arcpy)
		slicePts.append(pt1.pointFromAngleAndDistance(ang,fromPt1Dist,'PLANAR').getPart(0))		# get the Points from the point geometry object

	return(slicePts)
		

### slice a single polygon into smaller polygons
# - when geting points along lines it is assumes that the corners contains the correct order to slice along the line (always 0,1 and 2,3)
def slicePoly(corners, poly_geom, num_slices, sr):
	
	lineSegSlicePoints = { 
		1: getSlicePoints(poly_geom[corners[0]], poly_geom[corners[1]], num_slices),
		2: getSlicePoints(poly_geom[corners[2]], poly_geom[corners[3]], num_slices)
	}
			
	
	### create an array of new Polygon features that are the sliced based on the parallel line segments
	newPolys = []
	for i in range(len(lineSegSlicePoints[1])-1):
		ul = lineSegSlicePoints[1][i]
		ur = lineSegSlicePoints[2][i]
		ll = lineSegSlicePoints[1][i+1]
		lr = lineSegSlicePoints[2][i+1]
		poly = Polygon(arcpy.Array([ul,ur,lr,ll]),sr)
		newPolys.append(poly)
	
	return(newPolys)

  
  

#### add the plot layer to the data frame
def add_layer_to_map(arcmap_paramters, output_data):
	f.tweet("Loading Plot Layer: {0}".format(output_data['slice_layer_path']), ap=arcpy)
	_full_path_to_slice_layer = os.path.join(output_data['slice_layer_path'],output_data['slice_layer_name'])
	plotLyr = arcmap_paramters['maps'].addDataFromPath(_full_path_to_slice_layer)
	exp = '$feature.' + output_data['slice_id_field']
	
	#arcpy.management.ApplySymbologyFromLayer(plotLyr, output_parameters['symLyr'])
	
	for lyr in arcmap_paramters['maps'].listLayers():
		# tweet(lyr.name, ap=arcpy)
		if(lyr.name == output_data['slice_layer_name']):
			labelClasses = lyr.listLabelClasses()
			labelClasses[0].expression = exp
			lyr.showLabels = False	


#### set paramters for outputs
def set_output_data(tool_parameters):
	#_layer_description = arcpy.Describe(tool_parameters['out_plot_layer'])
	_out_param = {
		'slice_layer': tool_parameters['out_plot_layer'],
		'slice_layer_name': os.path.basename(tool_parameters['out_plot_layer'].value),
		'slice_layer_path': os.path.dirname(tool_parameters['out_plot_layer'].value),									
		'slice_id_field': 'Row'											# new column name for sliced polygons
		#'symLyr': os.path.join(os.path.dirname(os.path.realpath(__file__)),'plot.lyrx')
	}
	#f.tweet(_out_param, ap=arcpy)
	return(_out_param)



def slice_all_polygons(map_param, tool_param, plot_polygons):	
	slicedPoly = {}
	for oid, p in plot_polygons.items():
		_polygon_point_geometry = create_point_geometry(plot_polygons[oid]['pts'], map_param['sr'])
		_slice_corners = get_corners_to_slice(_polygon_point_geometry, tool_param['slice_direction'])
		#f.tweet("MSG: Sequence of Plot Corners: {0} ".format(_slice_corners), ap=arcpy)
		#f.tweet(_polygon_point_geometry[0].firstPoint, ap=arcpy)
		#sys.exit()
		slicedPoly[oid] = {
			'oid': oid,
			'plot_id': plot_polygons[oid]['plotId'],
			'slice_polygon_geometry': slicePoly(_slice_corners, _polygon_point_geometry, tool_param['slice_number'], map_param['sr'])
		}
	return(slicedPoly)



#### create the new slices plot layer and add all the new slices plots 	
def create_layer(sliced_polygons, sr, output_data, tool_param):
	f.tweet("Msg: Creating New Slices Plot Trial Layer...{0} - {1}\n".format(output_data['slice_layer_path'], output_data['slice_layer_name']), ap=arcpy)
	newlayer = arcpy.management.CreateFeatureclass(output_data['slice_layer_path'], output_data['slice_layer_name'], "POLYGON", spatial_reference=sr)
	fClass = newlayer[0]		# get the path to the layer 
	arcpy.AddField_management(fClass, tool_param['plot_layer_id'].value, "TEXT", field_length=12)	
	arcpy.AddField_management(fClass, output_data['slice_id_field'], "LONG")
			
	with arcpy.da.InsertCursor(fClass, ['SHAPE@', tool_param['plot_layer_id'].value, output_data['slice_id_field']]) as cursor:
		for oid, poly in sliced_polygons.items():					 # loop through polygons inserting..
			pid = str(poly['plot_id'])							
			sliceNum = 1										 
			for p in poly['slice_polygon_geometry']:						# each one of the polygon slices
				#newId = pid + '-' + str(sliceNum)
				newId = sliceNum
				cursor.insertRow([p, pid, newId])	
				sliceNum += 1
	del cursor
	return(fClass)


# add a field to the sliced polygon layer';s attribute table so as to group slices within polygons (i.e. treatments)
def add_grouping_field(sliced_layer, field_to_slice_on, sliced_field_id, number_to_group):
	arcpy.AddField_management(sliced_layer, sliced_field_id, "LONG")

	_max_slice_value = max([cur[0] for cur in arcpy.da.SearchCursor(sliced_layer, field_to_slice_on)])
	f.tweet("Maximum Row Value: {0}".format(_max_slice_value), ap=arcpy) 

	if(_max_slice_value % number_to_group != 0):
		arcpy.AddWarning("Can't split {0} rows evenly with {1} groupings".format(_max_slice_value, number_to_group)) 
	else:
		f.tweet("Adding and calculating Field: {0}".format(sliced_field_id), ap=arcpy) 
		_expres = 'int((!row!-1)/{0}) + 1'.format(number_to_group)
		arcpy.CalculateField_management(sliced_layer, sliced_field_id, _expres, "PYTHON3")




### ============ Main ==================
if __name__ == '__main__':
	
	# Get the parameters set in the Toolbox and in the current Map
	#  - [plot_layer, plot_layer_id, slice_direction, slice_number, out_plot_layer, number_to_group, field_name 
	_toolparam = f.get_tool_param()
	_mapparam = f.set_arcmap_param()  

	# add a specfic spatial reference (need to fix at some point)
	_mapparam['sr'] = arcpy.SpatialReference(2264)
	#_mapparam['sr'] = arcpy.Describe(_toolparam['plot_layer']).SpatialReference

	# set the output data
	_output_data = set_output_data(_toolparam)

	# read the plots into a dictionary
	_plot_poly_data = load_polys(_toolparam['plot_layer'], _toolparam['plot_layer_id'].value)

	# slice the polygons 
	_sliced_polygons = slice_all_polygons(_mapparam, _toolparam, _plot_poly_data)

	# create and sav ethe new sliced layer
	_new_sliced_layer = create_layer(_sliced_polygons, _mapparam['sr'], _output_data, _toolparam)

	#sys.exit()
	#_new_sliced_layer = arcpy.MakeFeatureLayer_management(os.path.join(_mapparam['gdb'], 'PlotSlice'),"slice_layer")
	
	if(_toolparam['number_to_group'] > 0 and _toolparam['field_name'] is not None):
		add_grouping_field(_new_sliced_layer, _output_data['slice_id_field'], _toolparam['field_name'], _toolparam['number_to_group'])

	f.tweet("ALL SLICED UP LIKE A NINJI...", ap=arcpy)

	#add_layer_to_map(_mapparam, _output_data)
	
	

