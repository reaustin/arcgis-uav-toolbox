import os, sys
import pandas as pd
import arcpy

from arcpy.sa import RasterCalculator 



def tweet(msg, ap=None):
	if(ap is not None):
		ap.AddMessage(msg)
	print(msg)



# Calculates the Visible Atmospherically Resistant Index for an RGB Image
# - VARI (raster, {red_band_id}, {green_band_id}, {blue_band_id})
def calcVARI(uav_img):
    tweet('Calculating VARI...', ap=arcpy)
    return(arcpy.ia.VARI(uav_img,1,2,3))


# Calculate the Green Leaf Index (GLI) - [Louhaichi, M, 2001]
# -> (Green-Red) + (Green+Blue) / (2*Green) + Red + Blue
def calcGLI(img_info, band_order=['R','G','B']):
    tweet('Calculating GLI...', ap=arcpy)
    _out_ras = RasterCalculator([img_info[0]['raster'], img_info[1]['raster'], img_info[2]['raster']], 
                                band_order, 
                                '((2*G)-R-B) / ((2*G) + R + B)'
                                )
    return(_out_ras)


# Calculate the Red-Green-Blue Vegetation Index (RGBVI) - Bendig  et  al.  2015
# -> (Green * Green) - (Red * Blue) / (Green * Green) + (Red * Blue)
def calcRGBVI(img_info, band_order=['R','G','B']):
    tweet('Calculating RGBVI...', ap=arcpy)
    _out_ras = RasterCalculator([img_info[0]['raster'], img_info[1]['raster'], img_info[2]['raster']], 
                                band_order, 
                                '(G*G) - (R*B) / ((G*G) + (R*B))'
                                )
    return(_out_ras)


# Calculate the Normalized Green Red Difference Index (NGRDI) - Tucker  1979
# -> (Green - Red / Green + Red)
def calcNGRDI(img_info, band_order=['R','G','B']):
    tweet('Calculating NGRDI...', ap=arcpy)
    _out_ras = RasterCalculator([img_info[0]['raster'], img_info[1]['raster'], img_info[2]['raster']], 
                                band_order, 
                                '(G-R) / (G+R)'
                                )
    return(_out_ras)