from __future__ import print_function, division, absolute_import

from builtins import super
import logging
import networkx as nx
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.modify.system_structure import system_structure_modifier
from ditto.models.feeder_metadata import Feeder_metadata
from ditto.models.line import Line
from ditto.models.power_source import PowerSource
from ditto.network.network import Network
import numpy as np

logger = logging.getLogger('layerstack.layers.PostProcessing')


class PostProcessing(DiTToLayerBase):
    name = "post-processing"
    uuid = UUID("958b5e41-be14-49c4-8a1b-f03a412d003e")
    version = '0.1.0'
    desc = "runs multiple post-processing operations"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['path_to_feeder_file'] = Kwarg(default=None, description='Path to feeder.txt',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['path_to_switching_devices_file'] = Kwarg(default=None, description='Path to switching_devices.dss',
                                                            parser=None, choices=None,
                                                            nargs=None, action=None)
        kwarg_dict['switch_to_recloser'] = Kwarg(default=False, description='If True does the switch to recloser post-processing',
                                                            parser=None, choices=None,
                                                            nargs=None, action=None)
        kwarg_dict['center_tap_postprocess'] = Kwarg(default=False, description='If True the phases downstream of center tap transformer are reorganized to reflect the phase of the transformer',
                                                            parser=None, choices=None,
                                                            nargs=None, action=None)
        return kwarg_dict
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        path_to_feeder_file = None
        path_to_switching_devices_file = None
        center_tap_postprocess = False
        switch_to_recloser = False
        if 'path_to_feeder_file' in kwargs:
            path_to_feeder_file = kwargs['path_to_feeder_file']   

        if 'path_to_switching_devices_file' in kwargs:
            path_to_switching_devices_file = kwargs['path_to_switching_devices_file']    

        if 'switch_to_recloser' in kwargs:
            switch_to_recloser = kwargs['switch_to_recloser']

        if 'center_tap_postprocess' in kwargs:
            center_tap_postprocess = kwargs['center_tap_postprocess']
        
        #Create the modifier object
        modifier=system_structure_modifier(model,'st_mat')

        #Center-tap loads
        if center_tap_postprocess:
            modifier.center_tap_load_preprocessing()

        #Set node nominal voltages
        modifier.set_nominal_voltages_recur()

        #Set line nominal voltages
        modifier.set_nominal_voltages_recur_line()

        #Create Feeder_metadata objects for each feeder    

        #Open and read feeder.txt
        with open(path_to_feeder_file, 'r') as f:
            lines = f.readlines()

        all_feeder_data = set()
        for line in lines[1:]:
            #Parse the line
            node,sub,feed,sub_trans = map(lambda x:x.strip().lower(), line.split(' '))
            sub_trans = sub_trans.replace('ctrafo','tr')
            all_feeder_data.add((feed,sub,sub_trans))

        for feeder in all_feeder_data:
            modifier.set_feeder_metadata(feeder[0],feeder[1],feeder[2])

        
        for i in modifier.model.models:
            if isinstance(i,PowerSource) and hasattr(i,'is_sourcebus') and i.is_sourcebus ==1:
                i.positive_sequence_impedance = complex(1.1208,3.5169)
                i.zero_sequence_impedance = complex(1.1208,3.5169)
        

        #Set headnodes for each feeder
        modifier.set_feeder_headnodes()

        #Replace all switchin devices ampacity 3000.0 default values with nans
        #such that we can call the modifier method on it
        for obj in modifier.model.models:
            if isinstance(obj,Line):
                if obj.is_switch == 1 or obj.is_breaker == 1 or obj.is_sectionalizer ==1 or obj.is_fuse == 1 or obj.is_recloser == 1:
                    for w in obj.wires:
                        if w.ampacity == 3000.0:
                            w.ampacity = np.nan
                    
        #Do the actual mdifications
        modifier.set_switching_devices_ampacity()

        #Open the switches which need to be opened.
        modifier.open_close_switches(path_to_switching_devices_file)

        tmp_net = Network()    
        tmp_net.build(modifier.model,'st_mat')
        tmp_net.set_attributes(modifier.model)
        tmp_net.remove_open_switches(modifier.model)
        print(len(nx.cycle_basis(tmp_net.graph)))
        print(nx.cycle_basis(tmp_net.graph))

        #Create the sub-transmission Feeder_metadata
        if not 'subtransmission' in modifier.model.model_names.keys():
            api_feeder_metadata = Feeder_metadata(modifier.model)
            api_feeder_metadata.name = 'subtransmission'
            api_feeder_metadata.substation = modifier.source
            api_feeder_metadata.headnode = modifier.source
            api_feeder_metadata.transformer = modifier.source

        #switch to recloser post-processing
#        if switch_to_recloser:
#            modifier.replace_first_switch_with_recloser()
                    
        #Return the modified model
        return modifier.model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    PostProcessing.main()

    
