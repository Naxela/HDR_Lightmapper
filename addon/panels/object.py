import bpy
from bpy.props import *
from bpy.types import Menu, Panel
from ... addon.properties import object
from .. import icon

class TLM_PT_ObjectMenu(bpy.types.Panel):
    bl_label = "The Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = bpy.context.object
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene

        if obj.type == "MESH":
            row = layout.row(align=True)
            row.prop(obj, "tlm_mesh_lightmap_use")
            if obj.tlm_mesh_lightmap_use:
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_apply_after")
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_emissive")
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_emissive_shadow")
                row = layout.row()
                row.prop(obj, "tlm_mesh_lightmap_resolution")
                row = layout.row()
                row.prop(obj, "tlm_mesh_lightmap_unwrap_mode")
                row = layout.row()
                row.prop(obj, "tlm_mesh_unwrap_margin")
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_bake_ao")