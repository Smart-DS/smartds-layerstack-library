from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

from ditto.metrics.network_analysis import network_analyzer
from ditto.modify.system_structure import system_structure_modifier

logger = logging.getLogger('layerstack.layers.SceMetricComputationLayer')


class SceMetricComputationLayer(DiTToLayerBase):
    name = "SCE metric computation layer"
    uuid = UUID("c302e3fa-5117-4ae4-b776-1a8a87b1e1c7")
    version = '0.1.0'
    desc = "Compute the metrics for SCE feeders."

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['feeder_name'] = Kwarg(default=None, description='Name of the feeder being parsed.',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['output_filename_xlsx'] = Kwarg(default='./', description='Path to output the excel metric file.',
                                                   parser=None, choices=None,
                                                   nargs=None, action=None)
        kwarg_dict['output_filename_json'] = Kwarg(default='/', description='Path to output the JSON metric file.',
                                                   parser=None, choices=None,
                                                   nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        model.set_names()

        if "feeder_name" in kwargs:
            feeder_name = kwargs["feeder_name"]
        else:
            feeder_name = "sce_feeder"

        if "output_filename_xlsx" in kwargs:
            output_filename_xlsx = kwargs["output_filename_xlsx"]
        else:
            output_filename_xlsx = '{}.xlsx'.format(feeder_name)

        if "output_filename_json" in kwargs:
            output_filename_json = kwargs["output_filename_json"]
        else:
            output_filename_json = '{}.json'.format(feeder_name)

        #Create the modifier object
        modifier = system_structure_modifier(model)

        #Set the nominal voltages
        modifier.set_nominal_voltages_recur()
        modifier.set_nominal_voltages_recur_line()

        #Create the network analyzer
        network_analyst=network_analyzer(modifier.model)
        network_analyst.model.set_names()
        network_analyst.compute_all_metrics(feeder_name)

        #Export the metrics
        network_analyst.export(output_filename_xlsx)
        network_analyst.export_json(output_filename_json)

        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via
    #     layerstack.start_console_log
    #
    SceMetricComputationLayer.main()


