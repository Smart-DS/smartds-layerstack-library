# Smart-DS Layerstack Library

[![Documentation](https://img.shields.io/badge/docs-ready-blue.svg)](http://smart-ds.github.io/smartds-layerstack-library)

Repository for layers and stacks related to the Smart-DS project.

## Create a new DiTTo model layer

```ipython
from layerstack.layer import Layer
from ditto.dittolayers import DittoLayerBase

parent_dir = 'smartds-layerstack-library/layer_library/'
Layer.create('Human Readable Name for New Layer',parent_dir,
    desc="Add brief description here if desired. Can always be added later.",
    layer_base_class=DittoLayerBase)
```

## Create a new (non-DiTTo) model reading layer

```ipython
from layerstack.layer import Layer, LayerBase

parent_dir = 'smartds-layerstack-library/layer_library/'
# existing example
Layer.create('From OpenDSS',parent_dir,
    desc="Layer to load DiTTo model from Open DSS",layer_base_class=LayerBase)
# in the apply method, load the model then set stack.model equal to the result
# (see [from_opendss/layer.py](layer_library/from_opendss/layer.py#L46))
```

## Create a new (non-DiTTo) model writing layer

```ipython
from layerstack.layer import Layer, LayerBase

parent_dir = 'smartds-layerstack-library/layer_library/'
# existing example
Layer.create('To OpenDSS',parent_dir,
    desc="Layer to write DiTTo model to Open DSS",layer_base_class=LayerBase)
# In the apply method, ditto_model = stack.model, then write ditto_model out
# to the desired format. Functionally these layers could be written as 
# DiTToLayerBase classes, but then there would be a risk of the Stack trying to 
# write the DiTTo model out to disc, which currently throws an exception.
```

## Create a new stack

```bash
git clone https://github.com/Smart-DS/dataset3.git
cd 'smartds-layerstack-library/bin'
ipython
```

```ipython
import create_test_stacks
create_test_stacks.create_test_stack('../../dataset3')
```

## Run a stack

```bash
git clone https://github.com/Smart-DS/dataset3.git
cd 'smartds-layerstack-library/bin'
ipython
```

```
from create_test_stacks import update_stack_base_dir
update_stack_base_dir('../stack_library/ditto_test_stack_dataset3.json','../../dataset3')
from layerstack.stack import Stack
s = Stack.load('../stack_library/ditto_test_stack_dataset3.json')
s.run_dir = 'run_dir'
s.run()
```
