"""Exact active-bonded-pad clipping for ephemeral protected branch obstacles."""
from native7_RX_IO4_model_v2 import build as build_base
from native7_RX_IO4_model_v2 import adapter,HERE,ROOT

def build():
    g,base,C,view0,work,before,inventory,jobs=build_base()
    bonded={'PORT_C_RX_EXT':'U15.5','PORT_C_TX_EXT':'U15.2'}
    pad_geometry={net:g.entry(g.one_pad(key))[1] for net,key in bonded.items()}
    def view(net,role,objects,*,additional_roles=None):
        alias,rows=view0(net,role,objects,additional_roles=additional_roles)
        result=[]
        for original,row in zip(objects,rows):
            source=original[0];o,cu,mask,drill=row
            if source['net']==net and source['kind']=='track' and o['net']!=alias:
                # Other-role copper within the actual bonded pad is the intended
                # common terminal. All outside-pad copper, masks and drills remain.
                cu={layer:(shape.difference(pad_geometry[net][layer]) if layer in pad_geometry[net] else shape) for layer,shape in cu.items()}
            result.append((o,cu,mask,drill))
        return alias,result
    inventory['branch_view_geometry_rule']={'bonded_keys':bonded,'foreign_other_role_track_copper_clipped_only_inside_actual_active_bonded_pad':True,'outside_pad_copper_and_all_mask_drill_geometry_unchanged':True,'physical_objects_never_mutated_by_view':True}
    return g,base,C,view,work,before,inventory,jobs
