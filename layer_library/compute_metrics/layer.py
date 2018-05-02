from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

from ditto.metrics.network_analysis import network_analyzer

logger = logging.getLogger('layerstack.layers.Compute_Metrics')


class Compute_Metrics(LayerBase):
    name = "compute_metrics"
    uuid = "UUID(18b94030-ca09-40ca-9ea0-b9cb1c9090fb)"
    version = '0.1.0'
    desc = "Layer to compute the metrics and write them out to xlsx and json"

    @classmethod
    def args(cls):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['excel_output'] = Kwarg(default=None, description='path to the output file for xlsx export',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['json_output'] = Kwarg(default=None, description='path to the output file for json export',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        if 'excel_output' in kwargs:
            excel_output = kwargs['excel_output']
        else:
            raise ValueError('Missing output file name for excel')

        if 'json_output' in kwargs:
            json_output = kwargs['json_output']
        else:
            raise ValueError('Missing output file name for json')

        #Create a network analyzer object
        #TODO: When calling the network_split layer before, this step is
        #done twice which is a waste of time...
        network_analyst = network_analyzer(stack.model)

        #Set the names
        network_analyst.model.set_names()

        #Compute the metrics
        network_analyst.compute_all_metrics_per_feeder()
        
        #Export metrics to Excel
        network_analyst.export(excel_output)
        
        #Export metrics to JSON
        network_analyst.export_json(json_output)

        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Compute_Metrics.main()

    