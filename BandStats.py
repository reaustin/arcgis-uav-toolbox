import os
import arcpy
from arcpy.sa import ZonalStatisticsAsTable


###---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)


### Get the tools parameters [plotLyr, plotID, img, outFile]
def getToolParam():
	toolParam = {}
	params	= arcpy.GetParameterInfo()
	for p in params:
		toolParam[p.name] = p.value
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


#### set parameters for outputs
def setOutParam(toolParam):
	outParam = {
		'outfile': toolParam['outFile'],
	}
	#tweet(outParam, ap=arcpy)
	return(outParam)


def getBandInfo(img):
	imgDsc = arcpy.Describe(img)
	imgInfo = {
		'lyr': img,
		'name': imgDsc.nameString,
		'path': imgDsc.path,
		'num_bands': imgDsc.bandCount
	}
	bandList = []
	i = 1
	for rband in imgDsc.children:
		bandList.append((i, rband.name))
		i += 1
	imgInfo['bands'] = bandList
	#tweet(imgInfo, ap=arcpy)
	return(imgInfo)


def calcPlotStats(toolParam, bandInfo):
	imgFileBase = os.path.join(bandInfo['path'], bandInfo['name'])
	outFileName = toolParam['outFile'].value

	for bandNum, bandName in bandInfo['bands']:
		curLay = imgFileBase + "\\" + bandName
		currOutFile = outFileName + '_B' + str(bandNum)
		tweet("MSG: Calculating Statistics for Band Number: {0}\n{1}\n{2}".format(bandNum,curLay,currOutFile), ap=arcpy)
		ZonalStatisticsAsTable(toolParam['plotLyr'], toolParam['plotID'],curLay, currOutFile, "NODATA", "ALL")

		

	tweet("MSG: Calculating Band Statistics", ap=arcpy)
	#imgZSaT = ZonalStatisticsAsTable(toolParam['plotLyr'], toolParam['plotID'], toolParam['img'], toolParam['outFile'], "NODATA", "ALL", "ALL_SLICES")
	#imgZSaT = ZonalStatisticsAsTable(toolParam['plotLyr'], toolParam['plotID'], toolParam['img'], toolParam['outFile'], "NODATA", "ALL")






if __name__ == '__main__':
	
    #### Get the parameters set in the Toolbox and in the Map
	toolParam = getToolParam()
	mapParam = setArcMapParam()
	outParam = setOutParam(toolParam)

	imgBandInfo = getBandInfo(toolParam['img'])

	calcPlotStats(toolParam, imgBandInfo)
	
	tweet("MSG: ALL DONE MY BRUTHA", ap=arcpy)
