from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.powertransformer import PowerTransformer
from ditto.models.regulator import Regulator
from ditto.models.winding import Winding
from ditto.models.phase_winding import PhaseWinding
from ditto.modify.modify import Modifier

logger = logging.getLogger('layerstack.layers.Add_Rnm_Regulators')


class Add_Rnm_Regulators(DiTToLayerBase):
    name = "add_rnm_regulators"
    uuid = UUID("d71e8449-ef20-42a6-aef0-8bbabb364fb4")
    version = '0.1.0'
    desc = "Add regulator controls using the RNM naming scheme"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['rnm_name'] = Kwarg(default=None, description='The prefix used in RNM for Transformers which are regulators',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['setpoint'] = Kwarg(default=None, description='The regulator setpoint',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):

        rnm_name = None
        setpoint = None
        if 'rnm_name' in kwargs:
            rnm_name = kwargs['rnm_name']
        if 'setpoint' in kwargs:
            setpoint = kwargs['setpoint']
        for m in model.models:
            if isinstance(m,PowerTransformer) and hasattr(m,'name') and rnm_name.lower() in m.name:
                api_regulator = Regulator(model)
                api_regulator.name = 'reg_'+m.name
                api_regulator.from_element = m.from_element
                api_regulator.to_element = m.to_element
                api_regulator.positions = m.positions
                windings = []
                if m.windings is not None and len(m.windings)>0:
                    for w in m.windings:
                        winding = Winding(model)
                        winding.nominal_voltage = w.nominal_voltage
                        winding.voltage_type = w.voltage_type
                        winding.resistance = w.resistance
                        winding.rated_power = w.rated_power
                        phase_windings = []
                        if w.phase_windings is not None and len(w.phase_windings)>0:
                            for p in w.phase_windings:
                                phase_winding = PhaseWinding(model)
                                phase_winding.phase = p.phase
                                phase_windings.append(phase_winding)
                        winding.phase_windings = phase_windings
                        windings.append(winding)
                api_regulator.windings = windings


                api_regulator.ltc = 0
                api_regulator.is_subtation = 0
                api_regulator.pt_ratio = float(m.windings[0].nominal_voltage)/120.0/(3**0.5)
                api_regulator.ct_ratio = 100.0
                api_regulator.bandwidth = 2.0
                if setpoint is not None:
                    api_regulator.setpoint = setpoint
                modifier = Modifier()
                modifier.delete_element(model,m)

                
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Add_Rnm_Regulators.main()

    
