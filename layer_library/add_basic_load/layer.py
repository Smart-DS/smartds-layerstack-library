from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from ditto.layers.args import Arg, Kwarg
from ditto.layers.layer import ModelType, ModelLayerBase

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.modify.modify import Modifier

logger = logging.getLogger('ditto.layers.Add_Basic_Load')


class Add_Basic_Load(ModelLayerBase):
    name = "Add_Basic_Load"
    desc = "Layer to add load to base DiTTo model from a CSV file"
    model_type = ModelType.DiTTo

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
    Add_Load.main()
