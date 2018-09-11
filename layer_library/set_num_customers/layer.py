from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.load import Load

logger = logging.getLogger('layerstack.layers.Set_Num_Customers')


class Set_Num_Customers(DiTToLayerBase):
    name = "set_num_customers"
    uuid = UUID("04711fc4-f6fc-41f8-87ad-770116ff84e6")
    version = '0.1.0'
    desc = "Set the number of customers to the loads"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['num_customers'] = Kwarg(default=None, description='Number of customers at each load')
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        num_customers = None
        if 'num_customers' in kwargs:
            num_customers = float(kwargs['num_customers'])

        if num_customers is not None:
            for i in model.models:
                if isinstance(i,Load):
                    i.num_users = num_customers 

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Num_Customers.main()

    
