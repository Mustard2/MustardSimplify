import bpy

from . import MainPanel


class MUSTARDSIMPLIFY_PT_Settings(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_Settings"
    bl_label = "Settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = bpy.context.scene.MustardSimplify_Settings

        box = layout.box()
        box.label(text="Main Settings", icon="SETTINGS")
        col = box.column(align=True)
        col.prop(settings, "advanced")
        col.prop(settings, "debug")

        layout.operator("mustard_simplify.openlink", text="Check New Version",
                        icon="URL").url = "https://github.com/Mustard2/MustardSimplify/releases"
        layout.operator("mustard_simplify.openlink", text="Report Issue",
                        icon="URL").url = "https://github.com/Mustard2/MustardSimplify/issues"


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Settings)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Settings)
