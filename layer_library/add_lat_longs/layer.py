from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

import math
import pyproj
import os
logger = logging.getLogger('layerstack.layers.Add_Lat_Longs')


class Add_Lat_Longs(DiTToLayerBase):
    name = "add_lat_longs"
    uuid = UUID("d7cf3ab2-a1d5-4f7b-8ca9-a59d3a1a013e")
    version = '0.1.0'
    desc = "Add lat-long coordinates in the OpenDSS output for any Buscoords file"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['folder_location'] = Kwarg(default=None, description='Location from where to start traversing',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['dataset'] = Kwarg(default=None, description='Dataset area being used',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        projection = {'dataset_4':'epsg:32610', 'dataset_3':'epsg:32617', 'dataset_2':'epsg:32613','t_and_d':'epsg:32614','houston':'epsg:32614','texas_rural':'epsg:32614','South_Texas':'epsg:32614','texas_test':'epsg:32614','Full_Texas':'epsg:32614'}
        folder_location = None
        if 'folder_location' in kwargs:
            folder_location = kwargs['folder_location']

        dataset = None
        if 'dataset' in kwargs:
            dataset = kwargs['dataset']
        print('Writing long-lats')
        invproj = pyproj.Proj(init=projection[dataset],preserve_units=True) 
        for dirname,subdirs,files in os.walk(folder_location):
            if 'Buscoords.dss' in files:
                f_in = open(os.path.join(dirname,'Buscoords.dss'),'r')
                f_out = open(os.path.join(dirname,'Long_lat_buscoords.txt'),'w')
                for row in f_in.readlines():
                    coords = row.split()
                    if len(coords) != 3:
                        f_out.write('\n')
                        continue
                    x = coords[1]
                    y = coords[2]
                    lat_long = invproj(x,y,inverse=True)
                    i_lat = lat_long[1]
                    i_long = lat_long[0]
                    f_out.write(coords[0]+' '+str(i_long)+' '+str(i_lat)+'\n')
                f_in.close()
                f_out.close()
                
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Add_Lat_Longs.main()

    
