from __future__ import print_function, division, absolute_import
import os

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.writers.json.write import Writer

logger = logging.getLogger('layerstack.layers.To_Json')


class To_Json(DiTToLayerBase):
    name = "to_json"
    uuid = UUID("e1865221-7c70-47e4-a9c8-030c80ad95ff")
    version = '0.1.0'
    desc = "Write the dataset to json"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Location to write the json file to',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['filename'] = Kwarg(default='full_model.json', description='Actual filename',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        base_dir = None
        filename = 'full_model.json'
        if 'base_dir' in kwargs:
            base_dir = kwargs['base_dir']
        if 'filename' in kwargs:
            filename = kwargs['filename']

        if base_dir is None:
            return model
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        writer = Writer(output_path=base_dir,filename=filename)
        writer.write(model)

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    To_Json.main()

    
