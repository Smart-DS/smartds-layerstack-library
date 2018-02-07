import os

from layerstack.layer import Layer
from layerstack.stack import Stack

repo_dir = os.path.dirname(os.path.dirname(__file__))
layer_library_dir = os.path.join(repo_dir,'layer_library')
stack_library_dir = os.path.join(repo_dir,'stack_library')

def create_test_stack():
    stack = Stack(name='DiTTo Test Stack')
    stack.append(Layer(os.path.join(layer_library_dir,'from_opendss')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_substations')))
    stack.append(Layer(os.path.join(layer_library_dir,'add_timeseries_load')))
    stack.append(Layer(os.path.join(layer_library_dir,'scale_loads')))
    stack.append(Layer(os.path.join(layer_library_dir,'to_opendss')))

    # base_model = from_opendss.apply(stack,base_model,'data/dataset3/mixed_humid/industrial/OpenDSS/master.dss','data/dataset3/mixed_humid/industrial/OpenDSS/buscoords.dss')
    # substation_model = add_substations.apply(stack,base_model,'data/dataset3/mixed_humid/industrial/feeders/feeders.txt','data/substations','data/dataset3/post_process/modified_substations')
    # timeseries_model = add_timeseries_load.apply(stack,substation_model,'data/dataset3/mixed_humid/industrial/consumers&street_map/customers_extended.csv')
    # scaled_model = scale_loads.apply(stack, timeseries_model, scale_factor = 1.1)
    # final_model = write_model.apply(stack, scaled_model,'data/dataset3/post_process/mixed_humid/industrial/') 

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

