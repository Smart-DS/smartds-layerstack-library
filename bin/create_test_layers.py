from layerstack.layer import Layer, LayerBase
from ditto.dittolayers import DiTToLayerBase
import os

Layer.create('create_nested_placement',os.path.join('..','layer_library'),desc='Create placements that fit inside each other',layer_base_class=DiTToLayerBase)

