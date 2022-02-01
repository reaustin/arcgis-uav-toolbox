import os, sys
import arcpy
from arcpy.sa import ZonalStatisticsAsTable
import pandas as pd
import pdb


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
	param['root'] = os.path.dirname(param['project'].filePath)
	arcpy.env.overwriteOutput = True 
	param['sr'] = arcpy.SpatialReference(2264)
	return param



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
	plotStatInfo = {}
	for bandNum, bandName in bandInfo['bands']:
		curLay = imgFileBase + "\\" + bandName
		currOutFile = outFileName + '_B' + str(bandNum)
		tweet("MSG: Calculating Statistics for Band Number: {0}\n  {1}\n  {2}".format(bandNum,curLay,currOutFile), ap=arcpy)
		ZonalStatisticsAsTable(toolParam['plotLyr'], toolParam['plotID'],curLay, currOutFile, "NODATA", "ALL")
		plotStatInfo[bandNum] = { 'statFile' : currOutFile }
	
	return(plotStatInfo)


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




### convert the geodatabse tables into dataframes 
def createDataFrames(plotStatInfo):
	tweet("MSG: Converting to data frames...", ap=arcpy)
	for bandnum, statInfo in plotStatInfo.items():
		statInfo['df'] = table_to_data_frame(statInfo['statFile'])
		

### add a column to the data frame indicating the band number 
def addBandNumbersToDf(plotStatInfo):
	tweet("MSG: Adding band numbers to dataframes...", ap=arcpy)
	for bandnum, statInfo in plotStatInfo.items():
		statInfo['df']['band'] = bandnum


### create a parameter (dictionary) used to rename the columns in a pandas data frame
def renameColumnParam(df, postFix, excludeFldList):
	rename = {}
	for dfColumn in list(df):
		if(dfColumn not in excludeFldList):
			newFldName = dfColumn + postFix
			rename[dfColumn] = newFldName
	return(rename)	


def renameStatFields(plotStatInfo, statFld):
	tweet("MSG: Renaming Columns...", ap=arcpy)	
	createDataFrames(plotStatInfo)
	for bandnum, statDf in plotStatInfo.items():
		postFix = "_B" + str(bandnum)
		_rename = renameColumnParam(statDf['df'], postFix, [statFld, 'Rowid','OBJECTID'])
		statDf['df'].rename(columns=_rename, inplace=True)
		


### used for debugging
def setStatInfo():
	plotStatInfo = {
		1: "P:\Tobacco\locations\CentralCrops\GIS\projects\CWNCC21\CWNCC21.gdb\outstat_B1",
		2: "P:\Tobacco\locations\CentralCrops\GIS\projects\CWNCC21\CWNCC21.gdb\outstat_B2",
		3: "P:\Tobacco\locations\CentralCrops\GIS\projects\CWNCC21\CWNCC21.gdb\outstat_B3"
	}
	return(plotStatInfo)


### combine all the individual band statistics into one file (append long)
# - assumes a new column representing band number has already been added
def combineDataFrames(plotStatInfo):
	df_all = pd.DataFrame()
	for bandnum, statDf in plotStatInfo.items():
			df_all = df_all.append(statDf['df'])

	#tweet(df_all, ap=arcpy)
	return(df_all)
	

def deleteGeodatabaseTables(plotStatInfo):
	tweet("MSG: Deleting Temporary Tables...", ap=arcpy)
	for bandnum, statInfo in plotStatInfo.items():
		tweet("   - {0}".format(statInfo['statFile']), ap=arcpy)
		arcpy.Delete_management(statInfo['statFile'])



def saveStats(outDf, outFile):
	tweet("MSG: Saving Plot Statistics To: {0}".format(outFile), ap=arcpy)	
	outDf.to_csv(outFile)


if __name__ == '__main__':
	
    #### Get the parameters set in the Toolbox and in the Map
	toolParam = getToolParam()
	mapParam = setArcMapParam()
	imgBandInfo = getBandInfo(toolParam['img'])

	# calculte the zonal statitics by plot and save locations in dictionary
	plotStatInfo = calcPlotStats(toolParam, imgBandInfo)
	#plotStatInfo = setStatInfo()

	### convert the geodatabase tables into pandas dataframes
	createDataFrames(plotStatInfo)

	### add a column to each df that represents that band
	addBandNumbersToDf(plotStatInfo)

	### combine all the df (band statistics) into one dataframe - append 
	_df_allStats = combineDataFrames(plotStatInfo)

	### save the output file
	outFile = os.path.join(mapParam['root'],'output.csv')
	saveStats(_df_allStats, outFile)

	### do some housecleaning
	deleteGeodatabaseTables(plotStatInfo)

	tweet("MSG: ALL DONE MY BRUTHA", ap=arcpy)
