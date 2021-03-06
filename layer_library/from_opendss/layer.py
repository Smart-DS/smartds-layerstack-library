from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

from ditto.store import Store
from ditto.readers.opendss.read import Reader as OpenDSSReader

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
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Base directory for argument paths.')
        return kwarg_dict

    @classmethod
    def apply(cls, stack, opendss_model, bus_coords, base_dir=None, read_power_source=True):
        if base_dir and (not os.path.exists(opendss_model)):
            opendss_model = os.path.join(base_dir,opendss_model)
        if base_dir and (not os.path.exists(bus_coords)):
            bus_coords = os.path.join(base_dir,bus_coords)

        if not os.path.exists(opendss_model):
            raise ValueError("No opendss_model file exists at {}".format(opendss_model))
        if not os.path.exists(bus_coords):
            raise ValueError("No bus_coords model file exists at {}".format(bus_coords))

        base_model = Store()
        reader = OpenDSSReader(master_file=opendss_model,buscoordinates_file=bus_coords)
        reader.parse(base_model)
        base_model.set_names()
        stack.model = base_model
        return True


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    FromOpenDSS.main()
