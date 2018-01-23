from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from ditto.layers.args import Arg, Kwarg
from ditto.layers.layer import ModelType, ModelLayerBase

import os
from ditto.store import Store
from ditto.readers.csv.read import reader as CsvReader
from ditto.readers.opendss.read import reader as OpenDSSReader
from ditto.modify.modify import Modifier

logger = logging.getLogger('ditto.layers.Clean_Up_Substations')


class Clean_Up_Substations(ModelLayerBase):
    name = "Clean_Up_Substations"
    desc = "Layer to clean up substations after adding load"
    model_type = ModelType.DiTTo

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('sub_internals',
                            description='Path to substations internals',
                            parser=str, choices=None, nargs=None))
        return arg_list

    @classmethod
    def apply(cls, stack, model, sub_internals):
        reduced_model = model
        modifier = Modifier()
        csv_reader = CsvReader()
        for sub in os.listdir(sub_internals):
            to_delete = Store()
            to_delete2 = Store()
            to_delete3 = Store()
            sub_lines = os.path.join(sub_internals, sub, 'internals_lines.csv')
            csv_reader.parse(to_delete, sub_lines)
            sub_nodes = os.path.join(sub_internals, sub, 'internals_nodes.csv')
            csv_reader.parse(to_delete2, sub_nodes)
            to_delete = modifier.add(to_delete, to_delete2)
            sub_transformers = os.path.join(sub_internals, sub,
                                            'internals_transformers.csv')
            csv_reader.parse(to_delete3, sub_transformers)
            to_delete = modifier.add(to_delete, to_delete3)

            reduced_model = modifier.delete(reduced_model, to_delete)

        substation = Store()
        final_model = reduced_model
        for sub in os.listdir(sub_internals):
            odss_reader = OpenDSSReader()
            sub_master = os.path.join(sub_internals, sub, 'master.dss')
            odss_reader.build_opendssdirect(sub_master)
            sub_bus_coords = os.path.join(sub_internals, sub, 'Buscoords.dss')
            odss_reader.set_dss_file_names({'Nodes': sub_bus_coords})
            odss_reader.parse(substation, verbose=True)

            final_model = modifier.add(final_model, substation)

        return final_model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    #
    Clean_Up_Substations.main()
