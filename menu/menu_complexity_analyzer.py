import bpy

from .. import __package__ as base_package
from ..tools.ops_complexity_analyzer import is_workbench
from . import MainPanel


class MUSTARDSIMPLIFY_PT_ComplexityAnalyzer(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_ComplexityAnalyzer"
    bl_label = "Scene Complexity Analyzer"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        if addon_prefs.wiki:
            layout.operator(
                "mustard_simplify.openlink", text="", icon="QUESTION"
            ).url = (
                "https://github.com/Mustard2/MustardSimplify/wiki#complexity-analyzer"
            )

    def draw(self, context):
        layout = self.layout
        settings = context.scene.MustardSimplify_Settings
        wb = is_workbench(context)

        if not wb:
            box = layout.box()
            col = box.column(align=True)
            col.label(
                text="Switch to Workbench view to use Complexity Analyzer.",
                icon="INFO",
            )
            col.separator()
            col.operator(
                "mustard_simplify.complexity_analyzer_switch_workbench",
                text="Switch to Workbench",
                icon="SHADING_SOLID",
            )

        col = layout.column()
        col.enabled = wb

        col.row(align=True).prop(settings, "complexity_analyzer_mode", expand=True)

        col.separator()

        row = col.row(align=True)
        if settings.complexity_analyzer_active:
            row.operator(
                "mustard_simplify.complexity_analyzer_toggle",
                text="Disable",
                icon="CANCEL",
            )
        else:
            row.operator(
                "mustard_simplify.complexity_analyzer_toggle",
                text="Enable",
                icon="PLAY",
            )
        row.prop(settings, "complexity_analyzer_live_update", text="", icon="ANIM")


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_ComplexityAnalyzer)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_ComplexityAnalyzer)
