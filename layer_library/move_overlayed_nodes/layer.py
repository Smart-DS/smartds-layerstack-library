from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import random
import networkx as nx
#from networkx.drawing.nx_agraph import graphviz_layout
from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase
import networkx

logger = logging.getLogger('layerstack.layers.Move_Overlayed_Nodes')


class Move_Overlayed_Nodes(DiTToLayerBase):
    name = "move_overlayed_nodes"
    uuid = UUID("31f61c51-a89a-419c-80ba-23d4b89730eb")
    version = '0.1.0'
    desc = "Jiggle the coordinate positions of nodes that are on top of each other"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['delta_x'] = Kwarg(default=None, description='Shift in the coordinates X position',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['delta_y'] = Kwarg(default=None, description='Shift in the coordinates Y position',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        random.seed(0)
        delta_x = 1 # Use 1 as a default
        delta_y = 0 # Use 0 as a default
        if 'delta_x' in kwargs:
            delta_x = kwargs['delta_x']
        if 'delta_y' in kwargs:
            delta_y = kwargs['delta_y']
        all_positions = {}
        all_positions_intermediate = {}
        for m in model.models:
            if hasattr(m,'name') and m.name is not None and hasattr(m,'positions') and m.positions is not None:
                if len(m.positions)==1: # Only look at elements with only one position attribute
                    pos = (float(round(m.positions[0].lat)),float(round(m.positions[0].long)))
                    if pos in all_positions:
                        all_positions[pos].append(m.name)
                    else:
                        all_positions[pos] = [m.name]
                if len(m.positions)>2: #Intermediate nodes
                    for i in range(1,len(m.positions)):
                        pos = (float(round(m.positions[i].lat)),float(round(m.positions[i].long))) #x2,y2
                        pos_prev = (float(round(m.positions[i-1].lat)),float(round(m.positions[i-1].long))) #x1,y1
                        norm = ((pos[0]-pos_prev[0])**2 + (pos[1]-pos_prev[1])**2)**0.5
                        if norm !=0:
                            perp = ((pos[1]-pos_prev[1])/norm,(pos_prev[0]-pos[0])/norm) # perpendicular unit vector so that the change ensures the lines are in parallel
                        else:
                            perp = (1,0)
                        if pos in all_positions_intermediate:
                            all_positions_intermediate[pos].append((m.positions[i],perp)) #Add model not name as position objects exist without names
                        else:
                            all_positions_intermediate[pos] = [(m.positions[i],perp)]
        model.build_networkx('st_mat')
        spring = nx.spring_layout(model._network.graph)
        for pos in all_positions:
            if len(all_positions[pos]) >1:
                #model._network.build(model,source='st_mat')
                #model._network.set_attributes(model)
                #path = model.get_extremal_path(all_positions[pos])
                #import pdb;pdb;pdb.set_trace()
                path = all_positions[pos]
                for i in range(len(path)):
                    ###range1 = random.choice([(-2*delta_x,-0.5*delta_x),(0.5*delta_x,2*delta_x)]) 
                    ###range2 = random.choice([(-2*delta_y,-0.5*delta_y),(0.5*delta_y,2*delta_y)]) 
                    ###model[path[i]].positions[0].lat += random.uniform(range1[0],range1[1])
                    ###model[path[i]].positions[0].long += random.uniform(range2[0],range1[1])
                    factor = 1
                    if len(path)>6:
                        factor = 1.5
                    model[path[i]].positions[0].lat += spring[path[i]][0]*delta_x *factor
                    model[path[i]].positions[0].long += spring[path[i]][1]*delta_y *factor

        for pos in all_positions_intermediate:
            if len(all_positions_intermediate[pos])>1:
                path = all_positions_intermediate[pos]
               # import pdb;pdb.set_trace()
                for i in range(len(path)):
                    m = path[i][0]
                    perp = path[i][1]
                    m.lat +=perp[0]*i
                    m.long +=perp[1]*i


        model._network.graph = None #So these layouts don't remain permanant
        return model
                



        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    Move_Overlayed_Nodes.main()

    
