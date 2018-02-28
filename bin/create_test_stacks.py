import logging
import os

logger = logging.getLogger(__name__)

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # This is in bin so need to go one level up
layer_library_dir = os.path.join(repo_dir,'layer_library')
stack_library_dir = os.path.join(repo_dir,'stack_library')
placement_library_dir = os.path.join(repo_dir,'placement_library')


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


def create_test_stack_basic(dataset_dir,dataset_name='dataset3'):
    global placement_library_dir, layer_library_dir, stack_library_dir,repo_dir
    stack = Stack(name='DiTTo Test Stack Basic {}'.format(dataset_name.title()))

    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    if not dataset_name:
        dataset_name = os.path.basename(dataset_dir)

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    if dataset_name == 'dataset3':
        from_opendss = stack[0]
        from_opendss.args[0] = os.path.join('mixed_humid','industrial','OpenDSS','master.dss')
        from_opendss.args[1] = os.path.join('mixed_humid','industrial','OpenDSS','buscoords.dss')
        from_opendss.kwargs['base_dir'] = dataset_dir

        to_opendss = stack[1]
        to_opendss.args[0] = os.path.join('post_process','mixed_humid','industrial') 
        to_opendss.kwargs['base_dir'] = dataset_dir
    else:
        raise NotImplementedError("Unknown dataset_name {!r}".format(dataset_name))

    stack.save(os.path.join(stack_library_dir,stack.suggested_filename))


def create_test_stack_substations(dataset_dir,dataset_name='dataset3'):
    global placement_library_dir, layer_library_dir, stack_library_dir,repo_dir
    stack = Stack(name='DiTTo Test Stack Substations {}'.format(dataset_name.title()))
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_substations')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    if not dataset_name:
        dataset_name = os.path.basename(dataset_dir)

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    if dataset_name == 'dataset3':
        from_opendss = stack[0]
        from_opendss.args[0] = os.path.join('mixed_humid','industrial','OpenDSS','master.dss')
        from_opendss.args[1] = os.path.join('mixed_humid','industrial','OpenDSS','buscoords.dss')
        from_opendss.kwargs['base_dir'] = dataset_dir

        add_substations = stack[1]
        add_substations.args[0] = os.path.join('mixed_humid','industrial','feeders','feeders.txt')
        add_substations.args[1] = os.path.join('post_process','modified_substations')
        add_substations.kwargs['base_dir'] = dataset_dir

        to_opendss = stack[2]
        to_opendss.args[0] = os.path.join('post_process','mixed_humid','industrial') 
        to_opendss.kwargs['base_dir'] = dataset_dir        
    else:
        raise NotImplementedError("Unknown dataset_name {!r}".format(dataset_name))

    stack.save(os.path.join(stack_library_dir,stack.suggested_filename))
    

def create_test_stack_DERs(dataset_dir,dataset_name='dataset3'):
    global placement_library_dir, layer_library_dir, stack_library_dir,repo_dir
    stack = Stack(name='DiTTo Test Stack DERs {}'.format(dataset_name.title()))
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'create_placement')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_pv')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_storage')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))
    # TODO: add the other layer pieces here too.

    if not dataset_name:
        dataset_name = os.path.basename(dataset_dir)

    for layer in stack:
        layer.args.mode = ArgMode.USE
        layer.kwargs.mode = ArgMode.USE

    if dataset_name == 'dataset3':
        from_opendss = stack[0]
        from_opendss.args[0] = os.path.join('mixed_humid','industrial','OpenDSS','master.dss')
        from_opendss.args[1] = os.path.join('mixed_humid','industrial','OpenDSS','buscoords.dss')
        from_opendss.kwargs['base_dir'] = dataset_dir

        feeders = 'all'
        equipment_type = 'ditto.models.load.Load'
        selection = ('Random',10)
        seed = 1
        placement_folder = placement_library_dir
        file_name = feeders+'_'+equipment_type.split('.')[-1]+'_'+selection[0]+'-'+str(selection[1])+'_'+str(seed)+'.txt'
        
        create_placement = stack[1]
        create_placement.args[0] = 'all'
        create_placement.args[1] = 'ditto.models.load.Load'
        create_placement.args[2] = ('Random',10)
        create_placement.args[3] = 1
        create_placement.args[4] = placement_library_dir
        create_placement.args[5] = file_name

        add_pv = stack[2]
        add_pv.args[0] = os.path.join(placement_folder,file_name)
        add_pv.args[1] = 10
        add_pv.args[2] = 1.0

        add_storage = stack[3]
        add_storage.args[0] = os.path.join(placement_folder,file_name)
        add_storage.args[1] = 8
        add_storage.args[2] = 14

        to_opendss = stack[4]
        to_opendss.args[0] = os.path.join('post_process','mixed_humid','industrial') 
        to_opendss.kwargs['base_dir'] = dataset_dir        


    else:
        raise NotImplementedError("Unknown dataset_name {!r}".format(dataset_name))

    stack.save(os.path.join(stack_library_dir,stack.suggested_filename))

def create_test_stack(dataset_dir,dataset_name='dataset3'):
    """
    Saves a DiTTo test stack to the stack_library.

    :param dataset_dir: Directory where the Smart-DS dataset resides
    :type dataset_dir: str
    :param dataset_name: Name of the Smart-DS dataset
    :type dataset_name: str
    """
    global placement_library_dir, layer_library_dir, stack_library_dir,repo_dir
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
        from_opendss.args[0] = os.path.join('mixed_humid','industrial','OpenDSS','master.dss')
        from_opendss.args[1] = os.path.join('mixed_humid','industrial','OpenDSS','buscoords.dss')
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

def main():
    create_test_stack_DERs('/home/telgindy/Ditto/DiTTo/data/dataset3')
    update_stack_base_dir('../stack_library/ditto_test_stack_ders_dataset3.json','../../dataset3')
    from layerstack.stack import Stack
    s = Stack.load('../stack_library/ditto_test_stack_ders_dataset3.json')
    s.run_dir = 'run_dir'
    s.run()

if __name__ == "__main__":
    main()
