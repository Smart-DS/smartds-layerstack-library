from layerstack.layer import Layer, LayerBase
from ditto.dittolayers import DiTToLayerBase
import os

Layer.create('set_lv_as_triplex',os.path.join('..','layer_library'),desc='Replace low voltage overhead lines that are copper with triplex wires',layer_base_class=DiTToLayerBase)

