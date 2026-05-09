import bpy

from .. import __package__ as base_package
from . import MainPanel


class MUSTARDSIMPLIFY_PT_Tools(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_Tools"
    bl_label = "Tools"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        if addon_prefs.wiki:
            layout.operator(
                "mustard_simplify.openlink", text="", icon="QUESTION"
            ).url = "https://github.com/Mustard2/MustardSimplify/wiki#tools"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "mustard_simplify.add_proxy",
            text="Create Armature Proxy",
            icon="ARMATURE_DATA",
        )
        layout.operator(
            "mustard_simplify.data_removal", text="Data Removal", icon="BRUSH_DATA"
        )


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Tools)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Tools)
