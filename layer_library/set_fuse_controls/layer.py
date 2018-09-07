from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
from ditto.models.line import Line

logger = logging.getLogger('layerstack.layers.Set_Fuse_Controls')


class Set_Fuse_Controls(DiTToLayerBase):
    name = "set_fuse_controls"
    uuid = UUID("d208979a-df15-44ea-859f-223c09168f84")
    version = '0.1.0'
    desc = "Layer to set fuse limits"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['current_rating'] = Kwarg(default=None, description='Rated current of the fuse',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['fuse_set'] = Kwarg(default=None, description='Set of the fuse names to apply the controls to. If None provided, controls applied to all fuses',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        current_rating = None
        fuse_set = None
        if 'current_rating' in kwargs:
            current_rating = kwargs['current_rating']
        if fuse_set in kwargs:
            fuse_set = kwargs['fuse_set']
        if current_rating is not None:
            for i in model.models:
                if isinstance(i,Line) and hasattr (i,'is_fuse') and i.is_fuse and hasattr(i,'wires') and i.wires is not None:
                    if fuse_set is not None:
                        if i in fuse_set:
                            for w in i.wires:
                                w.is_fuse = True
                                w.interrupting_rating = float(current_rating)
                    else:
                        for w in i.wires:
                            w.is_fuse = True
                            w.interrupting_rating = float(current_rating)


        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Set_Fuse_Controls.main()

    
