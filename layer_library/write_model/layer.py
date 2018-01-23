from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from ditto.layers.args import Arg, Kwarg
from ditto.layers.layer import ModelType, ModelLayerBase

from ditto.writers.opendss.write import writer as Writer

logger = logging.getLogger('ditto.layers.Write_Model')


class Write_Model(ModelLayerBase):
    name = "Write_Model"
    desc = "Layer to write model out of DiTTo"
    model_type = ModelType.DiTTo

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('output_path',
                            description='Path to output model to',
                            parser=None, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, model, output_path):
        writer = Writer(linecodes_flag=True, output_path=output_path)
        writer.write(model, verbose=True)
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    #
    Write_Model.main()
