import os, sys
import arcpy
from arcpy import Point, Polygon



###---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)

### Get the tools parameters [plotLyr, sliceDir, sliceNum, outPlotLyr]
def getToolParam():
	toolParam = {}
	params	= arcpy.GetParameterInfo()
	for p in params:
		toolParam[p.name] = p.value
	toolParam['toolpath'] = os.path.realpath(__file__)
	return(toolParam)


### Set/Get ArcGIS properties
def setArcMapParam():
	param = {}
	param['project'] = arcpy.mp.ArcGISProject("CURRENT")
	param['maps'] = param['project'].listMaps()[0]
	param['gdb'] = param['project'].defaultGeodatabase
	arcpy.env.overwriteOutput = True 
	param['sr'] = arcpy.SpatialReference(2264)
	return param



def loadPolys(plotLyr, plotId):
	plotPoly = {}
	for row in arcpy.da.SearchCursor(plotLyr, ['OID@', plotId, 'SHAPE@']):
		pts = []
		plotPoly[row[0]] = { 'oid': row[0], 'plotId': row[1], 'pts' : row[2].getPart(0) } 	## just get the outside polygon (no rings)
	return(plotPoly)	



### concert at the Points into PointGeometry for addional functionality
def createPtGeom(poly, sr):
	pts = []
	for p in poly:
		pts.append(arcpy.PointGeometry(p, sr))
	return(pts)



def disBetweenPts(pt1, pt2, mapParam):
	p1Geom = arcpy.PointGeometry(pt1, mapParam['sr'])
	p2Geom = arcpy.PointGeometry(pt2, mapParam['sr'])
	return(p1Geom.distanceTo(p2Geom))



### determine which points in the plot rectange should be used to slice the plot (rectangle)
# - this is based on the sliceDir parameter [Length or Width]
# - the rray indicates the points and their order to use when creating the new plots 
#    -line segment1 uses points 1,4    line segment2 uses 2,3  (Length and distP1P2 > distP1P4)
def getCornersToSlice(polyPtsGeom, direction):
	distP1P2 = abs(polyPtsGeom[0].distanceTo(polyPtsGeom[1]))
	distP1P4 = abs(polyPtsGeom[0].distanceTo(polyPtsGeom[3]))
	tweet("MSG: Distance To Corners: P1 to P2: {0:.2f}, P1 to P4: {1:.2f}".format(distP1P2, distP1P4), ap=arcpy)
	if(direction == 'Width'):
		if(distP1P2 > distP1P4):
			return([1,4,2,3])
		else:
			return([1,2,4,3])
	else:							# assuming direction='Width'
		if(distP1P2 > distP1P4):
			return([1,2,4,3])
		else:
			return([1,4,2,3])		
	



### get the points alone a line that extends from pt1 to pt2 by the number of slices
# - assumes pts are <PointGeometry> type
# - WARNING: For some reason distance is always reporting in meters regardless of spatial reference
def getSlicePoints(pt1, pt2, numSlices):
	slicePts = []
	ang,dist = pt1.angleAndDistanceTo(pt2,'PLANAR')
	dist = dist * (3937/1200)
	#tweet("MSG: Angle and Distanace: angle: {0:.2f}, distance: {1:.2f}".format(ang, dist), ap=arcpy)
	distBetPts = dist / numSlices
	slicePts.append(pt1.getPart(0))
	for s in range(numSlices):
		fromPt1Dist = (s+1) * distBetPts
		slicePts.append(pt1.pointFromAngleAndDistance(ang,fromPt1Dist).getPart(0))		# get the Points from the point geometry object
	return(slicePts)
		

