from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.FindPeakLoad')


class FindPeakLoad(DiTToLayerBase):
    name = "Find Peak Load"
    uuid = UUID("880466d5-2171-4633-ae7e-30446829a189")
    version = 'v0.1.0'
    desc = "Layer to find the peak timeseries loads"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['kwarg_name'] = Kwarg(default=None, description='',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    FindPeakLoad.main()

    
