import bpy, math, os, platform, subprocess, sys, re, shutil, webbrowser, glob, bpy_extras, site
import cv2
import numpy as np
from time import time

def backup_material_copy(slot):
    material = slot.material
    dup = material.copy()
    dup.name = material.name + "_Original"
    dup.use_fake_user = True

def backup_material_restore(slot):
    material = slot.material
    if material.name + "_Original" in bpy.data.materials:
        original = bpy.data.materials[material.name + "_Original"]
        slot.material = original
        material.name = material.name + "_temp"
        original.name = original.name[:-9]
        original.use_fake_user = False
        material.user_clear()
        bpy.data.materials.remove(material)
    else:
        pass
        #Check if material has nodes with lightmap prefix

def load_pfm(file, as_flat_list=False):
    #start = time()

    header = file.readline().decode("utf-8").rstrip()
    if header == "PF":
        color = True
    elif header == "Pf":
        color = False
    else:
        raise Exception("Not a PFM file.")

    dim_match = re.match(r"^(\d+)\s(\d+)\s$", file.readline().decode("utf-8"))
    if dim_match:
        width, height = map(int, dim_match.groups())
    else:
        raise Exception("Malformed PFM header.")

    scale = float(file.readline().decode("utf-8").rstrip())
    if scale < 0:  # little-endian
        endian = "<"
        scale = -scale
    else:
        endian = ">"  # big-endian

    data = np.fromfile(file, endian + "f")
    shape = (height, width, 3) if color else (height, width)
    if as_flat_list:
        result = data
    else:
        result = np.reshape(data, shape)
    #print("PFM import took %.3f s" % (time() - start))
    return result, scale

def save_pfm(file, image, scale=1):
    #start = time()

    if image.dtype.name != "float32":
        raise Exception("Image dtype must be float32 (got %s)" % image.dtype.name)

    if len(image.shape) == 3 and image.shape[2] == 3:  # color image
        color = True
    elif len(image.shape) == 2 or len(image.shape) == 3 and image.shape[2] == 1:  # greyscale
        color = False
    else:
        raise Exception("Image must have H x W x 3, H x W x 1 or H x W dimensions.")

    file.write(b"PF\n" if color else b"Pf\n")
    file.write(b"%d %d\n" % (image.shape[1], image.shape[0]))

    endian = image.dtype.byteorder

    if endian == "<" or endian == "=" and sys.byteorder == "little":
        scale = -scale

    file.write(b"%f\n" % scale)

    image.tofile(file)

    #print("PFM export took %.3f s" % (time() - start))

def check_denoiser_path(self, scene):

    #TODO - Apply for Optix too...

    if scene.TLM_SceneProperties.tlm_denoise_use:
        if scene.TLM_SceneProperties.tlm_oidn_path == "":
            scriptDir = os.path.dirname(os.path.realpath(__file__))
            if os.path.isdir(os.path.join(scriptDir,"Addon/Assets/OIDN/bin")):
                scene.TLM_SceneProperties.tlm_oidn_path = os.path.join(scriptDir,"Addon/Assets/OIDN/bin")
                if scene.TLM_SceneProperties.tlm_oidn_path == "":
                    self.report({'INFO'}, "No denoise OIDN path assigned")
                    return{'FINISHED'}

def check_compatible_naming(self):
    for obj in bpy.data.objects:
        if "_" in obj.name:
            obj.name = obj.name.replace("_",".")
        if " " in obj.name:
            obj.name = obj.name.replace(" ",".")
        if "[" in obj.name:
            obj.name = obj.name.replace("[",".")
        if "]" in obj.name:
            obj.name = obj.name.replace("]",".")

        for slot in obj.material_slots:
            if "_" in slot.material.name:
                slot.material.name = slot.material.name.replace("_",".")
            if " " in slot.material.name:
                slot.material.name = slot.material.name.replace(" ",".")
            if "[" in slot.material.name:
                slot.material.name = slot.material.name.replace("[",".")
            if "[" in slot.material.name:
                slot.material.name = slot.material.name.replace("]",".")

