from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

from ditto.store import Store
from ditto.readers.opendss.read import reader as OpenDSSReader

logger = logging.getLogger('layerstack.layers.FromOpenDSS')


class FromOpenDSS(LayerBase):
    name = "From OpenDSS"
    uuid = UUID("f6a6cd1d-193f-475d-96a2-b9f5d88de202")
    version = 'v0.1.0'
    desc = "Layer to load DiTTo model from Open DSS"

    @classmethod
    def args(cls):
        arg_list = super().args()
        arg_list.append(Arg('opendss_model',
                            description='Path to OpenDSS model to be loaded',
                            parser=str, choices=None, nargs=None))
        arg_list.append(Arg('bus_coords',
                            description='Bus Coords for OpenDSS Model',
                            parser=str, choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['read_power_source'] = Kwarg(default=True, parser=bool)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, opendss_model, bus_coords, read_power_source=True):
        base_model = Store()
        reader = OpenDSSReader()
        reader.build_opendssdirect(opendss_model)
        reader.set_dss_file_names({'Nodes': bus_coords})
        reader.parse(base_model, verbose=True, read_power_source=read_power_source)
        base_model.set_names()
        stack.model = base_model
        return True


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    FromOpenDSS.main()