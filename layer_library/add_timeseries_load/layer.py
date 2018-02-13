from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.AddTimeseriesLoad')

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.modify.modify import Modifier


class AddTimeseriesLoad(DiTToLayerBase):
    name = "Add Timeseries Load"
    uuid = UUID("51f48260-a314-4dfb-aa5c-b64b98a219c8")
    version = 'v0.1.0'
    desc = "Layer to add timeseries load objects to base DiTTo model"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('load_path', description='', parser=None,
                            choices=None, nargs=None))
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
    AddTimeseriesLoad.main()

    
