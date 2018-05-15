from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

from ditto.store import Store
from ditto.readers.cyme.read import Reader as CymeReader

logger = logging.getLogger('layerstack.layers.FromCyme')


class FromCyme(LayerBase):
    name = "From Cyme"
    uuid = UUID("f6a6cd1d-193f-475d-96a2-b9f5d88de202")
    version = 'v0.1.0'
    desc = "Layer to load DiTTo model from Cyme"

    @classmethod
    def args(cls):
        arg_list = super().args()
        arg_list.append(Arg('cyme_model',
                            description='Path to Cyme model to be loaded',
                            parser=str, choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Base directory for argument paths.')
        return kwarg_dict

    @classmethod
    def apply(cls, stack, cyme_location, base_dir=None):

        if not os.path.exists(os.path.join(base_dir,cyme_location)):
            raise ValueError("No folder exists at {}".format(os.path.join(base_dir,cyme_location)))

        base_model = Store()
        reader = CymeReader(data_folder_path=os.path.join(base_dir,cyme_location))
        reader.parse(base_model)
        base_model.set_names()
        stack.model = base_model
        return True


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    FromCyme.main()
