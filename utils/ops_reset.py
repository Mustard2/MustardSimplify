import bpy
from bpy.props import *


class MUSTARDSIMPLIFY_OT_ResetSettings(bpy.types.Operator):
    """Reset addon settings"""
    bl_idname = "mustard_simplify.reset_settings"
    bl_label = "Reset Settings"
    bl_options = {'REGISTER'}

    def execute(self, context):

        scene = bpy.context.scene
        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        objects = scene.MustardSimplify_SetObjects.objects

        modifiers.clear()
        objects.clear()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_ResetSettings)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_ResetSettings)