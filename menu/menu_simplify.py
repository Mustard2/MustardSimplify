import bpy

from . import MainPanel
from .. import __package__ as base_package


class MUSTARDSIMPLIFY_PT_Simplify(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_Simplify"
    bl_label = "Simplify"

    def draw(self, context):

        scene = context.scene
        layout = self.layout
        settings = scene.MustardSimplify_Settings

        if settings.simplify_status:
            op = layout.operator("mustard_simplify.scene", text="Un-Simplify Scene",
                                 icon="MOD_SIMPLIFY", depress=True)
        else:
            op = layout.operator("mustard_simplify.scene", text="Simplify Scene", icon="MOD_SIMPLIFY")
        op.enable_simplify = not settings.simplify_status

        row = layout.row(align=True)
        if settings.simplify_fastnormals_status and scene.render.engine == "CYCLES":
            op2 = row.operator('mustard_simplify.fast_normals',
                               text="Enable Eevee Fast Normals" if not settings.simplify_fastnormals_status else "Disable Eevee Fast Normals",
                               icon="ERROR", depress=settings.simplify_fastnormals_status)
        else:
            row.enabled = not scene.render.engine == "CYCLES"
            op2 = row.operator('mustard_simplify.fast_normals',
                               text="Enable Eevee Fast Normals" if not settings.simplify_fastnormals_status else "Disable Eevee Fast Normals",
                               icon="MOD_NORMALEDIT", depress=settings.simplify_fastnormals_status)
        op2.custom = not settings.simplify_fastnormals_status


class MUSTARDSIMPLIFY_PT_Simplify_Options(MainPanel, bpy.types.Panel):
    bl_label = "Options"
    bl_parent_id = "MUSTARDSIMPLIFY_PT_Simplify"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        if addon_prefs.wiki:
            layout.operator("mustard_simplify.openlink", text="",
                         icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#simplify"

    def draw(self, context):

        scene = context.scene
        layout = self.layout
        settings = scene.MustardSimplify_Settings

        row = layout.row()
        col = row.column()
        row.enabled = not settings.simplify_status
        col.prop(settings, "blender_simplify")
        row.operator("mustard_simplify.menu_blender_simplify_settings", icon="PREFERENCES", text="")

        col = layout.column(align=True)
        col.enabled = not settings.simplify_status
        row = col.row()
        row.prop(settings, "objects")
        row.operator("mustard_simplify.menu_objects_select", icon="PREFERENCES", text="")

        row = col.row()
        row.prop(settings, "modifiers")
        row.operator("mustard_simplify.menu_modifiers_select", icon="PREFERENCES", text="")

        row = col.row()
        row.prop(settings, "shape_keys")
        row.operator("mustard_simplify.menu_shape_keys_settings", icon="PREFERENCES", text="")

        col.prop(settings, "drivers")

        col.prop(settings, "physics")

        col.prop(settings, "normals_auto_smooth")


class MUSTARDSIMPLIFY_PT_Simplify_Exceptions(MainPanel, bpy.types.Panel):
    bl_label = "Exceptions"
    bl_parent_id = "MUSTARDSIMPLIFY_PT_Simplify"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        if addon_prefs.wiki:
            layout.operator("mustard_simplify.openlink", text="",
                            icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#exceptions"

    def draw(self, context):

        scene = context.scene
        layout = self.layout
        settings = scene.MustardSimplify_Settings

        row = layout.row()
        row.prop(settings, 'exception_type', expand=True)
        row.enabled = not settings.simplify_status

        if settings.exception_type == "OBJECT":

            row = layout.row()
            row.enabled = not settings.simplify_status
            row.template_list("MUSTARDSIMPLIFY_UL_Exceptions_UIList", "The_List", scene.MustardSimplify_Exceptions,
                              "exceptions", scene, "mustardsimplify_exception_uilist_index")
            col = row.column(align=True)
            col.operator("mustard_simplify.remove_exception", icon="REMOVE", text="")

            row = layout.row()
            row.enabled = not settings.simplify_status
            row.prop_search(settings, "exception_select", scene, "objects", text="")
            row.operator("mustard_simplify.add_exception", text="", icon="ADD")

            if scene.mustardsimplify_exception_uilist_index > -1 and len(
                    scene.MustardSimplify_Exceptions.exceptions) > 0:
                obj = scene.MustardSimplify_Exceptions.exceptions[scene.mustardsimplify_exception_uilist_index]

                if obj is not None:
                    box = layout.box()
                    item_in_exception_collection = False
                    if settings.exception_collection is not None:
                        item_in_exception_collection = obj.exception in [x for x in (
                            settings.exception_collection.all_objects if settings.exception_include_subcollections else settings.exception_collection.objects)]
                    box.enabled = not item_in_exception_collection and not settings.simplify_status

                    col = box.column(align=True)
                    col.label(text="Properties to Simplify", icon="PROPERTIES")

                    row = col.row()
                    row.prop(obj, 'visibility')

                    row = col.row()
                    row.enabled = obj.exception.type == "MESH" or obj.exception.type == "GPENCIL"
                    row.prop(obj, 'modifiers')
                    row.enabled = settings.modifiers

                    row = col.row()
                    row.enabled = obj.exception.type == "MESH"
                    row.prop(obj, 'shape_keys')
                    row.enabled = settings.shape_keys

                    row = col.row()
                    row.prop(obj, 'drivers')
                    row.enabled = settings.drivers

                    row = col.row()
                    row.enabled = obj.exception.type == "MESH"
                    row.prop(obj, 'normals_auto_smooth')
                    row.enabled = settings.normals_auto_smooth

        else:

            row = layout.row()
            row.enabled = not settings.simplify_status
            row.prop_search(settings, "exception_collection", bpy.data, "collections", text="")
            row = layout.row()
            row.enabled = not settings.simplify_status
            row.prop(settings, "exception_include_subcollections")


class MUSTARDSIMPLIFY_PT_Simplify_ExecutionTimes(MainPanel, bpy.types.Panel):
    bl_label = "Execution Times"
    bl_parent_id = "MUSTARDSIMPLIFY_PT_Simplify"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        modifiers_with_time = [x for x in modifiers if x.execution_time]
        return len(modifiers_with_time) > 0

    def draw_header_preset(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        if addon_prefs.wiki:
            layout.operator("mustard_simplify.openlink", text="",
                            icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#execution-times"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        settings = scene.MustardSimplify_Settings
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        modifiers_with_time = [x for x in modifiers if x.execution_time]

        row = layout.row()
        col = row.column()
        row2 = col.row(align=True)
        row2.prop(settings, "execution_times", icon="ANIM")
        row2.operator("mustard_simplify.update_execution_time", icon="UV_SYNC_SELECT", text="")
        if settings.execution_times:
            col.prop(settings, "execution_times_frames_rate")

        box = layout.box()
        row2 = box.row()
        row2.prop(settings, 'execution_time_order', expand=True)
        row2.scale_y = 1.2
        for modifier in sorted(modifiers_with_time, key=(lambda x: x.name) if
                               settings.execution_time_order == "NAME" else (lambda y: int(y.time*1000)),
                               reverse=settings.execution_time_order == "TIME"):
            row2 = box.row()
            row2.label(text=modifier.disp_name, icon=modifier.icon)
            row2.alert = modifier.time > 0.1
            row2.scale_x = 0.3
            row2.label(text=str(int(modifier.time * 1000)) + " ms")

        if addon_prefs.debug:
            box.separator()
            row2 = box.row()
            row2.label(text="Execution Time Computation Overhead", icon="TIME")
            row2.scale_x = 0.3
            row2.alert = settings.execution_times_overhead > 0.1
            row2.label(text=str(int(settings.execution_times_overhead * 1000)) + " ms")


class MUSTARDSIMPLIFY_PT_Simplify_Advanced(MainPanel, bpy.types.Panel):
    bl_label = "Advanced"
    bl_parent_id = "MUSTARDSIMPLIFY_PT_Simplify"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        return addon_prefs.advanced

    def draw_header_preset(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[base_package].preferences
        if addon_prefs.wiki:
            layout.operator("mustard_simplify.openlink", text="",
                            icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#advanced"

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences
        system = prefs.system

        layout.label(text="Textures Size Limit")
        layout.scale_x = 1.5
        layout.prop(system, "gl_texture_limit", text="")


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Simplify)
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Simplify_Options)
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Simplify_Exceptions)
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Simplify_ExecutionTimes)
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Simplify_Advanced)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Simplify_Advanced)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Simplify_ExecutionTimes)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Simplify_Exceptions)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Simplify_Options)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Simplify)
