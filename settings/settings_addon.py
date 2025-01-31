import bpy
from bpy.props import *
from .. import __package__ as base_package


# Addon preferences can be accessed with
# from .. import __package__ as base_package
# ...
# addon_prefs = bpy.context.preferences.addons[base_package].preferences
class MustardSimplify_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = base_package

    # Wiki links
    wiki: BoolProperty(name="Show Wiki/Help Buttons",
                       description="Show the Help buttons near the tools",
                       default=True)

    viewport_button: BoolProperty(default=True,
                                  name="Simplify Viewport Button",
                                  description="Add buttons in Viewport to enable/disable Simplify, and Eevee Fast "
                                              "Normals")

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
        col.prop(self, "wiki")
        col.prop(self, "viewport_button")

        col.separator()
        col.prop(self, "advanced")
        col.prop(self, "debug")

        col = layout.column(align=True)
        col.operator("mustard_simplify.reset_settings", icon="GHOST_DISABLED")

        col = layout.column(align=True)
        col.operator("mustard_simplify.openlink", text="Report Issue",
                        icon="URL").url = "https://github.com/Mustard2/MustardSimplify/issues"


def register():
    bpy.utils.register_class(MustardSimplify_AddonPrefs)


def unregister():
    bpy.utils.unregister_class(MustardSimplify_AddonPrefs)
