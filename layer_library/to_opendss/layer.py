from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

from ditto.writers.opendss.write import writer as Writer

logger = logging.getLogger('layerstack.layers.ToOpenDSS')


class ToOpenDSS(LayerBase):
    name = "To OpenDSS"
    uuid = "293a0dd3-4065-4602-bb91-919c2001d47d"
    version = 'v0.1.0'
    desc = "Layer to write DiTTo model in OpenDSS format"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('output_path',
                            description='Path to output model to',
                            parser=None, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, output_path):
        writer = Writer(linecodes_flag=True, output_path=output_path)
        writer.write(stack.model, verbose=True)
        return True


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    ToOpenDSS.main()

    