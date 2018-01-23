from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from ditto.layers.args import Arg, Kwarg
from ditto.layers.layer import ModelType, ModelLayerBase

from ditto.store import Store
from ditto.readers.opendss.read import reader as OpenDSSReader

logger = logging.getLogger('ditto.layers.From_Opendss')


class From_Opendss(ModelLayerBase):
    name = "From_OpenDSS"
    desc = "Layer to load DiTTo model from Open DSS"
    model_type = ModelType.DiTTo

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('opendss_model',
                            description='Path to OpenDSS model to be loaded',
                            parser=str, choices=None, nargs=None))
        arg_list.append(Arg('bus_coords',
                            description='Bus Coords for OpenDSS Model',
                            parser=str, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, model, opendss_model, bus_coords, read_power_source = True):
        base_model = Store()
        reader = OpenDSSReader()
        reader.build_opendssdirect(opendss_model)
        reader.set_dss_file_names({'Nodes': bus_coords})
        reader.parse(base_model, verbose=True, read_power_source=read_power_source)
        base_model.set_names()
        return base_model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    #
    From_Opendss.main()
