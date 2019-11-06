from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.regulator import Regulator

logger = logging.getLogger('layerstack.layers.Fix_Regulator_Voltage')


class Fix_Regulator_Voltage(DiTToLayerBase):
    name = "fix_regulator_voltage"
    uuid = UUID("746905bd-92f2-4c81-b245-f11a5e6a04b3")
    version = '0.1.0'
    desc = "Some regulators from RNM are at 7.2 not 12.47kv"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        for i in model.models:
            if isinstance(i,Regulator):
                #import pdb;pdb.set_trace()
                if i.windings is not None and len(i.windings) == 2 and round(i.windings[0].nominal_voltage/1000.0,2) == 7.2:
                    print('direct '+i.name,i.windings[0].nominal_voltage)
                    i.windings[0].nominal_voltage = 12470
                    i.windings[1].nominal_voltage = 12470
                    i.pt_ratio = 60.0
                if i.connected_transformer is not None and i.connected_transformer in model.model_names:
                    trans = model[i.connected_transformer]
                    if trans.windings is not None and len(trans.windings) == 2 and round(trans.windings[0].nominal_voltage/1000.0,2) == 7.2:
                        print(trans.name,trans.windings[0].nominal_voltage)
                        trans.windings[0].nominal_voltage = 12470
                        trans.windings[1].nominal_voltage = 12470
                        i.pt_ratio = 60.0
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Fix_Regulator_Voltage.main()

    
