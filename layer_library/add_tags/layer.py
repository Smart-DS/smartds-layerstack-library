from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
from pathlib import Path
import os
from shutil import copyfile

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.Add_Tags')


class Add_Tags(DiTToLayerBase):
    name = "add_tags"
    uuid = UUID("71a4755e-9ee5-4d86-8b5e-bbf87fe804ca")
    version = '0.1.0'
    desc = "Copy tags into the output folder."

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['output_folder'] = Kwarg(default=None, description='Location where tags should be moved to',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['tag_file'] = Kwarg(default=None, description='Location of tag txt file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        output_folder = None
        tag_file = None
        if 'output_folder' in kwargs:
            output_folder = kwargs['output_folder']
        if 'tag_file' in kwargs:
            tag_file = kwargs['tag_file']

        print(tag_file,output_folder)
        if tag_file is not None and output_folder is not None:
            if os.path.isdir(output_folder) and Path(tag_file).is_file():
                copyfile(tag_file,os.path.join(output_folder,'tags.txt'))

            
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Add_Tags.main()

    
