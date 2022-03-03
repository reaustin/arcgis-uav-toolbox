import os, sys
import arcpy
from arcpy import Point, Polygon, Polyline
import pdb


#====== SUPORT FUNCTIONS =======#

def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)


def setArcMapParam():
	param = {}
	param['project'] = arcpy.mp.ArcGISProject("CURRENT")
	param['maps'] = param['project'].listMaps()[0]
	arcpy.env.overwriteOutput = True 
	#param['sr'] = arcpy.SpatialReference(2264)
	param['map_sr'] = param['maps'].spatialReference
	param['meters_per_unit'] = param['map_sr'].metersPerUnit
	return param




def ScriptTool(param):
	#tweet(param, ap=arcpy)
	#pdb.set_trace()
	return


#### Calculate angle from two points. (Zero is East) 
# - uses ArcPy point objects
# - flip will calculate from second to first vertex (opposite)
def calcAngle(pt1, pt2, flip=False):
	if(flip):
		pt1, pt2 = pt2, pt1
	rotAngle = math.degrees(math.atan2((pt2.Y-pt1.Y),(pt2.X-pt1.X)))    
	tweet("Rotating: {0}".format(rotAngle), ap=arcpy)
	return(rotAngle)


#### Get the upper left hand corner of a plot (x,y) pair based on column and row
# - x and y are based off 0,0 orgin at this point in the code
def getPlot_ll(column, row, tInfo):
	llx = tInfo['BoarderDim'][0] + ((column-1)*tInfo['AlleyDim'][0]) + ((column-1)*tInfo['plotSize'][0])
	lly = tInfo['BoarderDim'][1] + ((row-1)*tInfo['AlleyDim'][1]) + ((row-1)*tInfo['plotSize'][1])
	return([llx, lly])
	
	

#### given the upper left corner, return the plot as a Polgon object
def getPlotPoly(llx, lly, plotSize, spatialRef):
	ll = Point(llx, lly)
	ul = Point(llx+plotSize[0], lly)
	ur = Point(llx+plotSize[0], lly+plotSize[1])
	lr = Point(llx, lly+plotSize[1])
	return(Polygon(arcpy.Array([ll,ul,ur,lr]),spatialRef))	
	

#### rotate all plots around specifid orgin (centerPt = center of rotation)
def rotatePlots(trial, centerPt, angle): 
	#angle = angle * -1
	tweet("Rotating Trial:  Angle: {0}".format(angle), ap=arcpy)
	tweet("Rotation Point:  X: {0}, Y: {1}".format(centerPt.X, centerPt.Y), ap=arcpy)
	angleRad = math.radians(angle)
	
	for p in trial['plots']:
		#tweet(trial['plots'][p], ap=arcpy)
		polyGeom = trial['plots'][p]
		rotArray = []
		for segment in polyGeom.getPart():
			for pt in segment:
				x = pt.X - centerPt.X
				y = pt.Y - centerPt.Y 
				xr = (x * math.cos(angleRad)) - (y * math.sin(angleRad)) + centerPt.X
				yr = (x * math.sin(angleRad)) + (y * math.cos(angleRad)) + centerPt.Y
				rotArray.append(Point(xr,yr))				
		
		trial['plots'][p] = Polygon(arcpy.Array(rotArray))				# overwrite polgon with rotated coordinates
	
	
	
#### move all the plots by shiting in the X and Y direction
def movePlots(trial, moveX, moveY):
	tweet("Moving Trial: X: {0}, Y: {1}".format(moveX, moveY), ap=arcpy)
	for p in trial['plots']:
		polyGeom = trial['plots'][p]
		moveArray = []		
		for segment in polyGeom.getPart():
			for pt in segment:
				moveArray.append(Point((pt.X + moveX),(pt.Y + moveY)))
		
		trial['plots'][p] = Polygon(arcpy.Array(moveArray))				# overwrite polgon with rotated coordinates	
		
	

#### add the plot layer to the data frame
def addLayer(arcgis):
	tweet("Loading Plot Layer: {0}".format(arcgis['plotLayer']), ap=arcpy)
	plotLyr = arcgis['maps'].addDataFromPath(arcgis['plotLayer'])
	
	for lyr in arcgis['maps'].listLayers():
		tweet(lyr.name, ap=arcpy)
		if(lyr.name == 'plots'):
			labelClasses = lyr.listLabelClasses()
			labelClasses[0].expression =  '$feature.PlotId'
			lyr.showLabels = True	


	

#====== MAIN TOOL FUNCTIONS =======#

##### Trial Information: Read and store informtion about the trial setup  (everything in X.Y format [columns,rows])
def TrialInfo(toolParam):
	trialInfo = {
		'plotNum': [toolParam['cols'], toolParam['rows']],				# number of plots in X and Y dimensions
		'plotSize': [toolParam['plotX'], toolParam['plotY']],			# size of each plot
		'AlleyDim': [toolParam['alleyX'], toolParam['alleyY']],			# width of alleys
		'BoarderDim': [toolParam['boarderX'], toolParam['boarderY']],	# width of boarder outside of plot area
		'side': toolParam['side'] 										# the side (left or right) of the guideline to create the plots
		}

	tweet("Plot Side: {0}".format(trialInfo['side']), ap=arcpy)
	if(trialInfo['side'] == 'Right'):
		trialInfo['plotSize'][1] = trialInfo['plotSize'][1] * -1
		trialInfo['AlleyDim'][1] = trialInfo['AlleyDim'][1] * -1
		trialInfo['BoarderDim'][1] = trialInfo['BoarderDim'][1] * -1
	
	return(trialInfo)


