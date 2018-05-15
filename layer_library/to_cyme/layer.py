from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase
import os
from ditto.writers.cyme.write import Writer as CymeWriter

logger = logging.getLogger('layerstack.layers.To_Cyme')


class To_Cyme(LayerBase):
    name = "to_cyme"
    uuid = UUID("39bd3f89-9f08-4ef6-873a-28c393fb32dd")
    version = '0.1.0'
    desc = "Layer to write the model to cyme"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('output_path', description='path to folder where cyme files are written'))
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Base directory for argument paths')
        return kwarg_dict

    @classmethod
    def apply(cls, stack, output_path, base_dir = None):
        if base_dir and (not os.path.exists(output_path)):
            output_path = os.path.join(base_dir,output_path)
            
        logger.info('Writing {!r} out to {!r}.'.format(stack.model,output_path))
        writer = CymeWriter(output_path = output_path,log_path=output_path)
        writer.write(stack.model)
        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    To_Cyme.main()

    
