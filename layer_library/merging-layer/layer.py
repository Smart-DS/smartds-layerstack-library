from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.readers.csv.read import reader as CSVReader
from ditto.modify.modify import Modifier
from ditto.store import Store
import os
import pandas as pd

logger = logging.getLogger('layerstack.layers.MergingLayer')


class MergingLayer(DiTToLayerBase):
    name = "merging-layer"
    uuid = UUID("67ec2cc6-d36d-4576-af37-60ffd5178af9")
    version = '0.1.0'
    desc = "create a DiTTo model for Load and/or Capacitor coordinates and merge them to the main model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['filename'] = Kwarg(default=None, description='Path to the CSV input file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):

        if 'filename' in kwargs:
            filename = kwargs['filename']
	
        #If the file does not exist, do nothing and return the input model
        if not os.path.exists(filename):
            return model

        # If the file is empty also do nothing and return the input model
        try:
            df = pd.read_csv(filename)
        except pd.errors.EmptyDataError:
            logging.warning("Empty Dataframe loaded for {}".format(filename))
            return model

        #Create a CSV reader
        csv_reader = CSVReader()
        m2 = Store()
        csv_reader.parse(m2, filename)

        #Create a Modifier object
        modifier = Modifier()

        #Merge the two models
        new_model = modifier.merge(model, m2)

        #Return the new model
        return new_model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    MergingLayer.main()

    
