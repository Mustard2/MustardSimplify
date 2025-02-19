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
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

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

        box = layout.box()
        row = box.row()
        row.prop(settings, 'collapse_options', text="",
                 icon="RIGHTARROW" if settings.collapse_options else "DOWNARROW_HLT", emboss=False)
        row.label(text="Options")
        if addon_prefs.wiki:
            row.operator("mustard_simplify.openlink", text="",
                         icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#simplify"
        if not settings.collapse_options:
            row = box.row()
            col = row.column()
            row.enabled = not settings.simplify_status
            col.prop(settings, "blender_simplify")
            row.operator("mustard_simplify.menu_blender_simplify_settings", icon="PREFERENCES", text="")

            col = box.column(align=True)
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

        box = layout.box()
        row = box.row()
        row.prop(settings, 'collapse_exceptions', text="",
                 icon="RIGHTARROW" if settings.collapse_exceptions else "DOWNARROW_HLT", emboss=False)
        row.label(text="Exceptions")
        if addon_prefs.wiki:
            row.operator("mustard_simplify.openlink", text="",
                         icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#exceptions"
        if not settings.collapse_exceptions:

            row = box.row()
            row.prop(settings, 'exception_type', expand=True)
            row.enabled = not settings.simplify_status

            if settings.exception_type == "OBJECT":

                row = box.row()
                row.enabled = not settings.simplify_status
                row.template_list("MUSTARDSIMPLIFY_UL_Exceptions_UIList", "The_List", scene.MustardSimplify_Exceptions,
                                  "exceptions", scene, "mustardsimplify_exception_uilist_index")
                col = row.column(align=True)
                col.operator("mustard_simplify.remove_exception", icon="REMOVE", text="")

                row = box.row()
                row.enabled = not settings.simplify_status
                row.prop_search(settings, "exception_select", scene, "objects", text="")
                row.operator("mustard_simplify.add_exception", text="", icon="ADD")

                if scene.mustardsimplify_exception_uilist_index > -1 and len(
                        scene.MustardSimplify_Exceptions.exceptions) > 0:
                    obj = scene.MustardSimplify_Exceptions.exceptions[scene.mustardsimplify_exception_uilist_index]

                    if obj is not None:
                        box = box.box()
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

                row = box.row()
                row.enabled = not settings.simplify_status
                row.prop_search(settings, "exception_collection", bpy.data, "collections", text="")
                row = box.row()
                row.enabled = not settings.simplify_status
                row.prop(settings, "exception_include_subcollections")

        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        modifiers_with_time = [x for x in modifiers if x.execution_time]
        if len(modifiers_with_time) > 0:
            box = layout.box()
            row = box.row()
            row.prop(settings, 'collapse_times', text="",
                     icon="RIGHTARROW" if settings.collapse_times else "DOWNARROW_HLT", emboss=False)
            row.label(text="Execution Times")
            if addon_prefs.wiki:
                row.operator("mustard_simplify.openlink", text="",
                             icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#execution-times"
            if not settings.collapse_times:
                row = box.row()
                col = row.column()
                row2 = col.row(align=True)
                row2.prop(settings, "execution_times", icon="ANIM")
                row2.operator("mustard_simplify.update_execution_time", icon="UV_SYNC_SELECT", text="")
                if settings.execution_times:
                    col.prop(settings, "execution_times_frames_rate")

                box2 = box.box()
                row2 = box2.row()
                row2.prop(settings, 'execution_time_order', expand=True)
                row2.scale_y = 1.2
                for modifier in sorted(modifiers_with_time, key=(lambda x: x.name) if
                                       settings.execution_time_order == "NAME" else (lambda y: int(y.time*1000)),
                                       reverse=settings.execution_time_order == "TIME"):
                    row2 = box2.row()
                    row2.label(text=modifier.disp_name, icon=modifier.icon)
                    row2.alert = modifier.time > 0.1
                    row2.scale_x = 0.3
                    row2.label(text=str(int(modifier.time * 1000)) + " ms")

                if addon_prefs.debug:
                    box2.separator()
                    row2 = box2.row()
                    row2.label(text="Execution Time Computation Overhead", icon="TIME")
                    row2.scale_x = 0.3
                    row2.alert = settings.execution_times_overhead > 0.1
                    row2.label(text=str(int(settings.execution_times_overhead * 1000)) + " ms")

        if addon_prefs.advanced:
            box = layout.box()
            row = box.row()
            row.prop(settings, 'collapse_others', text="",
                     icon="RIGHTARROW" if settings.collapse_others else "DOWNARROW_HLT", emboss=False)
            row.label(text="Advanced")
            row.operator("mustard_simplify.openlink", text="",
                         icon="QUESTION").url = "https://github.com/Mustard2/MustardSimplify/wiki#advanced"
            if not settings.collapse_others:
                row = box.row()

                prefs = context.preferences
                system = prefs.system

                row.label(text="Textures Size Limit")
                row.scale_x = 1.5
                row.prop(system, "gl_texture_limit", text="")


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_PT_Simplify)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_PT_Simplify)
