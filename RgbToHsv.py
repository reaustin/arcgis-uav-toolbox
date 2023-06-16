import UAVTools.Functions
import UAVTools.Functions as f

import os, sys
import glob
import arcpy

from importlib import reload
reload(UAVTools.Functions)


if __name__ == '__main__':

    OUT_IMAGE_POSTFIX = '_hsv.tif'

    # Get the parameters set in the Toolbox and in the current Map [input_folder, output_folder, filter]
    _toolparam = f.get_tool_param()
    _mapparam = f.set_arcmap_param()    


    # look through the directory grabbing 3 band tiff files that meet the filter if specified 
    types = ('.tif', '.tiff')
    for file in os.listdir(_toolparam['input_folder'].value):
        if file.lower().endswith(types):
            
            _file_name = os.path.join(_toolparam['input_folder'].value, file)
            _raster = arcpy.Raster(_file_name)

            items = file.lower().split('_')

            if(_toolparam['filter'] in items) or (_toolparam['filter'] is None):

                if(f.check_bands(_raster, 3)):

                    _file_name_base = os.path.splitext(file)[0]
                    _out_hsv_file = os.path.join(_toolparam['output_folder'].value, _file_name_base + OUT_IMAGE_POSTFIX)
                    
                    f.tweet("MSG: Converting RGB to HSV...\n  -> {0}\n  -> {1}".format(_file_name, _out_hsv_file), ap=arcpy) 
                    _out_hsv_image = arcpy.ia.ColorspaceConversion(_raster, "rgb_to_hsv")

                    f.tweet("MSG: Saving HSV...\n  -> {0}".format(_out_hsv_file), ap=arcpy) 
                    _out_hsv_image.save(_out_hsv_file)

                else:
                    f.tweet("SKipping - Wrong number of bands...\n  ->{0}".format(_file_name), ap=arcpy) 

            else:
                f.tweet("SKipping - Did not meet filter requirement...\n  ->{0}\n   ->filter: {1}".format(_file_name, _toolparam['filter']), ap=arcpy) 



    
    f.tweet("ALL LOADED UP...", ap=arcpy) 

