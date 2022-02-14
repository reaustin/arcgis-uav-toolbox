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
def calcMGVRI(img, band_order=['R','G','B']):
    tweet('Calculating MGVRI...', ap=arcpy)
    _out_ras = RasterCalculator([img[0]['raster'], img[1]['raster'], img[2]['raster']], 
                                band_order, 
                                '((G*G) -(R*R)) / ((G*G) (R*R))'
                                )
    return(_out_ras)    



# Calculate the Modified Photochemical Reflectance Index (MPRI) - Yang et al.(2008)
def calcMPRI(img, band_order=['R','G','B']):
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


### ========================================== ###
#---- Below are 5 Bands Vegetative Indicies  ----#


# Calculate the Normalised difference Vegetation Index (NDVI) - Rouse et al (1973)
def calcNDVI(img, band_order):
    tweet('Calculating NDVI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                '(NIR - R) / (NIR + R)'
                                )
    return(_out_ras) 



# Calculate the Red-Edge Normalised difference Vegetation Index (RENDVI) - Rouse et al (1973)
def calcRENDVI(img, band_order):
    tweet('Calculating RE-NDVI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                '(RE - R) / (RE + R)'
                                )
    return(_out_ras) 



# Calculate the Difference Vegatiavte Index (DVI) - Jordan (1969)
def calcDVI(img, band_order):
    tweet('Calculating DVI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                'NIR - R'
                                )
    return(_out_ras) 


# Calculate the Ratio Vegetation Index (RVI) - Pearson and Miller (1972)
def calcRVI(img, band_order):
    tweet('Calculating RVI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                'NIR / R'
                                )
    return(_out_ras) 



# Calculate the Green Normalized Difference Vegetation Index (GNDVI) - Ma et al. 1996
def calcGNDVI(img, band_order):
    tweet('Calculating GNDVI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                '(NIR - G) / (NIR + G)'
                                )
    return(_out_ras) 


# Calculate Chlorophyll Index (CI) - Gitelson et al
def calcCI(img, band_order):
    tweet('Calculating CI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                '(NIR / R) - 1'
                                )
    return(_out_ras) 



# Calculate Chlorophyll Vegetation Index CVI Vincini et al
def calcCVI(img, band_order):
    tweet('Calculating CVI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                '(NIR / G) * (R / G)'
                                )
    return(_out_ras) 



# Calculate Red Edge Index (REI) - Vogelmann et al.
def calcREI(img, band_order):
    tweet('Calculating REI...', ap=arcpy)
    _raster_list = [ img[index]['raster'] for index, data in img.items() ]
    _out_ras = RasterCalculator(_raster_list,
                                band_order, 
                                '(NIR / RE)'
                                )
    return(_out_ras) 

