import bpy


def draw_item(self, context):
    layout = self.layout
    scene = context.scene
    settings = scene.MustardSimplify_Settings

    layout.separator()

    row = layout.row(align=True)
    op = row.operator("mustard_simplify.scene", text="Simplify", icon="MOD_SIMPLIFY",
                      depress=settings.simplify_status)
    op.enable_simplify = not settings.simplify_status

    op2 = row.operator('mustard_simplify.fast_normals', text="",
                       icon="ERROR" if settings.simplify_fastnormals_status and scene.render.engine == "CYCLES" else
                       "MOD_NORMALEDIT",
                       depress=settings.simplify_fastnormals_status)
    op2.custom = not settings.simplify_fastnormals_status


def register():
    bpy.types.VIEW3D_MT_editor_menus.append(draw_item)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_item)
