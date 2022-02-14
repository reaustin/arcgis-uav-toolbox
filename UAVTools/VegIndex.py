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
def calcVARI(img, band_order=['R','G','B']):
    tweet('Calculating VARI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '(G - R) / (G + R - B)'
                                )
    return(_out_ras)



# Calculates the Excess Green Image (EXG) - Woebbecke et al. (1995)
# - VARI (raster, {red_band_id}, {green_band_id}, {blue_band_id})
def calcEXG(img, band_order=['R','G','B']):
    tweet('Calculating EXG...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '(2 * G) - R - B)'
                                )
    return(_out_ras)



# Calculate the Green Leaf Index (GLI) - [Louhaichi, M, 2001]
# -> (Green-Red) + (Green+Blue) / (2*Green) + Red + Blue
def calcGLI(img, band_order=['R','G','B']):
    tweet('Calculating GLI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '((2*G)-R-B) / ((2*G) + R + B)'
                                )
    return(_out_ras)


# Calculate the Red-Green-Blue Vegetation Index (RGBVI) - Bendig  et  al.  2015
# -> (Green * Green) - (Red * Blue) / (Green * Green) + (Red * Blue)
def calcRGBVI(img, band_order=['R','G','B']):
    tweet('Calculating RGBVI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '(G - (B * R)) / ((G*G) + (B * R))'
                                )
    return(_out_ras)


# Calculate the Normalized Green Red Difference Index (NGRDI) - Tucker  1979
# -> (Green - Red / Green + Red)
def calcNGRDI(img, band_order=['R','G','B']):
    tweet('Calculating NGRDI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '(G-R) / (G+R)'
                                )
    return(_out_ras)



# Calculate the Modified Green Red Vegetation Index (MGVRI) - Bendig, et al. (2015)
def calcNGRDI(img, band_order=['R','G','B']):
    tweet('Calculating MGVRI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '((G*G) -(R*R)) / ((G*G) (R*R))'
                                )
    return(_out_ras)    



# Calculate the Modified Photochemical Reflectance Index (MPRI) - Yang et al.(2008)
def calcNGRDI(img, band_order=['R','G','B']):
    tweet('Calculating MPRI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '(G - R) / (G + R)'
                                )
    return(_out_ras)



# Calculate the Vegetativen Index (VEG) - Hague et al. (2006)
def calcVEG(img, band_order=['R','G','B']):
    tweet('Calculating VEG...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                'G / ((Power(R,0.667) * Power(B,1-0.0667))'
                                )
    return(_out_ras) 

    