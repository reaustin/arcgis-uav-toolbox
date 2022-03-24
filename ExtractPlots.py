import UAVTools.Functions
import UAVTools.Functions as f

import os, sys
import arcpy

from importlib import reload
reload(UAVTools.Functions)


# ---------- FUNCTION BLOCK -----------------------
def tweet(msg, ap=None):
    if(ap is not None):
        ap.AddMessage(msg)
    print(msg)


# Get the tools parameters [plot_lyr, img_list, output_folder, buffer_distance]
def get_tool_param():
    param = {}
    for p in arcpy.GetParameterInfo():
        param[p.name] = p.value
    return(param)




if __name__ == '__main__':

    OUT_IMAGE_POSTFIX = '_c.tif'
    PLOT_BUFFER =  os.path.join('in_memory', 'plot_buff')
    PLOT_BUFFER =  'in_memory/plot_buff'

    img_extract_data = {}


    # Get the parameters set in the Toolbox and in the current Map
    _toolparam = get_tool_param()
    _mapparam = f.set_arcmap_param()

    # create the output directory for the geotiffs if it does not exsist
    f.make_dir("P:\\Tobacco\\locations\\CentralCrops\\GIS\\projects\\CWNCC21\\uav\\imagery\\rgb\\") 
    #f.make_dir(_toolparam['output_folder'].value) 

    sys.exit()
    # set the layer information for the plot layer
    _plot_layer_data = f.set_layer_data(_toolparam['plot_layer'])

    
    # if a beffer is set create the buffer around the plots
    if(_toolparam['buffer_distance'] > 0):
        tweet('Buffering Plot Layer... ', ap=arcpy)
        arcpy.Buffer_analysis(_plot_layer_data['lyr'], PLOT_BUFFER, _toolparam['buffer_distance'])
        _plot_layer_data['lyr'] = PLOT_BUFFER



    # loop through the arcpy Value table pulling out the images 
    #   - note it is a list of lists, thus refer to the first item for the raster layer
    for img in _toolparam['img_list']:
        _img_data = f.set_image_data(img[0])
        _out_raster_file = os.path.join(_toolparam['output_folder'].value,_img_data['name_base'] + OUT_IMAGE_POSTFIX)
        tweet("Extracting image... {0}".format(_out_raster_file), ap=arcpy)
        _out_raster = arcpy.sa.ExtractByMask(_img_data['raster'],_plot_layer_data['lyr'])
        tweet("Saving image... {0}".format(_out_raster_file), ap=arcpy)
        _out_raster.save(_out_raster_file)
        img_extract_data[_img_data['name_base']] = { 
            'raster': _out_raster,
            'out_tiff': _out_raster_file
        }    

    # clean up the memeory layer if it was created
    if(_toolparam['buffer_distance'] > 0):
        _plot_layer_data['lyr'].cleanup()
    
    tweet("\nI'm Extracted ;) ", ap=arcpy)