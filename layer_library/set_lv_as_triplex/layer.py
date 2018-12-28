from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.line import Line

logger = logging.getLogger('layerstack.layers.Set_Lv_As_Triplex')


class Set_Lv_As_Triplex(DiTToLayerBase):
    name = "set_lv_as_triplex"
    uuid = UUID("7871e9b2-a4d2-4da7-a86a-0c384b2637a9")
    version = '0.1.0'
    desc = "Replace low voltage overhead lines that are copper with triplex wires"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['to_replace'] = Kwarg(default=None, description='List of nameclasses that get replaced with LV triplex lines',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        to_replace = []
        if 'to_replace' in kwargs:
            to_replace = kwargs['to_replace']
        x0_list = {'Zuzara':0.463,'Rucina':0.6753,'Periwinkle':1.8071}
        x1_list = {'Zuzara':0.0888,'Rucina':0.0956,'Periwinkle':0.1012}
        r0_list = {'Zuzara':0.877,'Rucina':1.2917,'Periwinkle':2.5529}
        r1_list = {'Zuzara':0.2707,'Rucina':0.4291,'Periwinkle':1.365}
        #c0_list = {'Zuzara':8.2283,'Rucina':8.8331,'Periwinkle':9.5016}
        c0_list = {'Zuzara':1.389,'Rucina':2.0259,'Periwinkle':5.4213}
        c1_list = {'Zuzara':61.8052,'Rucina':58.7016,'Periwinkle':54.4840}
        nameclass_list = {'Zuzara':'1P_OH_AL_4/0_Zuzara_0_416_0','Rucina':'1P_OH_AL_2/0_Rucina_0_416_0', 'Periwinkle':'1P_OH_AL_4_Periwinkle_0_416_0'}
        #c1 is B1/(2*pi*60) *1000 (for per meter) from catalog

        for i in model.models:
            if isinstance(i,Line) and i.nameclass is not None:
                for nameclass in to_replace:
                    if nameclass in i.nameclass:
                        if len(i.wires) != 2:
                            print('Warning - expecting two phases')
                        if i.length > 27:
                            name = 'Zuzara'

                        elif i.length <4:
                            name = 'Periwinkle'

                        else:
                            name = 'Rucina'

                        i.nameclass = nameclass_list[name]
                        r0 = r0_list[name]/1000.0
                        r1 = r1_list[name]/1000.0
                        x0 = x0_list[name]/1000.0
                        x1 = x1_list[name]/1000.0
                        c0 = x0_list[name]/1000.0
                        c1 = c1_list[name]/1000.0
                        impedance = [[complex(2*r1+r0,2*x1+x0)/3.0, complex(r0-r1,x0-x1)/3.0],[complex(r0-r1,x0-x1)/3.0,complex(2*r1+r0,2*x1+x0)/3.0]] 
                        capacitance = [[complex(2*c1+c0,0)/3.0, complex(c0-c1,0)/3.0],[complex(c0-c1,0)/3.0,complex(2*c1+c0,0)/3.0]] 
                        i.impedance_matrix = impedance
                        i.capacitance_matrix = capacitance
                        for w in i.wires:
                            w.nameclass = i.nameclass[6:].replace('_','-')



        for i in model.models:
            if isinstance(i,Line) and i.nominal_voltage is not None and i.line_type is not None:
                if i.nominal_voltage < 600:
                    for nc in i.wires:
                        if nc.nameclass is not None and i.line_type == 'overhead':
                            nc.nameclass = 'LV_OH_'+nc.nameclass
                        if nc.nameclass is not None and i.line_type == 'underground':
                            nc.nameclass = 'LV_UG_'+nc.nameclass

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Lv_As_Triplex.main()

    
