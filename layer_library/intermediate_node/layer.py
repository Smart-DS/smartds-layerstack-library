from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.models.position import Position

logger = logging.getLogger('layerstack.layers.Intermediate_Node')


class Intermediate_Node(DiTToLayerBase):
    name = "intermediate_node"
    uuid = UUID("a83d13b8-8293-4ecc-bfec-fc922fbb3764")
    version = '0.1.0'
    desc = "Use information from LineCoord.txt to create intermediate nodes with their coordinates"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['filename'] = Kwarg(default=None, description='Path to LineCoord.txt',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        if 'filename' in kwargs:
            filename = kwargs['filename']        

        #Open and read LineCoord.txt
        with open(filename,'r') as f:
            lines = f.readlines()
    
        #Parse the lines
        for line in lines:
            raw = line.split(';')
            #Get the name of the line
            line_name = raw[0].replace(' ','').lower()
            if line_name[-3:] == '_s0' or line_name[-3:] =='_s1' or line_name[-3:] == '_s2':
                continue

    
            #Get the coordinates
            coords = raw[1:]
            coords = map(lambda x:eval(x.strip()),coords)
    
            #For each coordinate, create a position object
            for coord in coords:
                #Create Position object
                pos = Position(model)
                
                #Set lat and long
                pos.long, pos.lat = coord
        
                #Add the coordinates to the model
                if model[line_name].positions is None:
                    model[line_name].positions=[pos]
                else:
                    model[line_name].positions.append(pos)
            
        #Return the model
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Intermediate_Node.main()

    
