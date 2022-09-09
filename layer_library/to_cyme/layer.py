from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase
import os
import pyproj
from ditto.writers.cyme.write import Writer as CymeWriter
from ditto.models.line import Line
from ditto.models.load import Load
from ditto.models.powertransformer import PowerTransformer
from ditto.models.regulator import Regulator
from ditto.models.storage import Storage
from ditto.models.photovoltaic import Photovoltaic
from ditto.models.base import Unicode
from ditto.models.phase_storage import PhaseStorage

import shutil
import random
logger = logging.getLogger('layerstack.layers.To_Cyme')


class To_Cyme(LayerBase):
    name = "to_cyme"
    uuid = UUID("39bd3f89-9f08-4ef6-873a-28c393fb32dd")
    version = '0.1.0'
    desc = "Layer to write the model to cyme"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('output_path', description='path to folder where cyme files are written'))
        arg_list.append(Arg('dataset', description='dataset name'))
        arg_list.append(Arg('cyme_curve_folder', description='location where cyme volt-var and volt-watt curves are'))
        arg_list.append(Arg('solar', description='solar scenario'))
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        kwarg_dict['base_dir'] = Kwarg(default=None, description='Base directory for argument paths')
        return kwarg_dict

    @classmethod
    def apply(cls, stack, output_path, dataset, cyme_curve_folder, solar,  base_dir = None):
        if base_dir and (not os.path.exists(output_path)):
            output_path = os.path.join(base_dir,output_path)

        if dataset == 'Full_Texas': #Don't write cyme in this case
            return True

        # Use state-plane projection
        projection = {'dataset_4':10, 'dataset_3':17, 'dataset_2':13,'t_and_d':14,'houston':14,'texas_rural':14,'South_Texas':14,'texas_test':14,'Full_Texas':14}
        folder_location = None
        proj = pyproj.Proj(proj='utm',zone=projection[dataset],ellps='WGS84', preserve_units=False)
        for i in stack.model.models:
            if hasattr(i,"positions") and i.positions is not None and len(i.positions) >0:
                for pos in i.positions:
                    lon = pos.long
                    lat = pos.lat
                    x,y = proj(lon,lat)
                    pos.long = x
                    pos.lat = y

        ###
        # Find the upstream transformer names
        to_element_map = {}
        from_element_map = {}
        for i in stack.model.models:
            if hasattr(i,'from_element'):
                from_element_map[i.from_element] = i
            if hasattr(i,'to_element'):
                to_element_map[i.to_element] = i

#        for i in stack.model.models:#For delta systems we randomly assign one of the two phases to connect the center tap transformer
#            if isinstance(i,PowerTransformer) and len(i.windings[0].phase_windings) ==2:
#                random.seed(hash(i.name))
#                i.windings[0].phase_windings = [i.windings[0].phase_windings[random.randint(0,1)]]
        for i in stack.model.models:
            if (isinstance(i,Load) or isinstance(i,Photovoltaic) or isinstance(i,Storage)) and i.nominal_voltage < 1000: #voltage check added to deal with MV loads
                curr_element = i
                to_element = i.connecting_element
                seen = set()
                lv_lines = []
                while not isinstance(curr_element,PowerTransformer):
                    seen.add(to_element)
                    curr_element = to_element_map[to_element]
                    to_element = curr_element.from_element
                    if to_element in seen:
                        to_element = curr_element.to_element
                    if to_element is None or to_element in seen:
                        print('problem with load '+i.name)
                        break
                    if isinstance(i,Load) and isinstance(curr_element,Line): #only adjust the lines when updating a load
                        lv_lines.append(curr_element)
                if isinstance(curr_element,PowerTransformer):
                    num_phases = len(curr_element.windings[0].phase_windings)
                    phases = []
                    for pw in range(num_phases):
                        phases.append(curr_element.windings[0].phase_windings[pw].phase)
                    if num_phases ==1:
                        phase = phases[0]
                    phases = set(phases)
                    if num_phases ==2:
                        if 'A' in phases and 'B' in phases:
                            phase = 'A'
                        if 'B' in phases and 'C' in phases:
                            phase = 'B'
                        if 'C' in phases and 'A' in phases:
                            phase = 'C'
                    if isinstance(i,Load):
                        i.upstream_transformer_name = curr_element.name
                        if len(curr_element.windings) ==3:
                            i.is_center_tap = True
                            # We have phases A and B in OpenDSS. Use them here for CYME logic with renamed phases and one dropped
                            i.phase_loads[0].phase = phase
                            i.phase_loads[1].drop = True
                            i.phase_loads[0].p += i.phase_loads[1].p
                            i.phase_loads[0].q += i.phase_loads[1].q
                                
                            i.center_tap_perct_1_N = 50
                            i.center_tap_perct_N_2 = 50
                            i.center_tap_perct_1_2 = 0
                            for line in lv_lines:
                                line.wires[0].phase = phase
                                line.wires[1].drop = True
                    elif isinstance(i,Photovoltaic):
                        if len(curr_element.windings) ==3:
                            i.phases = [Unicode(phase)]
                    elif isinstance(i,Storage):
                        if len(curr_element.windings) ==3:
                            phase_storage = PhaseStorage(stack.model)
                            phase_storage.phase = phase
                            # No kW power output since models use idling mode
                            i.phase_storages = [phase_storage]

        ####


        #import pdb;pdb.set_trace()

            
        logger.info('Writing {!r} out to {!r}.'.format(stack.model,output_path))
        writer = CymeWriter(output_path = output_path,log_path=output_path)
        writer.write(stack.model)

        if solar == 'high' or solar == 'extreme':
            shutil.copyfile(os.path.join(cyme_curve_folder,'1547_VOLT-VAR_CAT_B.cymcfg'),os.path.join(output_path,'1547_VOLT-VAR_CAT_B.cymcfg'))
        if solar == 'extreme':
            shutil.copyfile(os.path.join(cyme_curve_folder,'1547_VOLT-WATT_CAT_B.cymcfg'),os.path.join(output_path,'1547_VOLT-WATT_CAT_B.cymcfg'))
        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    To_Cyme.main()

    
