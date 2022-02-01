"""
Tool:               <Tool label>
Source Name:        <File name>
Version:            <ArcGIS Version>
Author:             <Author>
Usage:              <Command syntax>
Required Arguments: <parameter0>
                    <parameter1>
Optional Arguments: <parameter2>
                    <parameter3>
Description:        <Description>
"""
import arcpy
import pandas as pd
import pdb


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
			data['col'].append(plotId[0])
			data['row'].append(plotId[1])	
	return(pd.DataFrame(data))



### Create the new labels in the dataframe
def createLabels(df, toolParam):
	colMax = df['col'].max()
	rowMax = df['row'].max()
	#if(toolParam['corner'] == 'Upper Left'):
	#	if(toolParam['direction'] == 'East-West'):
		
	
	#if(toolParam['corner'] == 'Upper Right'):
	
	
	if(toolParam['corner'] == 'Lower Left'):
		if(toolParam['direction'] == 'East-West'):

			df['newCol'] = df['oid']
			df['newRow'] = df['oid']
			tweet(df, ap=arcpy)
			#pdb.set_trace()
			
	
	
	#if(toolParam['corner'] == 'Lower Right'):
	
	
	
		


if __name__ == '__main__':

	#### Get the parameters set in the Toolbox
	toolParam = {}
	params	= arcpy.GetParameterInfo()
	for p in params:
		toolParam[p.name] = p.value

	
	### Load teh data from theg plot layer into a pandas dataframe
	df = loadAttributes()


	#create the new attribiute in the layer and add the respective labels
	createLabels(df, toolParam)
	
	

