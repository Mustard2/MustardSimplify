import bpy
import webbrowser
from bpy.props import *


class MUSTARDSIMPLIFY_OT_LinkButton(bpy.types.Operator):
    """Open links in a web browser"""
    bl_idname = "mustard_simplify.openlink"
    bl_label = "Open Link"
    bl_options = {'REGISTER'}

    url: StringProperty(name='URL',
                        description="URL",
                        default="http://blender.org/"
                        )

    def execute(self, context):
        webbrowser.open_new(self.url)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_LinkButton)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_LinkButton)
