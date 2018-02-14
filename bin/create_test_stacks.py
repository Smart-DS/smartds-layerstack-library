import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack

repo_dir = os.path.dirname(os.path.dirname(__file__))
layer_library_dir = os.path.join(repo_dir,'layer_library')
stack_library_dir = os.path.join(repo_dir,'stack_library')


def update_stack_base_dir(stack_name,new_base_dir):
    """
    In this repo, base_dir typically points to a Smart-DS dataset directory. To
    run these stacks on different systems, update them to point to the base_dir
    as it occurs on your system.
    """
    stack_path = os.path.join(stack_library_dir,stack_name)
    stack = Stack.load(stack_path)
    for layer in stack:
        layer.kwargs.mode = ArgMode.USE
        if 'base_dir' in layer.kwargs:
            layer.kwargs['base_dir'] = new_base_dir
    stack.save(stack_path)


def create_test_stack(dataset_dir,dataset_name='dataset3'):
    stack = Stack(name='DiTTo Test Stack {}'.format(dataset_name.title()))
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_substations')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_timeseries_load')))
    stack.append(Layer(os.path.join(layer_library_dir,'scale_loads')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    if not dataset_name:
        dataset_name = os.path.basename(dataset_dir)

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    if dataset_name == 'dataset3':
        from_opendss = stack[0]
        from_opendss.args[0] = os.path.join('mixed_humid','industrial','master.dss')
        from_opendss.args[1] = os.path.join('mixed_humid','industrial','buscoords.dss')
        from_opendss.kwargs['base_dir'] = dataset_dir

        add_substations = stack[1]
        add_substations.args[0] = os.path.join('mixed_humid','industrial','feeders','feeders.txt')
        add_substations.args[1] = os.path.join('post_process','modified_substations')
        add_substations.kwargs['base_dir'] = dataset_dir

        add_timeseries_load = stack[2]
        add_timeseries_load.args[0] = os.path.join('mixed_humid','industrial','consumers&street_map','customers_extended.csv')
        add_timeseries_load.kwargs['base_dir'] = dataset_dir        

        scale_loads = stack[3]
        scale_loads.kwargs['scale_factor'] = 1.1

        to_opendss = stack[4]
        to_opendss.args[0] = os.path.join('post_process','mixed_humid','industrial') 
        to_opendss.kwargs['base_dir'] = dataset_dir
    else:
        raise NotImplementedError("Unknown dataset_name {!r}".format(dataset_name))

    stack.save(os.path.join(stack_library_dir,stack.suggested_filename))


# test_stack_basic.py
#
# add_substations = Add_Substations()
# scale_loads = Scale_Loads()
# add_timeseries_load = Add_Timeseries_Load()
# from_opendss = From_Opendss()
# write_model = Write_Model()
# base_model = Store()
# stack = Stack([from_opendss,write_model])
# base_model = from_opendss.apply(stack,base_model,'data/dataset3/mixed_humid/industrial/OpenDSS/master.dss','data/dataset3/mixed_humid/industrial/OpenDSS/buscoords.dss')
# final_model = write_model.apply(stack, base_model,'data/dataset3/post_process/mixed_humid_raw/industrial/') 

# test_stack_substations.py
#
# add_substations = Add_Substations()
# from_opendss = From_Opendss()
# write_model = Write_Model()
# base_model = Store()
# stack = Stack([from_opendss,add_substations,write_model])
# base_model = from_opendss.apply(stack,base_model,'data/dataset3/mixed_humid/industrial/OpenDSS/master.dss','data/dataset3/mixed_humid/industrial/OpenDSS/buscoords.dss')
# substation_model = add_substations.apply(stack,base_model,'data/dataset3/mixed_humid/industrial/feeders/feeders.txt','data/substations','data/dataset3/post_process/modified_substations')
# final_model = write_model.apply(stack, substation_model,'data/dataset3/post_process/mixed_humid_subs/industrial/') 