def store_existing(cycles, scene):
    prevCyclesSettings = [
        cycles.samples,
        cycles.max_bounces,
        cycles.diffuse_bounces,
        cycles.glossy_bounces,
        cycles.transparent_max_bounces,
        cycles.transmission_bounces,
        cycles.volume_bounces,
        cycles.caustics_reflective,
        cycles.caustics_refractive,
        cycles.device,
        scene.render.engine
    ]
    return prevCyclesSettings

def set_settings(cycles, scene):
    sceneProperties = scene.TLM_SceneProperties
    cycles.device = sceneProperties.tlm_mode
    scene.render.engine = "CYCLES"
    
    if scene.TLM_SceneProperties.tlm_quality == "Preview":
        cycles.samples = 32
        cycles.max_bounces = 1
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 1
        cycles.transparent_max_bounces = 1
        cycles.transmission_bounces = 1
        cycles.volume_bounces = 1
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.TLM_SceneProperties.tlm_quality == "Medium":
        cycles.samples = 64
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.TLM_SceneProperties.tlm_quality == "High":
        cycles.samples = 256
        cycles.max_bounces = 128
        cycles.diffuse_bounces = 128
        cycles.glossy_bounces = 128
        cycles.transparent_max_bounces = 128
        cycles.transmission_bounces = 128
        cycles.volume_bounces = 128
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.TLM_SceneProperties.tlm_quality == "Production":
        cycles.samples = 512
        cycles.max_bounces = 256
        cycles.diffuse_bounces = 256
        cycles.glossy_bounces = 256
        cycles.transparent_max_bounces = 256
        cycles.transmission_bounces = 256
        cycles.volume_bounces = 256
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True
    else:
        pass

def restore_settings(cycles, scene, prevCyclesSettings):
    cycles.samples = prevCyclesSettings[0]
    cycles.max_bounces = prevCyclesSettings[1]
    cycles.diffuse_bounces = prevCyclesSettings[2]
    cycles.glossy_bounces = prevCyclesSettings[3]
    cycles.transparent_max_bounces = prevCyclesSettings[4]
    cycles.transmission_bounces = prevCyclesSettings[5]
    cycles.volume_bounces = prevCyclesSettings[6]
    cycles.caustics_reflective = prevCyclesSettings[7]
    cycles.caustics_refractive = prevCyclesSettings[8]
    cycles.device = prevCyclesSettings[9]
    scene.render.engine = prevCyclesSettings[10]

def configure_world():
    pass

def configure_lights():
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            if obj.TLM_ObjectProperties.tlm_light_lightmap_use:
                if obj.TLM_ObjectProperties.tlm_light_casts_shadows:
                    bpy.data.lights[obj.name].cycles.cast_shadow = True
                else:
                    bpy.data.lights[obj.name].cycles.cast_shadow = False

                bpy.data.lights[obj.name].energy = bpy.data.lights[obj.name].energy * obj.TLM_ObjectProperties.tlm_light_intensity_scale

def preprocess_material(obj, scene):
    if len(obj.material_slots) == 0:
        single = False
        number = 0
        while single == False:
            matname = obj.name + ".00" + str(number)
            if matname in bpy.data.materials:
                single = False
                number = number + 1
            else:
                mat = bpy.data.materials.new(name=matname)
                mat.use_nodes = True
                obj.data.materials.append(mat)
                single = True

    #Make the materials unique if multiple users (Prevent baking over existing)
    for slot in obj.material_slots:
        mat = slot.material
        if mat.users > 1:
                copymat = mat.copy()
                slot.material = copymat 

    #Make a material backup and restore original if exists
    if scene.TLM_SceneProperties.tlm_caching_mode == "Copy":
        for slot in obj.material_slots:
            matname = slot.material.name
            originalName = matname + "_Original"
            hasOriginal = False
            if originalName in bpy.data.materials:
                hasOriginal = True
            else:
                hasOriginal = False

            if hasOriginal:
                backup_material_restore(slot)

            backup_material_copy(slot)
    else: #Cache blend
        pass

    for mat in bpy.data.materials:
        if mat.name.endswith('_baked'):
            bpy.data.materials.remove(mat, do_unlink=True)
    for img in bpy.data.images:
        if img.name == obj.name + "_baked":
            bpy.data.images.remove(img, do_unlink=True)

    ob = obj
    for slot in ob.material_slots:
        #If temporary material already exists
        if slot.material.name.endswith('_temp'):
            continue
        n = slot.material.name + '_' + ob.name + '_temp'
        if not n in bpy.data.materials:
            slot.material = slot.material.copy()
        slot.material.name = n

    #Add images for baking
    img_name = obj.name + '_baked'
    res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(scene.TLM_SceneProperties.tlm_lightmap_scale)
    if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
        img = bpy.data.images.new(img_name, res, res, alpha=False, float_buffer=True)
        img.name = img_name
    else:
        img = bpy.data.images[img_name]

    for slot in obj.material_slots:
        mat = slot.material
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        if "Baked Image" in nodes:
            img_node = nodes["Baked Image"]
        else:
            img_node = nodes.new('ShaderNodeTexImage')
            img_node.name = 'Baked Image'
            img_node.location = (100, 100)
            img_node.image = img
        img_node.select = True
        nodes.active = img_node

