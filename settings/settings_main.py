import bpy
from bpy.props import *


class MustardSimplify_Settings(bpy.types.PropertyGroup):

    # Modifiers
    blender_simplify: BoolProperty(name="Blender Simplify",
                                   description="Enable Blender Simplify",
                                   default=True)
    # Modifiers
    modifiers: BoolProperty(name="Modifiers",
                            description="Disable modifiers",
                            default=True)
    # Shape Keys
    shape_keys: BoolProperty(name="Shape Keys",
                             description="Mute un-used shape keys (value different from 0)",
                             default=True)
    shape_keys_disable_not_null: BoolProperty(name="Disable only when Null",
                                              description="Disable only Shape Keys with value equal to 0.\nThis applies only to non-driven Shape Keys (i.e., without drivers or animation keyframes)",
                                              default=True)
    shape_keys_disable_with_drivers: BoolProperty(name="Disable if with Drivers",
                                                  description="Disable Shape Keys driven by drivers",
                                                  default=True)
    shape_keys_disable_with_drivers_not_null: BoolProperty(name="Disable only when Null",
                                                           description="Disable Shape Keys driven by drivers only when null",
                                                           default=False)
    shape_keys_disable_with_keyframes: BoolProperty(name="Disable if with Animation Key-Frames",
                                                    description="Disable Shape Keys driven by animation keyframes regardless of other settings.\nThis is not affected by Disable when Null setting: if the setting is on, these Shape Keys are muted regardless of their value",
                                                    default=False)
    # Physics
    physics: BoolProperty(name="Physics",
                          description="Disable Physics",
                          default=True)
    # Drivers
    drivers: BoolProperty(name="Drivers",
                          description="Disable Drivers",
                          default=True)
    # Normals Auto Smooth
    normals_auto_smooth: BoolProperty(name="Normals Auto Smooth",
                                      description="Disable Normals Auto Smooth",
                                      default=True)

    # UI Settings
    collapse_options: BoolProperty(name="Collapse",
                                   default=True)
    collapse_exceptions: BoolProperty(name="Collapse",
                                      default=True)
    collapse_others: BoolProperty(name="Collapse",
                                  default=True)

    # Exceptions
    exception_type: EnumProperty(name="Exception",
                                 description="Exception Type",
                                 default="OBJECT",
                                 items=(
                                     ("OBJECT", "Objects", "Objects with exceptions", "OBJECT_DATAMODE", 0),
                                     ("COLLISION", "Collection", "Collection with exceptions",
                                      "OUTLINER_COLLECTION", 1)))

    def poll_exception(self, object):
        exceptions = bpy.context.scene.MustardSimplify_Exceptions.exceptions
        exceptions = [x.exception for x in exceptions]
        return not object in exceptions

    exception_select: PointerProperty(type=bpy.types.Object,
                                      poll=poll_exception,
                                      name="Object",
                                      description="Object to add to exceptions")

    exception_collection: PointerProperty(type=bpy.types.Collection,
                                          name="Collection",
                                          description="Collection whose Objects will be considered full exceptions")

    # Internal Settings
    simplify_fastnormals_status: BoolProperty(default=False)
    simplify_status: BoolProperty(default=False)

    # Modifiers to not simplify by default
    modifiers_ignore = ["ARMATURE", "HOOK"]


def register():
    bpy.utils.register_class(MustardSimplify_Settings)
    bpy.types.Scene.MustardSimplify_Settings = PointerProperty(type=MustardSimplify_Settings)


def unregister():
    bpy.utils.unregister_class(MustardSimplify_Settings)
