from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import os
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

from ditto.writers.opendss.write import Writer as Writer

logger = logging.getLogger('layerstack.layers.ToOpenDSS')


class ToOpenDSS(LayerBase):
    name = "To OpenDSS"
    uuid = UUID("293a0dd3-4065-4602-bb91-919c2001d47d")
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
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Base directory for argument paths.')
        kwarg_dict['separate_feeders'] = Kwarg(default=False, description='Boolean of whether or not to split data folders by feeder_name')
        kwarg_dict['separate_substations'] = Kwarg(default=False, description='Boolean of whther or not to split output data folders by substation_name')
        kwarg_dict['profile_path_res'] = Kwarg(default=None, description='Location where the profiles are for residential loads')
        kwarg_dict['profile_path_com'] = Kwarg(default=None, description='Location where the profiles are for commercial loads')
        kwarg_dict['solve'] = Kwarg(default=True, description='Whether or not to include a solve statement at the end of the file')
        kwarg_dict['remove_loadshapes'] = Kwarg(default=False, description='Whether or not to include a solve statement at the end of the file')
        return kwarg_dict

    @classmethod
    def apply(cls, stack, output_path, base_dir, separate_feeders,separate_substations,profile_path_res,profile_path_com,solve,remove_loadshapes):
        if base_dir and (not os.path.exists(output_path)):
            output_path = os.path.join(base_dir,output_path)

        writer = Writer(linecodes_flag=True, output_path=output_path,profile_path_res=profile_path_res,profile_path_com=profile_path_com,solve=solve,remove_loadshapes=remove_loadshapes)
        logger.debug("Writing {!r} out to {!r}.".format(stack.model,output_path))
        writer.write(stack.model, verbose=False,separate_feeders=separate_feeders, separate_substations=separate_substations) #i.e. break opendss network into subregions
        return True


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    ToOpenDSS.main()

    
