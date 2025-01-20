import bpy
import time
from bpy.app.handlers import persistent
from .. import __package__ as base_package


def update_all_execution_time():
    bpy.context.view_layer.update()

    context = bpy.context
    scene = context.scene
    depsgraph = context.view_layer.depsgraph

    modifiers = scene.MustardSimplify_SetModifiers.modifiers

    for modifier in modifiers:
        modifier.time = 0.

    if depsgraph:
        for obj in context.scene.objects:
            if obj:
                ob_eval = obj.evaluated_get(depsgraph)
                for modifier in ob_eval.modifiers:
                    if modifier.show_viewport:
                        modifiers[modifier.type].time += modifier.execution_time


@persistent
def update_animation_execution_time(scene):
    import time

    settings = scene.MustardSimplify_Settings
    addon_prefs = bpy.context.preferences.addons[base_package].preferences

    start = 0.
    if addon_prefs.debug:
        start = time.time()

    if not settings.execution_times:
        settings.execution_times_overhead = time.time() - start
        return

    if settings.execution_times_frames != 0:
        settings.execution_times_frames += 1
        if settings.execution_times_frames >= settings.execution_times_frames_rate:
            settings.execution_times_frames = 0
        return

    context = bpy.context
    scene = context.scene
    depsgraph = context.view_layer.depsgraph

    modifiers = scene.MustardSimplify_SetModifiers.modifiers
    modifiers_to_compute = [x.name for x in modifiers if x.execution_time]

    for modifier in modifiers:
        modifier.time = 0.

    if depsgraph:
        for obj in context.scene.objects:
            if obj:
                obj_modifiers_to_compute = [x for x in obj.modifiers if x.type in modifiers_to_compute]
                if len(obj_modifiers_to_compute):
                    ob_eval = obj.evaluated_get(depsgraph)
                    for modifier in ob_eval.modifiers:
                        if modifier.show_viewport and modifier.type in modifiers_to_compute:
                            modifiers[modifier.type].time += modifier.execution_time

    settings.execution_times_frames += 1

    if addon_prefs.debug:
        settings.execution_times_overhead = time.time() - start


class MUSTARDSIMPLIFY_OT_UpdateExecutionTime(bpy.types.Operator):
    """Update the report of execution for every modifier"""
    bl_idname = "mustard_simplify.update_execution_time"
    bl_label = "Update Execution time"

    def execute(self, context):
        bpy.context.view_layer.update()
        update_all_execution_time()
        self.report({'INFO'}, 'Mustard Simplify - Modifiers Execution Time has been updated.')
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_UpdateExecutionTime)
    bpy.app.handlers.frame_change_pre.append(update_animation_execution_time)


def unregister():
    bpy.app.handlers.frame_change_pre.remove(update_animation_execution_time)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_UpdateExecutionTime)
