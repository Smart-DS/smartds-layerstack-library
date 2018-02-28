from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
from ditto.models.storage import Storage
from ditto.models.phase_storage import PhaseStorage

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.base import Unicode
import json

logger = logging.getLogger('layerstack.layers.Add_Storage')


class Add_Storage(DiTToLayerBase):
    name = "add_storage"
    uuid = UUID("ceae532c-7fce-4674-b7aa-eaa69e219c9c")
    version = 'v0.1.0'
    desc = "Layer for adding static storage to a model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('placement', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('rated_power', description='', parser=None, choices=None, nargs=None))
        arg_list.append(Arg('rated_kWh', description='', parser=None, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, model, placement,rated_power,rated_kWh):

        loads = json.load(open(placement))
        for load in loads:
            ps = Storage(model)
            ps.name = 'storage_'+load
            ps.connecting_element = load
            ps.rated_power = rated_power
            ps.rated_kWh = rated_kWh

            phase_storages = []
            for phase_load in model[load].phase_loads:
                phase_storage = PhaseStorage(model)
                phase_storage.phase = phase_load.phase
                phase_storages.append(phase_storage)
            ps.phase_storage = phase_storages


        model.set_names()
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    Add_Storage.main()

    
