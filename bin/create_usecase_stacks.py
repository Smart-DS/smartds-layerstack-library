from enum import Enum, auto
import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack
from helpers import layer_library_dir, stack_library_dir, placement_library_dir

DATASET3_FEEDER_TYPES = ['industrial','rural','urban-suburban']
DATASET3_CLIMATE_ZONES = ['MixedHumid','CoolDry']

def dataset3_snapshot(dataset_dir,
                      climate_zone='MixedHumid',
                      feeder_type='industrial',
                      pct_customers=10):
    stack_name = "Dataset3 Snapshot {}, {}, {} Percent of Customers".format(
        climate_zone,feeder_type,pct_customers)
    short_name = 'ds3_snap_{}_{}_{}pct_customers'.format(
        climate_zone,feeder_type,pct_customers)

    stack = Stack(name=stack_name)
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'create_placement')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_storage')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    from_opendss = stack[0]
    from_opendss.args[0] = os.path.join(climate_zone,feeder_type,'OpenDSS','master.dss')
    from_opendss.args[1] = os.path.join(climate_zone,feeder_type,'OpenDSS','buscoords.dss')
    from_opendss.kwargs['base_dir'] = dataset_dir

    feeders = 'all'
    equipment_type = 'ditto.models.load.Load'
    selection = ('Random',pct_customers)
    seed = 1
    placement_folder = os.path.join(placement_library_dir,'dataset3',climate_zone,feeder_type)
    file_name = feeders+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'_'+str(seed)+'.txt'
    
    create_placement = stack[1]
    create_placement.args[0] = feeders
    create_placement.args[1] = equipment_type
    create_placement.args[2] = selection
    create_placement.args[3] = seed
    create_placement.args[4] = placement_library_dir
    create_placement.args[5] = file_name

    add_pv = stack[2]
    add_pv.args[0] = os.path.join(placement_folder,file_name) # placement
    add_pv.args[1] = 10                                       # rated power
    add_pv.args[2] = 1.0                                      # power factor

    add_storage = stack[3]
    add_storage.args[0] = os.path.join(placement_folder,file_name) # placement
    add_storage.args[1] = 8                                        # rated power
    add_storage.args[2] = 16                                       # rated kWh

    to_opendss = stack[4]
    to_opendss.args[0] = '.' # output to run directory

    stack.save(os.path.join(stack_library_dir,short_name + '.json'))


def dataset3_timeseries(dataset_dir,
                        climate_zone='MixedHumid',
                        feeder_type='industrial',
                        pct_energy_efficiency=10):  
    stack_name = "Dataset3 Timeseries {}, {}, {} Percent Energy Efficient".format(
        climate_zone,feeder_type,pct_energy_efficiency)
    short_name = 'ds3_timeseries_{}_{}_{}pct_ee'.format(
        climate_zone,feeder_type,pct_energy_efficiency)

    stack = Stack(name=stack_name)
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_substations')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_timeseries_load')))
    stack.append(Layer(os.path.join(layer_library_dir,'scale_loads')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    from_opendss = stack[0]
    from_opendss.args[0] = os.path.join(climate_zone,feeder_type,'OpenDSS','master.dss')
    from_opendss.args[1] = os.path.join(climate_zone,feeder_type,'OpenDSS','buscoords.dss')
    from_opendss.kwargs['base_dir'] = dataset_dir

    add_substations = stack[1]
    add_substations.args[0] = os.path.join(climate_zone,feeder_type,'feeders','feeders.txt')
    add_substations.args[1] = os.path.join('post_process','modified_substations')
    add_substations.kwargs['base_dir'] = dataset_dir

    add_timeseries_load = stack[2]
    add_timeseries_load.args[0] = os.path.join(climate_zone,feeder_type,'Inputs','customers_extended.txt')
    add_timeseries_load.kwargs['base_dir'] = dataset_dir        

    scale_loads = stack[3]
    scale_loads.kwargs['scale_factor'] = 1.0 - float(pct_energy_efficiency) / 100.0

    to_opendss = stack[4]
    to_opendss.args[0] = '.'

    stack.save(os.path.join(stack_library_dir,short_name + '.json'))