### slice a single polygon into smaller polygons
# - when geting points aong lines it is assumes that the corners contains the correct order to slice along the line (always 0,1 and 2,3)
def slicePoly(toolParam, polyPtsGeom, sr):
	
	lineSegSlicePoints = { 
		1: getSlicePoints(polyPtsGeom[toolParam['corners'][0]], polyPtsGeom[toolParam['corners'][1]], toolParam['sliceNum']),
		2: getSlicePoints(polyPtsGeom[toolParam['corners'][2]], polyPtsGeom[toolParam['corners'][3]], toolParam['sliceNum'])
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



def sliceAllPolys(mapParam, toolParam, plotPoly):
	polyPtsGeom = createPtGeom(plotPoly[1]['pts'], mapParam['sr'])
	toolParam['corners'] = getCornersToSlice(polyPtsGeom, toolParam['sliceDir'])
	tweet("MSG: Sequence of Plot Corners: {0} ".format(toolParam['corners']), ap=arcpy)
	
	slicedPoly = {}
	for oid, p in plotPoly.items():
		#tweet(plotPoly[oid]['pts'], ap=arcpy)
		#tweet(plotPoly[oid]['oid'], ap=arcpy)
		polyPtsGeom = createPtGeom(plotPoly[oid]['pts'], mapParam['sr'])
		slicedPoly[oid] = {
			'oid': oid,
			'plotId': plotPoly[oid]['plotId'],
			'slicePolyGeom': slicePoly(toolParam, polyPtsGeom, mapParam['sr'])
		}
	return(slicedPoly)
	


#### create the new plot layer and add all the new slices plots 	
def createLayer(outParam, slicedPoly, sr):
	tweet("Msg: Creating New Slices Plot Trial Layer...{0} - {1}\n".format(outParam['lyrPath'], outParam['lyrName']), ap=arcpy)
	newlayer = arcpy.management.CreateFeatureclass(outParam['lyrPath'], outParam['lyrName'], "POLYGON", spatial_reference=sr)
	fClass = newlayer[0]		# get the path to the layer 
	arcpy.AddField_management(fClass, outParam['plotId'], "TEXT", field_length=12)	
	arcpy.AddField_management(fClass, outParam['plotIdSlice'], "TEXT", field_length=15)	
	
	with arcpy.da.InsertCursor(fClass, ['SHAPE@', outParam['plotId'], outParam['plotIdSlice']]) as cursor:
		for oid, poly in slicedPoly.items():					 # loop through polygons inserting..
			pid = str(poly['plotId'])							
			sliceNum = 1										 
			for p in poly['slicePolyGeom']:						# each one of the polygon slices
				newId = pid + '-' + str(sliceNum)
				cursor.insertRow([p, pid, newId])	
				sliceNum += 1
	del cursor
	return(fClass)



#### add the plot layer to the data frame
def addLayer(outParam):
	tweet("Loading Plot Layer: {0}".format(outParam['fullPath']), ap=arcpy)
	plotLyr = mapParam['maps'].addDataFromPath(outParam['fullPath'])
	exp = '$feature.' + outParam['plotIdSlice']
	
	#arcpy.management.ApplySymbologyFromLayer(plotLyr, outParam['symLyr'])
	
	for lyr in mapParam['maps'].listLayers():
		# tweet(lyr.name, ap=arcpy)
		if(lyr.name == outParam['lyrName']):
			labelClasses = lyr.listLabelClasses()
			labelClasses[0].expression = exp
			lyr.showLabels = True	


#### set paramters for outputs
def setOutParam(toolParam):
	outParam = {
		'fullPath': toolParam['outPlotLyr'],
		'lyrName': os.path.basename(arcpy.Describe(toolParam['outPlotLyr']).nameString),
		'lyrPath': os.path.dirname(arcpy.Describe(toolParam['outPlotLyr']).nameString),
		'plotId': toolParam['plotId'].value,									# column in original layer to use as main plot id
		'plotIdSlice': toolParam['plotId'].value + 's',							# new column name for sliced polygons
		'symLyr': os.path.join(os.path.dirname(toolParam['toolpath']),'plot.lyrx')
	}
	#tweet(outParam, ap=arcpy)
	return(outParam)


### ============ Main ==================
if __name__ == '__main__':
	
	#### Get the parameters set in the Toolbox and in the Map
	toolParam = getToolParam()
	mapParam = setArcMapParam()
	outParam = setOutParam(toolParam)
	
	### read the plots into a dictionary
	plotPoly = loadPolys(toolParam['plotLyr'], toolParam['plotId'].value)
	
	slicedPoly = sliceAllPolys(mapParam, toolParam, plotPoly)
	
	newLyr = createLayer(outParam, slicedPoly, mapParam['sr'])

	addLayer(outParam)
	
	