def configure_objects(scene):

    iterNum = 0
    currentIterNum = 0

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                iterNum = iterNum + 1

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                currentIterNum = currentIterNum + 1

                #Configure selection
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active

                #Provide material if none exists
                preprocess_material(obj, scene)

                if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                uv_layers = obj.data.uv_layers
                if not "UVMap_Lightmap" in uv_layers:
                    uvmap = uv_layers.new(name="UVMap_Lightmap")
                    uv_layers.active_index = len(uv_layers) - 1
                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Lightmap":
                        bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin)
                    elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Smart Project":
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
                    else:
                        pass
                else:
                    for i in range(0, len(uv_layers)):
                        if uv_layers[i].name == 'UVMap_Lightmap':
                            uv_layers.active_index = i
                            break

                #Sort out nodes
                for slot in obj.material_slots:

                    nodetree = slot.material.node_tree

                    node = slot.material.name[:-5] + '_baked'
                    if not node in bpy.data.materials:
                        img_name = obj.name + '_baked'
                        mat = bpy.data.materials.new(name=node)
                        mat.use_nodes = True
                        nodes = mat.node_tree.nodes
                        img_node = nodes.new('ShaderNodeTexImage')
                        img_node.name = "Baked Image"
                        img_node.location = (100, 100)
                        img_node.image = bpy.data.images[img_name]
                        mat.node_tree.links.new(img_node.outputs[0], nodes['Principled BSDF'].inputs[0])
                    else:
                        mat = bpy.data.materials[node]
                        nodes = mat.node_tree.nodes
                        nodes['Baked Image'].image = bpy.data.images[img_name]

                for slot in obj.material_slots:

                    nodetree = bpy.data.materials[slot.name].node_tree
                    nodes = nodetree.nodes
                    mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                    for node in nodes:
                        if "LM" in node.name:
                            nodetree.links.new(n.outputs[0], mainNode.inputs[0])

                    for node in nodes:
                        if "Lightmap" in node.name:
                                nodes.remove(n)

                print("Configuring Object: " + bpy.context.view_layer.objects.active.name + " | " + str(currentIterNum) + " out of " + str(iterNum))

def bake_objects(scene):

    iterNum = 0
    currentIterNum = 0

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                iterNum = iterNum + 1

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active

                if scene.TLM_SceneProperties.tlm_indirect_only:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"INDIRECT"}, margin=scene.TLM_SceneProperties.tlm_dilation_margin)
                else:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.TLM_SceneProperties.tlm_dilation_margin)

                print("Baking Object: " + bpy.context.view_layer.objects.active.name + " | " + str(currentIterNum) + " out of " + str(iterNum))

def postmanage_materials(scene):
    for mat in bpy.data.materials:
        if mat.name.endswith('_baked'):
            has_user = False
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and mat.name.endswith('_' + obj.name + '_baked'):
                    has_user = True
                    break
            if not has_user:
                bpy.data.materials.remove(mat, do_unlink=True)

    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
    print("Checking for: " + dirpath)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)

    #Save
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                img_name = obj.name + '_baked'
                bakemap_path = os.path.join(dirpath, img_name)

                bpy.data.images[img_name].filepath_raw = bakemap_path + ".hdr"
                bpy.data.images[img_name].file_format = "HDR"
                bpy.data.images[img_name].save()

