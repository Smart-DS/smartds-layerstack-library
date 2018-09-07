from layerstack.layer import Layer, LayerBase
from ditto.dittolayers import DiTToLayerBase
import os

Layer.create('add_rnm_regulators',os.path.join('..','layer_library'),desc='Add regulator controls using the RNM naming scheme',layer_base_class=DiTToLayerBase)

