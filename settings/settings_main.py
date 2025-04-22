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
    physics: BoolProperty(name="Physics (Rigid Bodies)",
                          description="Disable Physics: controls rigid bodies only",
                          default=True)
    # Drivers
    drivers: BoolProperty(name="Drivers",
                          description="Disable Drivers",
                          default=True)
    # Normals Auto Smooth
    normals_auto_smooth: BoolProperty(name="Normals Auto Smooth",
                                      description="Disable Normals Auto Smooth",
                                      default=True)

    # Objects
    objects: BoolProperty(name="Objects",
                          description="Hide objects",
                          default=False)

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
    exception_include_subcollections: BoolProperty(default=True,
                                                   name="Include Objects in Sub-collections",
                                                   description="Objects in Sub-section of the selected collection are considered full exceptions.\nDisable to add only the Objects directly in the added collection")

    # Internal Settings
    simplify_fastnormals_status: BoolProperty(default=False)
    simplify_status: BoolProperty(default=False)

    # Modifiers to not simplify by default
    modifiers_ignore = ["ARMATURE", "HOOK"]

    # Objects to not simplify by default
    objects_ignore = ["MESH", "LIGHT", "CAMERA", "EMPTY", "ARMATURE", "CURVE", "SURFACE", "FONT"]

    # Execution Time
    execution_times: BoolProperty(name="Enable Animations Update",
                                  description="Automatically update the Execution Times during animations",
                                  default=False)
    execution_times_frames_rate: IntProperty(name="Update Frame-rate",
                                             description="Frames between Execution Time computation updates.\nA small number can affect Viewport performance.\nSet to 0 to update at every frame",
                                             default=30,
                                             min=0)
    execution_time_order: EnumProperty(name="Execution Time list order",
                                 default="NAME",
                                 items=(
                                     ("NAME", "Name", "Order by name", "SORTALPHA", 0),
                                     ("TIME", "Time", "Order by time", "TIME", 1))
                                       )
    # Internal
    execution_times_frames: IntProperty(default=0)
    execution_times_overhead: FloatProperty(default=0.)


def register():
    bpy.utils.register_class(MustardSimplify_Settings)
    bpy.types.Scene.MustardSimplify_Settings = PointerProperty(type=MustardSimplify_Settings)


def unregister():
    del bpy.types.Scene.MustardSimplify_Settings
    bpy.utils.unregister_class(MustardSimplify_Settings)