def denoise_lightmaps(scene):

    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                img_name = obj.name + '_baked'
                bakemap_path = os.path.join(dirpath, img_name)

                #Denoise here
                if scene.TLM_SceneProperties.tlm_denoise_use:
                    
                    if scene.TLM_SceneProperties.tlm_denoiser == "Optix":

                        image_output_destination = bakemap_path + ".hdr"
                        denoise_output_destination = bakemap_path + "_denoised.hdr"

                        if platform.system() == 'Windows':
                            optixPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_optix_path),"Denoiser.exe")
                            pipePath = [optixPath, '-i', image_output_destination, '-o', denoise_output_destination]
                        elif platform.system() == 'Darwin':
                            print("Mac for Optix is still unsupported")    
                        else:
                            print("Linux for Optix is still unsupported")

                        denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)

                        #if not verbose:
                        #    denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                        #else:
                        #    denoisePipe = subprocess.Popen(pipePath, shell=True)

                        denoisePipe.communicate()[0]

                    else:

                        image = bpy.data.images[img_name]
                        width = image.size[0]
                        height = image.size[1]

                        image_output_array = np.zeros([width, height, 3], dtype="float32")
                        image_output_array = np.array(image.pixels)
                        image_output_array = image_output_array.reshape(height, width, 4)
                        image_output_array = np.float32(image_output_array[:,:,:3])

                        image_output_destination = bakemap_path + ".pfm"

                        with open(image_output_destination, "wb") as fileWritePFM:
                            save_pfm(fileWritePFM, image_output_array)

                        denoise_output_destination = bakemap_path + "_denoised.pfm"

                        Scene = scene

                        verbose = Scene.TLM_SceneProperties.tlm_oidn_verbose
                        affinity = Scene.TLM_SceneProperties.tlm_oidn_affinity

                        if verbose:
                            v = "3"
                        else:
                            v = "0"

                        if affinity:
                            a = "1"
                        else:
                            a = "0"

                        threads = str(Scene.TLM_SceneProperties.tlm_oidn_threads)
                        maxmem = str(Scene.TLM_SceneProperties.tlm_oidn_maxmem)

                        if platform.system() == 'Windows':
                            oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe")
                            pipePath = [oidnPath, '-hdr', image_output_destination, '-o', denoise_output_destination, '-verbose', v, '-threads', threads, '-affinity', a, '-maxmem', maxmem]
                            print(pipePath)
                        elif platform.system() == 'Darwin':
                            oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                            pipePath = [oidnPath + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                        else:
                            oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                            pipePath = [oidnPath + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                            
                        if not verbose:
                            denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                        else:
                            denoisePipe = subprocess.Popen(pipePath, shell=True)

                        denoisePipe.communicate()[0]

                        with open(denoise_output_destination, "rb") as f:
                            denoise_data, scale = load_pfm(f)

                        ndata = np.array(denoise_data)
                        ndata2 = np.dstack( (ndata, np.ones((width,height)) )  )
                        img_array = ndata2.ravel()
                        bpy.data.images[image.name].pixels = img_array
                        bpy.data.images[image.name].filepath_raw = bakemap_path + "_denoised.hdr"
                        bpy.data.images[image.name].file_format = "HDR"
                        bpy.data.images[image.name].save()

def filter_lightmaps(scene):
    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                img_name = obj.name + '_baked'
                bakemap_path = os.path.join(dirpath, img_name)

                if scene.TLM_SceneProperties.tlm_filtering_use:
                    if scene.TLM_SceneProperties.tlm_denoise_use:
                        filter_file_input = img_name + "_denoised.hdr"
                    else:
                        filter_file_input = img_name + ".hdr"

                    #if all([module_pip, module_opencv]):
                    if all([True, True]):

                        filter_file_output = img_name + "_finalized.hdr"
                        os.chdir(os.path.dirname(bakemap_path))
                        opencv_process_image = cv2.imread(filter_file_input, -1)

                        if scene.TLM_SceneProperties.tlm_filtering_mode == "Box":
                            if scene.TLM_SceneProperties.tlm_filtering_box_strength % 2 == 0:
                                kernel_size = (scene.TLM_SceneProperties.tlm_filtering_box_strength + 1,scene.TLM_SceneProperties.tlm_filtering_box_strength + 1)
                            else:
                                kernel_size = (scene.TLM_SceneProperties.tlm_filtering_box_strength,scene.TLM_SceneProperties.tlm_filtering_box_strength)
                            opencv_bl_result = cv2.blur(opencv_process_image, kernel_size)
                            if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                    opencv_bl_result = cv2.blur(opencv_bl_result, kernel_size)

                        elif scene.TLM_SceneProperties.tlm_filtering_mode == "Gaussian":
                            if scene.TLM_SceneProperties.tlm_filtering_gaussian_strength % 2 == 0:
                                kernel_size = (scene.TLM_SceneProperties.tlm_filtering_gaussian_strength + 1,scene.TLM_SceneProperties.tlm_filtering_gaussian_strength + 1)
                            else:
                                kernel_size = (scene.TLM_SceneProperties.tlm_filtering_gaussian_strength,scene.TLM_SceneProperties.tlm_filtering_gaussian_strength)
                            sigma_size = 0
                            opencv_bl_result = cv2.GaussianBlur(opencv_process_image, kernel_size, sigma_size)
                            if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                    opencv_bl_result = cv2.GaussianBlur(opencv_bl_result, kernel_size, sigma_size)

                        elif scene.TLM_SceneProperties.tlm_filtering_mode == "Bilateral":
                            diameter_size = scene.TLM_SceneProperties.tlm_filtering_bilateral_diameter
                            sigma_color = scene.TLM_SceneProperties.tlm_filtering_bilateral_color_deviation
                            sigma_space = scene.TLM_SceneProperties.tlm_filtering_bilateral_coordinate_deviation
                            opencv_bl_result = cv2.bilateralFilter(opencv_process_image, diameter_size, sigma_color, sigma_space)
                            if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                    opencv_bl_result = cv2.bilateralFilter(opencv_bl_result, diameter_size, sigma_color, sigma_space)
                        else:

                            if scene.TLM_SceneProperties.tlm_filtering_median_kernel % 2 == 0:
                                kernel_size = (scene.TLM_SceneProperties.tlm_filtering_median_kernel + 1 , scene.TLM_SceneProperties.tlm_filtering_median_kernel + 1)
                            else:
                                kernel_size = (scene.TLM_SceneProperties.tlm_filtering_median_kernel, scene.TLM_SceneProperties.tlm_filtering_median_kernel)

                            opencv_bl_result = cv2.medianBlur(opencv_process_image, kernel_size[0])
                            if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                    opencv_bl_result = cv2.medianBlur(opencv_bl_result, kernel_size[0])

                        cv2.imwrite(filter_file_output, opencv_bl_result)
                        
                        bpy.ops.image.open(filepath=os.path.join(os.path.dirname(bakemap_path),filter_file_output))
                        bpy.data.images[obj.name+"_baked"].name = obj.name + "_temp"
                        bpy.data.images[obj.name+"_baked_finalized.hdr"].name = obj.name + "_baked"
                        bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])

                    else:
                       print("Modules missing...")

def bake_ordered(self, context):
    scene = context.scene
    cycles = scene.cycles

    #//////////// PRECONFIGURATION

    if not bpy.data.is_saved:
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    check_denoiser_path(self, scene)
    check_compatible_naming(self)

    prevSettings = store_existing(cycles, scene)
    set_settings(cycles, scene)

    #configure_World()
    configure_lights()

    print("////////////////////////////// CONFIGURING OBJECTS")
    configure_objects(scene)

    #Baking
    print("////////////////////////////// BAKING LIGHTMAPS")
    bake_objects(scene)

    #Post configuration
    print("////////////////////////////// MANAGING LIGHTMAPS")
    postmanage_materials(scene)

    #Denoise lightmaps
    print("////////////////////////////// DENOISE LIGHTMAPS")
    denoise_lightmaps(scene)

    #Filter lightmaps
    print("////////////////////////////// FILTER LIGHTMAPS")
    filter_lightmaps(scene)

    total_time = time()




    #//////////// POSTCONFIGURATION

    restore_settings(cycles, scene, prevSettings)

    print("////////////////////////////// LIGHTMAPS BUILT")

    print("Baking finished in: %.3f s" % (time() - total_time))