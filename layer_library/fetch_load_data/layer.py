from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

logger = logging.getLogger('layerstack.layers.Fetch_Load_Data')


class Fetch_Load_Data(LayerBase):
    name = "fetch_load_data"
    uuid = UUID("8d9a0f12-a460-4c5f-bb22-a53bfa0df9b2")
    version = '0.1.0'
    desc = "Layer to pull the raw Load data from the DRPOWER GRIDDATA repository"

    @classmethod
    def args(cls):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['kwarg_name'] = Kwarg(default=None, description='',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Fetch_Load_Data.main()

    