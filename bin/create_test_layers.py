from layerstack.layer import Layer, LayerBase
from ditto.dittolayers import DiTToLayerBase
import os

Layer.create('from_json',os.path.join('..','layer_library'),desc='Read a json DiTTo model into DiTTo',layer_base_class=LayerBase)

