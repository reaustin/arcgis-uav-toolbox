import UAVTools.Functions
import UAVTools.Functions as f

import os, sys
import arcpy

from importlib import reload
reload(UAVTools.Functions)


def template():
    _template = {
        'uav': {
            'imagery': { 
                'ms': { 
                    'vi': {},
                    'dsm': {},
                    'ortho': {}
                },
                'rgb': {
                    'vi': {},
                    'dsm': {},
                    'ortho': {}                    
                }
            },
            'analysis': {}
        }
    }
    return(_template)


def create_directories(dic, project_root):
    def one_directory(dic, path):
        for name, info in dic.items():
            next_path = os.path.join(path,name)
            if isinstance(info, dict):
                _new_folder = os.path.join(project_root, os.path.join(path,name))
                f.tweet('MSG: Creating Directory: \n  ->{0}'.format(_new_folder), ap=arcpy)
                f.make_dir(_new_folder)
                one_directory(info, next_path)
    one_directory(dic, '')




if __name__ == '__main__':


    # Get the parameters set in the Toolbox and in the current Map [project_root]
    _toolparam = f.get_tool_param()

    folder_template = template()
    
    create_directories(folder_template, _toolparam['project_root'].value)

    f.tweet('MSG: FINI..', ap=arcpy)

