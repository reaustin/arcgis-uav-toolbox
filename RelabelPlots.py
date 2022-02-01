import arcpy
import pandas as pd



def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)
	

### load the attributes from the plot layer into a dictionary
# - assumes there is an attribute 'PlotId' that contains column-row
def loadAttributes():
	data = { 
		'oid': [],
		'col': [],
		'row': []
	}	

	with arcpy.da.UpdateCursor(toolParam['plotLyr'], ['OID@', 'PlotId']) as cursor:
		for row in cursor:
			data['oid'].append(row[0])
			plot = row[1]
			plotId = [int(x) for x in plot.split('-')]			
			data['row'].append(plotId[0])
			data['col'].append(plotId[1])	
	return(pd.DataFrame(data))



### add new label attribute to plot layer
def addAttribute(df, toolParam):
	colMax = df['col'].max()
	rowMax = df['row'].max()
	arcpy.AddField_management(toolParam['plotLyr'], "Label", "TEXT", field_length=10)
	arcpy.CalculateField_management(toolParam['plotLyr'],'Label','\"0-0\"')
	
	if(toolParam['cFlip']):
		tweet("Flipping Columns", ap=arcpy)	
	if(toolParam['rFlip']):
		tweet("Flipping Rows", ap=arcpy)		
	
	with arcpy.da.UpdateCursor(toolParam['plotLyr'], ['OID@', 'PlotId', 'Label']) as cursor:
		tweet(cursor.fields, ap=arcpy)
		for row in cursor:
			tweet(row[2], ap=arcpy)
			p = [int(x) for x in row[1].split('-')]	
			r = p[0]
			c = p[1]
			if(toolParam['cFlip']):
				c = colMax + 1 - p[1] 
			if(toolParam['rFlip']):
				r = rowMax + 1 - p[0] 
			row[2] = str(r) + '-' + str(c)
			cursor.updateRow(row)
	del cursor		
			

### update the labeles in GIS to show new numbering
def updateLables(toolParam):
	maps = arcpy.mp.ArcGISProject("CURRENT").listMaps()[0]

	for lyr in maps.listLayers():
		tweet(lyr.name, ap=arcpy)
		if(lyr.name == 'plots'):
			labelClasses = lyr.listLabelClasses()
			labelClasses[0].expression =  '$feature.Label'
			lyr.showLabels = True	



if __name__ == '__main__':
	arcpy.env.overwriteOutput = True 	
	#### Get the parameters set in the Toolbox
	toolParam = {}
	params	= arcpy.GetParameterInfo()
	for p in params:
		toolParam[p.name] = p.value

	
	### Load teh data from theg plot layer into a pandas dataframe
	df = loadAttributes()

	# add labels to layer
	addAttribute(df, toolParam)
	

	updateLables(toolParam)



