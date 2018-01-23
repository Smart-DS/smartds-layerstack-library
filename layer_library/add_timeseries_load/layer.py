from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from ditto.layers.args import Arg, Kwarg
from ditto.layers.layer import ModelType, ModelLayerBase

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.modify.modify import Modifier

logger = logging.getLogger('ditto.layers.Add_Timeseries_Load')


class Add_Timeseries_Load(ModelLayerBase):
    name = "Add_Timeseries_Load"
    desc = "Layer to add timeseries load objects to base DiTTo model"
    model_type = ModelType.DiTTo

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
    Add_Timeseries_Load.main()
