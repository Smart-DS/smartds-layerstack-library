from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.Shorten_Long_Names')


class Shorten_Long_Names(DiTToLayerBase):
    name = "shorten_long_names"
    uuid = UUID("313ea099-8c4e-4468-b2f5-93fc19abec60")
    version = '0.1.0'
    desc = "Shorten line names that are too long for CYME"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['max_size'] = Kwarg(default=None, description='Maximum size of any element_name',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        max_size = None
        if 'max_size' in kwargs:
            max_size = kwargs['max_size']
        for i in model.models:
            if hasattr(i,'name') and len(i.name) > max_size:
                ### INSERT LOGIC HERE. JUST DEBUGGING FOR NOW ###
                print(len(i.name),i.name)
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Shorten_Long_Names.main()

    
