from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.regulator import Regulator

logger = logging.getLogger('layerstack.layers.Set_Ltc_Controls')


class Set_Ltc_Controls(DiTToLayerBase):
    name = "set_ltc_controls"
    uuid = UUID("959223ec-059b-43a5-95b8-e1b4a0afba68")
    version = '0.1.0'
    desc = "Layer to apply the LTC setpoints and controls in DiTTo"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['setpoint'] = Kwarg(default=105, description='Percentage per unit of LTC regulators',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        # TODO: Add other values other than setpoint which can be applied for the ltc controls        
        setpoint = None
        if 'setpoint' in kwargs:
            setpoint = kwargs['setpoint']
        for i in model.models:
            if isinstance(i,Regulator) and hasattr(i,'ltc') and i.ltc is not None and i.ltc:
                if hasattr(i,'setpoint') and setpoint is not None:
                    i.setpoint = float(setpoint)
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Ltc_Controls.main()

    
