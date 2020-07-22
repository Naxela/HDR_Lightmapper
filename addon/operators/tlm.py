import bpy, os, time, blf, webbrowser
from .. utility import build
from .. utility.cycles import cache

class TLM_BuildLightmaps(bpy.types.Operator):
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):

        #Add progress bar from 0.15

        print("MODAL")

        return {'PASS_THROUGH'}

    def invoke(self, context, event):

        if not bpy.app.background:

            print("Invoke")

            build.prepare_build(self, False)

        else:

            print("Running in background mode. Contextual operator not available. Use command 'thelightmapper.addon.build.prepare_build()'")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        pass

    def draw_callback_px(self, context, event):
        pass

class TLM_CleanLightmaps(bpy.types.Operator):
    bl_idname = "tlm.clean_lightmaps"
    bl_label = "Clean Lightmaps"
    bl_description = "Clean Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_EngineProperties.tlm_lightmap_savedir)
        if os.path.isdir(dirpath):
            for file in os.listdir(dirpath):
                os.remove(os.path.join(dirpath + "/" + file))

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    cache.backup_material_restore(obj)

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    cache.backup_material_rename(obj)

        for mat in bpy.data.materials:
            if mat.users < 1:
                bpy.data.materials.remove(mat)

        for mat in bpy.data.materials:
            if mat.name.startswith("."):
                if "_Original" in mat.name:
                    bpy.data.materials.remove(mat)

        for image in bpy.data.images:
            if image.name.endswith("_baked"):
                bpy.data.images.remove(image, do_unlink=True)

        return {'FINISHED'}

class TLM_ExploreLightmaps(bpy.types.Operator):
    bl_idname = "tlm.explore_lightmaps"
    bl_label = "Explore Lightmaps"
    bl_description = "Explore Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = scene.cycles

        if not bpy.data.is_saved:
            self.report({'INFO'}, "Please save your file first")
            return {"CANCELLED"}

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_EngineProperties.tlm_lightmap_savedir)

        if os.path.isdir(dirpath):
            webbrowser.open('file://' + dirpath)
        else:
            os.mkdir(dirpath)
            webbrowser.open('file://' + dirpath)

        return {'FINISHED'}