import bpy
from bpy.app.handlers import persistent


@persistent
def update_eevee_normals(scene):
    settings = scene.MustardSimplify_Settings

    if settings.simplify_fastnormals_status:
        bpy.ops.mustard_simplify.fast_normals(
            custom=not settings.simplify_fastnormals_status
        )


def register():
    bpy.app.handlers.render_pre.append(update_eevee_normals)


def unregister():
    bpy.app.handlers.render_pre.remove(update_eevee_normals)
