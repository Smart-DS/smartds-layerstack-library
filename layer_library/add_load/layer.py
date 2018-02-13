from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.modify.modify import Modifier

logger = logging.getLogger('layerstack.layers.AddLoad')


class AddLoad(DiTToLayerBase):
    name = "Add Load"
    uuid = UUID("3bca9dc6-cbcd-4430-a2d7-c767296e321a")
    version = 'v0.1.0'
    desc = "Layer to add load to base DiTTo model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('load_path',
                            description='Path to load data',
                            parser=str, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, model, load_path):
        loads = Store()
        reader = CsvReader()
        reader.parse(loads, load_path)

        modifier = Modifier()
        intermediate_model = modifier.merge(model, loads)
        return intermediate_model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    AddLoad.main()
    
