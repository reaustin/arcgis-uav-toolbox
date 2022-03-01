import UAVTools.Functions
import UAVTools.Functions as f

import os, sys
import arcpy

from importlib import reload
reload(UAVTools.Functions)



if __name__ == '__main__':


    # Get the parameters set in the Toolbox and in the current Map [root_dir, image_folder, wildcard]
    _toolparam = f.get_tool_param()
    _mapparam = f.set_arcmap_param()    


    # walk through the subdirectories looking for the image folder
    for root, subdirs, files in os.walk(_toolparam['root_dir'].value):
        if(_toolparam['image_folder'] in subdirs):
            _img_folder = os.path.join(root, _toolparam['image_folder'])
            for file in os.listdir(_img_folder):
                if file.lower().endswith(('.tif', '.tiff')):
                    if(_toolparam['wildcard'] in file) or (_toolparam['wildcard'] is None):
                        _img_file = os.path.join(_img_folder, file)
                        f.tweet(_img_file, ap=arcpy)
                        _img_layer = _mapparam['maps'].addDataFromPath(_img_file)
                        _img_layer.visible = False
                        l_cim = _img_layer.getDefinition('V2')
                        l_cim.expanded = False
                        _img_layer.setDefinition(l_cim)

    
    
    f.tweet("ALL LOADED UP...", ap=arcpy) 
