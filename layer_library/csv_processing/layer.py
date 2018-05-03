from __future__ import print_function, division, absolute_import
import pandas as pd
import os

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

logger = logging.getLogger('layerstack.layers.Csv_Processing')


class Csv_Processing(LayerBase):
    name = "csv_processing"
    uuid = UUID("bd8fef77-93aa-4869-85ed-26507f9b086d")
    version = '0.1.0'
    desc = "read the load/capacitor intermediate csv files, and output a csv file that can be used by the csv reader from ditto"

    @classmethod
    def args(cls):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['input_filename'] = Kwarg(default=None, description='Name of the CSV input file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['output_filename'] = Kwarg(default=None, description='Name of the CSV output file',
                                        parser=None, choices=None,
                                        nargs=None, action=None)
        kwarg_dict['object_name'] = Kwarg(default=None, description='Name of the object (ex: Load)',
                                        parser=None, choices=None,
                                        nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        
        if 'input_filename' in kwargs:
            input_filename = kwargs['input_filename']
        else:
            raise ValueError('Missing input file')

        if 'output_filename' in kwargs:
            output_filename = kwargs['output_filename']
        else:
            raise ValueError('Missing output file')

        if 'object_name' in kwargs:
            object_name = kwargs['object_name']
        else:
            raise ValueError('Missing object name')

        #Read the file using Pandas
        #If the file does not exist, the do nothing and return
        if not os.path.exists(input_filename):
            return True

        try:
            df = pd.read_csv(input_filename, delimiter=";")
        except pd.errors.EmptyDataError:
            logging.warning("Empty Dataframe loaded for {}".format(input_filename))
            return True
            

        #Set the column names
        if object_name.lower() == 'load':
            df['{obj}.name'.format(obj=object_name)] = '{objl}_'.format(objl=object_name.lower())+df['{obj}'.format(obj=object_name)]
        else:
            df['{obj}.name'.format(obj=object_name)] = df['{obj}'.format(obj=object_name)]

        #Put everything to lower case
        df['{obj}.name'.format(obj=object_name)] = df['{obj}.name'.format(obj=object_name)].apply(lambda x:x.lower())

        #Latitude
        df['{obj}.positions[0].lat'.format(obj=object_name)] = df['y'].apply(lambda x:x*10**3)

        #Longitude
        df['{obj}.positions[0].long'.format(obj=object_name)] = df['x'].apply(lambda x:x*10**3)

        #Remove useless columns
        df2 = df[['{obj}.name'.format(obj=object_name),
                  '{obj}.positions[0].long'.format(obj=object_name),
                  '{obj}.positions[0].lat'.format(obj=object_name)
                ]]

        #Write to csv
        df2.to_csv(output_filename, index=False)

        #Return True
        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Csv_Processing.main()

    
