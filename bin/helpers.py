import os

from layerstack.args import ArgMode
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

def output_model_to_run_dir(stack):
    last_layer = stack[-1]
    if last_layer.name == "To OpenDSS":
        assert 'base_dir' in layer.kwargs
        layer.kwargs['base_dir'] = stack.run_dir
    return stack