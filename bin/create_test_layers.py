from layerstack.layer import Layer, LayerBase
from ditto.dittolayers import DiTToLayerBase
import os

Layer.create('set_fuse_controls',os.path.join('..','layer_library'),desc='Layer to set fuse limits',layer_base_class=DiTToLayerBase)

