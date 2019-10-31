import bpy
from bpy.props import *
from bpy.types import Menu, Panel
from .. Utility import icon

class TLM_PT_Panel(bpy.types.Panel):
    bl_label = "The Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        row = layout.row(align=True)
        row.operator("tlm.build_lightmaps", icon="NONE", icon_value=icon.id("bake"))
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_bake_for_selection")
        row = layout.row(align=True)
        row.operator("tlm.clean_lightmaps", icon="NONE", icon_value=icon.id("clean"))
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_clean_option")
        row = layout.row(align=True)
        row.operator("tlm.explore_lightmaps", icon="NONE", icon_value=icon.id("explore"))

class TLM_PT_Settings(bpy.types.Panel):
    bl_label = "Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_mode")
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_quality')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_bake_mode')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_caching_mode')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_baketime_material')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_directional_mode')

        if not sceneProperties.tlm_directional_mode == "None":
            row = layout.row(align=True)
            row.prop(sceneProperties, 'tlm_bake_normal_denoising')

        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_lightmap_scale', expand=True)
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_lightmap_savedir')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_dilation_margin')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_exposure_multiplier')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_apply_on_unwrap')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_indirect_only')
        row = layout.row(align=True)
        if sceneProperties.tlm_indirect_only:
            row.prop(sceneProperties, 'tlm_indirect_mode')
            row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_keep_cache_files')

class TLM_PT_Denoise(bpy.types.Panel):
    bl_label = "Denoise"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        sceneProperties = scene.TLM_SceneProperties
        self.layout.prop(sceneProperties, "tlm_denoise_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        layout.active = sceneProperties.tlm_denoise_use
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_oidn_path")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_oidn_verbose")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_oidn_threads")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_oidn_maxmem")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_oidn_affinity")

class TLM_PT_Filtering(bpy.types.Panel):
    bl_label = "Filtering"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        sceneProperties = scene.TLM_SceneProperties
        self.layout.prop(sceneProperties, "tlm_filtering_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties

        column = layout.column()
        box = column.box()
        # if module.checkModules():
        #     box.label(text="OpenCV Installed", icon="INFO")
        # else:
        #     box.label(text="Please restart Blender after installing")
        #     box.operator("tlm.install_opencv",icon="PREFERENCES")

        # if(scene.tlm_filtering_use):
        #     if(module.checkModules()):
        #         layout.active = True
        #     else:
        #         layout.active = False
        # else:
        #     layout.active = False

        layout.active = True

        row = layout.row(align=True)
        row.prop(scene.TLM_SceneProperties, "tlm_filtering_mode")
        row = layout.row(align=True)
        if scene.TLM_SceneProperties.tlm_filtering_mode == "Gaussian":
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_gaussian_strength")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")
        elif scene.TLM_SceneProperties.tlm_filtering_mode == "Box":
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_box_strength")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")

        elif scene.TLM_SceneProperties.tlm_filtering_mode == "Bilateral":
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_bilateral_diameter")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_bilateral_color_deviation")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_bilateral_coordinate_deviation")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")
        else:
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_median_kernel", expand=True)
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")

class TLM_PT_Encoding(bpy.types.Panel):
    bl_label = "Encoding"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_encoding_mode", expand=True)
        if sceneProperties.tlm_encoding_mode == "RGBM" or sceneProperties.tlm_encoding_mode == "RGBD":
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_encoding_range")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_encoding_armory_setup")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_encoding_colorspace")

class TLM_PT_Compression(bpy.types.Panel):
    bl_label = "Compression"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        if sceneProperties.tlm_encoding_mode == "RGBE":
            layout.label(text="HDR compression not available for RGBE encoding")
        else:
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_compression")

class TLM_PT_Selection(bpy.types.Panel):
    bl_label = "Selection"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.label(text="Enable for selection")
        layout.label(text="Disable for selection")
        layout.label(text="Something...")

class TLM_PT_Additional(bpy.types.Panel):
    bl_label = "Additional"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        # layout.use_property_split = True
        # layout.use_property_decorate = False
        # layout.label(text="Enable for selection")
        # layout.label(text="Disable for selection")
        # layout.label(text="Something...")