##### Creates the trial based on user inputs 
def CreateTrial(trialInfo, spatialRef):
	trial = {} 
	trial = { 
		'dims': calcTrialDim(trialInfo),
		'plots': createPlots(trialInfo, spatialRef)
	} 

	rotatePlots(trial, Point(0,0), trialInfo['angle'])
	movePlots(trial, trialInfo['ulCorner'].X, trialInfo['ulCorner'].Y)
	return(trial)



##### Determine trial angle anf upper left corner from user input - i.e. trialGuide FeatureSet
def orientation(trialGuide):
	vertex = []															# an array of points, each point is a vertex of the line that the user created 
	for row in arcpy.da.SearchCursor(trialGuide, ["SHAPE@"]):
		for segment in row[0].getPart():
			for point in segment:
				vertex.append(point)		
	
	angle = calcAngle(vertex[0],vertex[1])
	return(angle, vertex[0])	



#### Calculate the trial dimensions (width,height)
def calcTrialDim(tInfo):
	tWidth = (2*tInfo['BoarderDim'][0]) + (tInfo['plotNum'][0]-1 * tInfo['AlleyDim'][0]) + (tInfo['plotSize'][0] * tInfo['plotNum'][0])		# X dimension
	tHeight = (2*tInfo['BoarderDim'][1]) + (tInfo['plotNum'][1]-1 * tInfo['AlleyDim'][1]) + (tInfo['plotSize'][1] * tInfo['plotNum'][1])	# Y dimension
	tweet("Trial Dimensions: {0} {1}".format(tWidth,tHeight), ap=arcpy)
	return([tWidth, tHeight])



#### loop through the rows and coumns creating the plots
# - if flip is specfied, plots are created on right side of guide line
def createPlots(tInfo, spatialRef, flip=False):
	id = 1
	plotDict = {}
	for c in range(1, tInfo['plotNum'][0]+1):
		for r in range(1, tInfo['plotNum'][1]+1):
			currentPlot_ll = getPlot_ll(c, r, tInfo)
			currentPlotPoly = getPlotPoly(currentPlot_ll[0], currentPlot_ll[1], tInfo['plotSize'], spatialRef)
			plotDict[id] = currentPlotPoly
			id += 1
	return(plotDict)



#### create a layer and add all the plots 	
def createTrialShape(trial, sr):
	tweet("Creating Trial Layer...", ap=arcpy)
	newlayer = arcpy.management.CreateFeatureclass(arcpy.env.scratchGDB, "plots", "POLYGON", spatial_reference = sr)
	fc = newlayer[0]		# get the path to the layer 
	with arcpy.da.InsertCursor(fc, ['SHAPE@']) as cursor:
		for x, y in trial['plots'].items():					 # loop through polygons inserting
			cursor.insertRow([y])		
	del cursor
	return(fc)


### add a label to the polygons (columns-row attribute) 
def addLabelAtribute(trialInfo, arcgis):
	arcpy.AddMessage("Labeling Plots")
	arcpy.AddField_management(arcgis['plotLayer'], "PlotId", "TEXT", field_length=10)
	with arcpy.da.UpdateCursor(arcgis['plotLayer'], ['OID@', 'PlotId']) as cursor:
		for row in cursor:
			oid = row[0]
			curCol = (oid-1)//(trialInfo['plotNum'][1])
			curRow = oid-(curCol * trialInfo['plotNum'][0])
			#row[1] = '{:02d}'.format(curRow) + '-' + '{:02d}'.format(curCol+1)
			row[1] = str(curRow) + '-' + str(curCol+1)
			cursor.updateRow(row)	


# convert the units specified by the user into the unbits of the map frame
def convert_units(toolParam, conversion):
	pamam_names = ['plotX','plotY','alleyX','alleyY','boarderX','boarderY']
	for i, key in toolParam.items():
		if(i in pamam_names):
			if(key > 0):
				toolParam[i] = key * conversion
				#tweet(toolParam[i],ap=arcpy)
				


#======= MAIN =======#
if __name__ == '__main__':

	FT_PER_METER = 0.30480060960121924
	METER_PER_FT = 1/FT_PER_METER

	##### Get the parameters set in the Toolbox
	toolParam = {}
	params	= arcpy.GetParameterInfo()
	for p in params:
		toolParam[p.name] = p.value
	
	### Set the paramters to the current working document
	arcgis = setArcMapParam()
	
	if not arcgis['map_sr'].type == "Projected":
		arcpy.AddError('ERROR: Map Frame must be set up a Projected Coordiate System') 
		sys.exit()
	else:
		arcpy.env.outputCoordinateSystem = arcgis['map_sr']
		

	### Read in information about the trial sizing and dimensions
	trialInfo = TrialInfo(toolParam)
	
	### Determine trial orientation if not specfied by the user
	trialInfo['angle'], trialInfo['ulCorner'] = orientation(toolParam['trialGuide'])	

	###assuming units provided in feet, if the map projection is meters, than convert the orgin of the trials to meters
	if(arcgis['meters_per_unit'] == 1):
		trialInfo['ulCorner'].X = trialInfo['ulCorner'].X * FT_PER_METER
		trialInfo['ulCorner'].Y = trialInfo['ulCorner'].Y * FT_PER_METER

	### Create the Trial
	trial = CreateTrial(trialInfo, arcgis['map_sr'])
	
	### Create the shapefile layer
	arcgis['plotLayer'] = createTrialShape(trial, arcgis['map_sr'])
	
	### Add labels to the plots (columns-rows)
	addLabelAtribute(trialInfo, arcgis)	
	
	### add to the map 
	addLayer(arcgis)
	

	
	
	
	


