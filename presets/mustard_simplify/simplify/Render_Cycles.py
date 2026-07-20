import bpy

settings = bpy.context.scene.MustardSimplify_Settings
rd = bpy.context.scene.render
cscene = bpy.context.scene.cycles if hasattr(bpy.context.scene, "cycles") else None

settings.blender_simplify = True
settings.objects = False
settings.culling = True
settings.modifiers = False
settings.shape_keys = False
settings.shape_keys_disable_not_null = True
settings.shape_keys_disable_with_drivers = True
settings.shape_keys_disable_with_drivers_not_null = False
settings.shape_keys_disable_with_keyframes = False
settings.drivers = False
settings.physics = False

rd.simplify_subdivision = 6
rd.simplify_child_particles = 1.0
rd.simplify_volumes = 1.0
rd.use_simplify_normals = False
rd.simplify_subdivision_render = 6
rd.simplify_child_particles_render = 1.0

if cscene is not None:
    cscene.texture_limit = "OFF"
    cscene.texture_limit_render = "OFF"
    cscene.use_camera_cull = True
    cscene.camera_cull_margin = 0.1
    cscene.use_distance_cull = True
    cscene.distance_cull_margin = 50.0
    if hasattr(cscene, "texture_resolution"):
        cscene.texture_resolution = 100.0
        cscene.texture_resolution_render = 100.0
