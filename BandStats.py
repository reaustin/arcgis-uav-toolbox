import os, sys
import arcpy
from arcpy.sa import ZonalStatisticsAsTable, Combine
import pandas as pd
import pdb


###---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)


### Get the tools parameters [plotLyr, plotID, img, imgClass, outFile]
def getToolParam():
	toolParam = {}
	params	= arcpy.GetParameterInfo()
	for p in params:
		toolParam[p.name] = p.value
	if(toolParam['imgClass'] is not None):
		toolParam['classImg'] = True					# the user input a classifed image
	else:
		toolParam['classImg'] = False
	return(toolParam)


### Set/Get ArcGIS properties
def setArcMapParam():
	param = {}
	param['project'] = arcpy.mp.ArcGISProject("CURRENT")
	param['maps'] = param['project'].listMaps()[0]
	param['gdb'] = param['project'].defaultGeodatabase
	param['root'] = os.path.dirname(param['project'].filePath)
	param['scratch'] = arcpy.env.scratchGDB
	arcpy.env.overwriteOutput = True 
	param['sr'] = arcpy.SpatialReference(2264)
	return param



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
    return fc_dataframe


### create a parameter (dictionary) used to rename the columns in a pandas data frame
def renameColumnParam(df, postFix, excludeFldList):
	rename = {}
	for dfColumn in list(df):
		if(dfColumn not in excludeFldList):
			newFldName = dfColumn + postFix
			rename[dfColumn] = newFldName
	return(rename)	


def deleteGeodatabaseTables(scratchGDB):
	tweet("MSG: Deleting Temporary Tables...", ap=arcpy)
	arcpy.env.workspace = scratchGDB
	for t in arcpy.ListTables():
		if('ZStat' in t):
			arcpy.Delete_management(t)
	for r in arcpy.ListRasters():
		if('_rasx' in r):	
			arcpy.Delete_management(r)



def saveStats(outDf, outFile):
	tweet("MSG: Saving Plot Statistics To: {0}".format(outFile), ap=arcpy)	
	outDf.to_csv(outFile, index=False)


def setClassifedRaster(classifiedRatser):
	if(classifiedRatser is not None):
		imgDsc = arcpy.Describe(classifiedRatser)
		classImg = {
			'lyr': classifiedRatser,
			'raster': arcpy.Raster(imgDsc.nameString), 
			'name' : classifiedRatser.name, 
			'name_base': os.path.splitext(arcpy.Raster(imgDsc.nameString).name)[0],
			'path_root': imgDsc.path,
			'path': os.path.join(imgDsc.path,classifiedRatser.name),
			'num_bands': imgDsc.bandCount,
			'has_vat': arcpy.Raster(imgDsc.nameString).hasRAT
		}
		tweet(classImg, ap=arcpy)
		if(classImg['has_vat']):
			classImg['df'] = table_to_data_frame(classImg['path'])
		
		arcpy.env.cellSize = classImg['raster']
		return(classImg)
	return(None)	



def createPlotRaster(plotLyr, plotIdField, outRasFile, debug=False):
	tweet("MSG: Creating Plot Ratser \n {0}".format(outRasFile), ap=arcpy)
	if(not debug):
		arcpy.FeatureToRaster_conversion(plotLyr, plotIdField, outRasFile)				## need to set the cells size to taht of the classRas
	plotData = {
		'lyr' : plotLyr,
		'raster': arcpy.Raster(outRasFile),
		'name' : arcpy.Raster(outRasFile).name,
		'id_field' : plotIdField.value,
		'path' : outRasFile,
		'df' : table_to_data_frame(outRasFile)
	}
	return(plotData)


### Calculate the statistics by zone (i.e. the plots,  and if specfied, the classified raster)
## - returns a dictionary that points to the output zonal statistics files
## - the zone field is always 'Value' 
def calcZoneStats(scratchGDB, zoneData, zoneField, uavImg, debug=False):
	imgDsc = arcpy.Describe(uavImg)
	zoneStat = {}

	i = 1
	for b in imgDsc.children:
		cBandPath = os.path.join(imgDsc.catalogPath,b.name)
		cOutFile =  os.path.join(scratchGDB,'ZStat_' + str(b.name))
		tweet("MSG: Calculating Statistics for Band Number: {0}\n  {1}".format(b.name,cOutFile), ap=arcpy)
		if(not debug):
			ZonalStatisticsAsTable(zoneData, zoneField, cBandPath, cOutFile, "NODATA", "ALL")
		zoneStat[i] = { 
			'band' : b.name,
			'statFile' : cOutFile 
		}
		i += 1
	return(zoneStat)	


### convert the geodatabse tables into dataframes and add a new key 'df' to the data dictionary
def createDataFrames(zoneStat):
	tweet("MSG: Converting tables to data frames...", ap=arcpy)
	for bandnum, zoneDict in zoneStat.items():
		zoneStat[bandnum]['df'] = table_to_data_frame(zoneDict['statFile'])



### add a column to each data frame in the zone dictionary indicating the band number 
def addBandNumbers(zoneStat):
	tweet("MSG: Adding band numbers to dataframes...", ap=arcpy)
	for bandnum, zoneDict in zoneStat.items():
		zoneDict['df']['Band']= bandnum


