from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.layerstack import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.PeakLoads')


class PeakLoads(DiTToLayerBase):
    name = "Peak Loads"
    uuid = UUID("002c1800-2e25-486e-b0c2-146dbfe714d2")
    version = 'v0.1.0'
    desc = "Layer to find the peak value in the timeseries load objects"

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
    PeakLoads.main()

    