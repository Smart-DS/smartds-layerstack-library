from __future__ import print_function, division, absolute_import

import os
from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase
from ditto.store import Store
from ditto.readers.json.read import Reader as JsonReader

logger = logging.getLogger('layerstack.layers.From_Json')


class From_Json(LayerBase):
    name = "from_json"
    uuid = UUID("8289736c-2bf1-434d-b531-1353076c4c89")
    version = '0.1.0'
    desc = "Read a json DiTTo model into DiTTo"

    @classmethod
    def args(cls):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Folder to read json file from',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['input_filename'] = Kwarg(default=None, description='Name of json file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        if 'base_dir' in kwargs:
            base_dir = kwargs['base_dir']
        else:
            base_dir = './'
        if 'input_filename' in kwargs:
            input_filename = kwargs['input_filename']
        else:
            input_filename = 'full_model.json' #Default
        base_model = Store()
        reader = JsonReader(input_file = os.path.join(base_dir,input_filename))
        reader.parse(base_model)
        base_model.set_names()
        stack.model = base_model

        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    From_Json.main()

    
