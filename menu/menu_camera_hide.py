import bpy

from . import MainPanel
from .. import __package__ as base_package


class MUSTARDSIMPLIFY_PT_CameraHide(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_CameraHide"
    bl_label = "Camera Hide (Experimental)"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        return addon_prefs.experimental

    def draw(self, context):
        scene = context.scene
        settings = scene.MustardSimplify_Settings

        layout = self.layout

        row = layout.row(align=True)
        row.enabled = not settings.live_frustum_running
        row.operator("mustard_simplify.apply_frustum_culling", icon='HIDE_OFF')
        row.operator("mustard_simplify.restore_frustum_culling", icon='X', text="")

        layout.separator()

        if settings.live_frustum_running:
            icon = 'PAUSE'
            text = "Stop Camera Hide"
        else:
            icon = 'PLAY'
            text = "Start Camera Hide"
        layout.operator("mustard_simplify.toggle_live_frustum_culling", icon=icon, text=text,
                        depress=settings.live_frustum_running)
        layout.prop(settings, "live_frustum_interval", slider=True)


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_CameraHide)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_CameraHide)