### combine all the individual band statistics (dataframes) into one file (append down)
# - assumes a new column representing band number has already been added
def combineDataFrames(zoneStat):
	df_all = pd.DataFrame()
	for bandnum, zoneDict in zoneStat.items():
		df_all = df_all.append(zoneDict['df'])
	return(df_all)


### combine the plot layer with the classified raster to create a unque combination of zones within each plot
def combineRasters(plotData, classRasData, outRasFile, debug=False):
	tweet("MSG: Combining Ratsers \n  {0} \n  {1}".format(plotData['path'], classRasData['path']), ap=arcpy)
	if(not debug):
		combineRaster = Combine([plotData['raster'], classRasData['raster']])
		combineRaster.save(outRasFile)
	zoneRasData = {
		'raster': arcpy.Raster(outRasFile),
		'path' : outRasFile,
		'df' : table_to_data_frame(outRasFile)
	}
	return(zoneRasData)


### clean up tey data frame by removeing pixel counts and other unneeded columns
def cleanZoneStatDf(dfMerge):
	dropCol = ['Value_y','Count_x', 'Count_y', 'Red', 'Green', 'Blue']
	dfMerge.drop(columns=dropCol, inplace=True)
	dfMerge.sort_values(by=['Value'], inplace=True)




### Merge the two dataframes so that it contains the combinations for the plotId and the classifications
def mergeDataframes(plotDf, plotIdName, classRasDf, classIdName, zonalRasDf):
	tweet("MSG: Merging  Plots with Zones", ap=arcpy)
	zonePlotMerge = pd.merge(zonalRasDf, plotDf, left_on=plotIdName, right_on='Value')
	zonePlotMerge.rename(columns={'Value_x': 'Value'}, inplace=True)
	tweet(zonePlotMerge, ap=arcpy)
	tweet(classIdName, ap=arcpy)
	zoneClassMerge = pd.merge(zonePlotMerge, classRasDf, left_on=classIdName, right_on='Value')
	zoneClassMerge.rename(columns={'Value_x': 'Value'}, inplace=True)
	cleanZoneStatDf(zoneClassMerge)	
	return(zoneClassMerge)



#### join the zonal information containing the plot identfier and the classfication idenfiers to the zonal stats dataframe
def joinZonalStatsIdentifiers(zonalStatDf, zonalStatsKeyDf):
	zonePlotMerge = pd.merge(zonalStatDf, zonalStatsKeyDf, on='Value')
	zonePlotMerge.sort_values(by=['Band','Value'], inplace=True)
	return(zonePlotMerge)


if __name__ == '__main__':
	
	DEBUG = False

    #### Get the parameters set in the Toolbox and in the current Map
	toolParam = getToolParam()
	mapParam = setArcMapParam()
	
	#### set zone raster and related data 
	classRasData = setClassifedRaster(toolParam['imgClass'])

	#### If a classifed raster is specified by the user, otherwise just use the plot raster as the zones
	if(toolParam['classImg']):
		tweet("MSG: Using Classifed Raster \n  {0}".format(classRasData['path']), ap=arcpy)
		
		#### Create Plot Raster
		plotRasFile = os.path.join(mapParam['scratch'],"plot_ras")
		plotData = createPlotRaster(toolParam['plotLyr'], toolParam['plotID'], plotRasFile, debug=DEBUG)
		
		#### Combine the plot ratser and the classifed raster to create unique zones for the zonal statistics
		zoneRasFile = os.path.join(mapParam['scratch'],"zone_ras")
		zoneRasData = combineRasters(plotData, classRasData, zoneRasFile, debug=DEBUG)
		
		#### Merge Vat's - combine the data from the plots layer  and classfied raster vat to create a key to later merge with the zonal stats
		zoneKeyDf = mergeDataframes(plotData['df'], plotData['name'], classRasData['df'], classRasData['name_base'], zoneRasData['df'])

		### Set the zone data and zone field to the zone raster dataset (plots and classifed classes)
		zoneData = zoneRasData['raster']
		zoneField = 'VALUE'

	else:
		### setthe zone Data and Ids
		zoneData = toolParam['plotLyr']
		zoneField = toolParam['plotID']	


	#### Calculate the zonal statistics
	zoneStat = calcZoneStats(mapParam['scratch'], zoneData, zoneField, toolParam['img'], debug=DEBUG)

	#### Convert the geodatbase tables into pandas dataframes and add a 'df' key to the zone stats dictionary
	createDataFrames(zoneStat)

	#### add band number to the dataframes 
	addBandNumbers(zoneStat)

	#### combine all the dat frames into one 
	zoneStatDf = combineDataFrames(zoneStat)

	#### merge the zonal information containing the plot identfier and the classfication idenfiers to the zonal stats dataframe
	if(toolParam['classImg']):
		outZonalStatDf = joinZonalStatsIdentifiers(zoneStatDf, zoneKeyDf)
	else:
		outZonalStatDf = zoneStatDf	

	#### write the zonal statistics to a table
	saveStats(outZonalStatDf, toolParam['outFile'].value)

	### do some housecleaning
	deleteGeodatabaseTables(mapParam['scratch'])

	tweet("MSG: ALL DONE MY BRUTHA", ap=arcpy)
