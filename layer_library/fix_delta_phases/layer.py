from __future__ import print_function, division, absolute_import

import os
from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.powertransformer import PowerTransformer
from ditto.models.phase_winding import PhaseWinding
from ditto.models.load import Load

logger = logging.getLogger('layerstack.layers.Fix_Delta_Phases')


class Fix_Delta_Phases(DiTToLayerBase):
    name = "fix_delta_phases"
    uuid = UUID("9f320f05-9319-420a-9ef3-19729ff3c82c")
    version = '0.1.0'
    desc = "Add phase connection information from original Transformers.dss file"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['transformer_file'] = Kwarg(default=None, description='Location or original OpenDSS Transformer file',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['readme_location'] = Kwarg(default=None, description='Location or readme file specifying whether this is a delta system',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        transformer_file = None
        if 'transformer_file' in kwargs:
            transformer_file = kwargs['transformer_file']
        readme_location = None
        if 'readme_location' in kwargs:
            readme_location = kwargs['readme_location']

        if readme_location is not None and os.path.exists(readme_location):
            f_readme = open(readme_location,'r')
            info = f_readme.readline().split()
            suffix = info[1][:-2]
            config = info[5]
            if config == 'delta-delta':
                element_mapping = {}
                f_transformers = open(transformer_file,'r')
                for row in f_transformers.readlines():
                    sp_data = row.split(" ")
                    from_element = None
                    to_element = None
                    phases = None
                    seen=False
                    for sp in sp_data:
                        if sp[:4] =='bus=' and not seen:
                            seen = True
                            full_name = sp[4:]
                            if '.' in full_name:
                                from_element = full_name.split('.')[0]
                                phases = full_name.split('.')[1:]
                            else:
                                phases = [1,2,3]
                                from_element = full_name
                        if sp[:4] =='bus=' and seen:
                            full_name = sp[4:]
                            if '.' in full_name:
                                to_element = full_name.split('.')[0]
                            else:
                                to_element = full_name

                    if from_element is not None and to_element is not None and phases is not None:
                        element_mapping[(from_element.lower(),to_element.lower())] = phases
                
                for obj in model.models:
                    if isinstance(obj,Load):
                        if (not obj.is_center_tap) or len(obj.phase_loads) == 3:
                            obj.connection_type = 'D'
                        else:
                            obj.connection_type = 'Y'

                    if isinstance(obj,PowerTransformer) and obj.windings[0].connection_type == "D":
                        if len(obj.windings[0].phase_windings)==1:
                            correct_phases_dss = element_mapping[(obj.from_element,obj.to_element)]
                            correct_phases = []
                            for st in correct_phases_dss:
                                correct_phases.append(chr(ord('A')-1+int(st)))
                            if len(correct_phases)!=2:
                                print("WARNING - incorrect number of phases read from transformer file")
                            obj.windings[0].phase_windings[0].phase= correct_phases[0]
                            additional_pw = PhaseWinding(model)
                            additional_pw.phase = correct_phases[1]
                            obj.windings[0].phase_windings.append(additional_pw)

                        winding1 = obj.windings[0]
                        winding2 = obj.windings[1]
                        if hasattr(winding1,'phase_windings') and winding1.phase_windings is not None:
                            n_phases = len(winding1.phase_windings)
                            if n_phases ==3:
                                if winding1.nominal_voltage is not None and winding1.nominal_voltage > 30000:
                                    winding1.connection_type = 'D'
                                    winding2.connection_type = 'Y'
                                else:
                                    winding1.connection_type = 'D'
                                    winding2.connection_type = 'D'
                            else:
                                winding1.connection_type = 'D'
                                winding2.connection_type = 'Y'

            else:
                for i in model.models:
                    if isinstance(i,Load):
                        i.connection_type = 'Y'

                    if isinstance(i,PowerTransformer) and i.windings is not None and len(i.windings)>1:
                        winding1 = i.windings[0]
                        winding2 = i.windings[1]
                        if hasattr(winding1,'phase_windings') and winding1.phase_windings is not None:
                            n_phases = len(winding1.phase_windings)
                            if n_phases ==3:
                                winding1.connection_type = 'D'
                                winding2.connection_type = 'Y'
                            else:
                                winding1.connection_type = 'Y'
                                winding2.connection_type = 'Y'

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Fix_Delta_Phases.main()

    
