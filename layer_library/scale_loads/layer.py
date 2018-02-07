from __future__ import print_function, division, absolute_import

from builtins import super
from random import shuffle
import logging

from layerstack.args import Arg, Kwarg
from ditto.layerstack import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.ScaleLoads')

from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.modify.modify import Modifier
from ditto.models.load import Load
from ditto.models.load import Timeseries


class ScaleLoads(DiTToLayerBase):
    name = "Scale Loads"
    uuid = "9aa14dff-f1c1-4c16-abc0-d6ff2ee9606c"
    version = 'v0.1.0'
    desc = "Layer to scale timeseries load objects for different years"

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['random_percent'] = Kwarg(default=None, description='',
            parser=None, choices=None,nargs=None, action=None)
        kwarg_dict['scale_factor'] = Kwarg(default=None, description='',
            parser=None, choices=None,nargs=None, action=None)
        kwarg_dict['timeseries_path'] = Kwarg(default=None, description='',
            parser=None, choices=None,nargs=None, action=None)
        return kwarg_dict

    # This function multiplies an entire (e.g. yearly) timeseries load by a single number
    # Random_percent applies this scaling to a random percentage of the loads
    # The timeseries_path can be used for applying different scaling factors to different customers which are specified in the csv file
    # TODO: Decid the most modular way to multiply timeseries objects using something like set_attributes in modify.py. I think create a new function called scale_timeseries which specifically multiplies the corresponding timeseries objects. 
    # TODO: When reading from timeseries_path create a new load object with the specified name and populate the timeseries attribute
    # TODO: When applying scaling from random_percent (e.g. 100), then create a new Load object with the right name, and fill it with a timeseries to multiply with.
    # TODO: Then call scale_timeseries in modify.py to multiply the objects
    # TODO: Create an extension of this layer for scaling which is different throughout the year
    @classmethod
    def apply(cls, stack, model, random_percent=None, scale_factor=None, timeseries_path=None):
        if timeseries_path is not None:
            scale_factor_model= Store()
            reader = CsvReader()
            reader.parse(sc_factor_model, scaling_path)
            modifier = Modifier()
            intermediate_model = modifier.merge(model, scale_factor_model)
            return intermediate_model

        if random_percent == None:
            random_percent = 100

        if scale_factor is not None:
            scale_factor_model = Store()
            modifier = Modifier()
            total_loads = 0
            for obj_name in model.model_names:
                if isinstance(model.model_names[obj_name], Load):
                    total_loads = total_loads +1

            num_selected = int(random_percent/100.0*total_loads)
            to_select = [1 for i in range(num_selected)] + [0 for i in range(total_loads-num_selected)]
            shuffle(to_select)
            load_cnt = 0
            for obj_name in model.model_names:
                if isinstance(model.model_names[obj_name], Load) and to_select[load_cnt] == 1:
                    tmp_load = Load(scale_factor_model)
                    tmp_timeseries = Timeseries(scale_factor_model)
                    tmp_timeseries.scale_factor = scale_factor
                    tmp_load.name = obj_name
                    tmp_load.timeseries = [tmp_timeseries]
                    modifier.set_attributes(model, model.model_names[obj_name], tmp_load)

            model.set_names()
            return model
        else:
            logger.warn('no scaling factor set')
            return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    # 
    ScaleLoads.main()

    