import bpy
from bpy.props import *


# Addon preferences can be accessed with
# addon_prefs = context.preferences.addons[__name__].preferences
class MustardSimplify_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = "MustardSimplify"

    # Maintenance tools
    advanced: BoolProperty(name="Advanced Options",
                           description="Unlock advanced options",
                           default=False)

    # Debug mode
    debug: BoolProperty(default=False,
                        name="Debug Mode",
                        description="Unlock Debug Mode.\nMore messaged will be generated in the "
                                    "console.\nEnable it only if you encounter problems, as it might "
                                    "degrade general Blender performance")

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.prop(self, "advanced")
        col.prop(self, "debug")

        col = layout.column(align=True)
        col.operator("mustard_simplify.openlink", text="Check Version",
                        icon="URL").url = "https://github.com/Mustard2/MustardSimplify/releases"
        col.operator("mustard_simplify.openlink", text="Report Issue",
                        icon="URL").url = "https://github.com/Mustard2/MustardSimplify/issues"


def register():
    bpy.utils.register_class(MustardSimplify_AddonPrefs)


def unregister():
    bpy.utils.unregister_class(MustardSimplify_AddonPrefs)
