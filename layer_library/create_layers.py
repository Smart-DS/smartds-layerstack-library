import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from layerstack.layer import Layer


cwd = os.getcwd()

parent_dir = cwd

# name = 'Stack_test'
# desc = 'Test Layer for Stack developement'
# Layer.create(name, parent_dir, desc=desc)

# # Load OpenDSS
# name = 'From_OpenDSS'
# desc = 'Layer to load DiTTo model from Open DSS'
# Layer.create(name, parent_dir, desc=desc)
#
# # Add Layer
# name = 'Add_Load'
# desc = 'Layer to add load to base DiTTo model'
# Layer.create(name, parent_dir, desc=desc)
#
# Clean up substations
# name = 'Add_Substations'
# desc = 'Layer to Add substations to the dataset3 model'
# Layer.create(name, parent_dir, desc=desc)
#
# # Write Model
# name = 'Write_Model'
# desc = 'Layer to write model out of DiTTo'
# Layer.create(name, parent_dir, desc=desc)


#name = 'Test_Layer'
#desc = 'Test Layer Demo'
#Layer.create(name, parent_dir, desc=desc)

# Add Timeseries Layers
#name = 'Add_Timeseries_Load'
#desc = 'Layer to add timeseries load objects to base DiTTo model'
#Layer.create(name, parent_dir, desc=desc)

# Scale the Loads
#name = 'Scale_Loads'
#desc = 'Layer to scale timeseries load objects for different years'
#Layer.create(name, parent_dir, desc=desc)

# Find Peak in Timeseries
#name = 'Peak_Loads'
#desc = 'Layer to find the peak value in the timeseries load objects'
#Layer.create(name, parent_dir, desc=desc)
