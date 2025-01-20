import bpy.utils


# Modifier status
class MustardSimplify_ModifierStatus(bpy.types.PropertyGroup):
    status: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty(default="")


# Shape Keys
class MustardSimplify_ShapeKeysStatus(bpy.types.PropertyGroup):
    status: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty(default="")


# Class with all the settings variables
class MustardSimplify_ObjectStatus(bpy.types.PropertyGroup):
    # Object visibility status
    visibility: bpy.props.BoolProperty(default=True)

    # Normals Auto Smooth status
    normals_auto_smooth: bpy.props.BoolProperty(default=True)
    # Modifiers status
    modifiers: bpy.props.CollectionProperty(type=MustardSimplify_ModifierStatus)
    # Shape Keys status
    shape_keys: bpy.props.CollectionProperty(type=MustardSimplify_ShapeKeysStatus)


# Class to store the scene status
class MustardSimplify_SceneStatus(bpy.types.PropertyGroup):
    rigidbody_world: bpy.props.BoolProperty(default=False)


# Classes to manage exceptions
class MustardSimplify_Exception(bpy.types.PropertyGroup):
    exception: bpy.props.PointerProperty(type=bpy.types.Object)
    modifiers: bpy.props.BoolProperty(name="Modifiers",
                                      description="Disable modifiers",
                                      default=False)
    shape_keys: bpy.props.BoolProperty(name="Shape Keys",
                                       description="Mute un-used shape keys (value different from 0)",
                                       default=False)
    drivers: bpy.props.BoolProperty(name="Drivers",
                                    description="Disable Drivers",
                                    default=False)
    normals_auto_smooth: bpy.props.BoolProperty(name="Normals Auto Smooth",
                                                description="Disable Normals Auto Smooth",
                                                default=False)
    visibility: bpy.props.BoolProperty(name="Visibility",
                                       description="Hide the Object",
                                       default=False)


class MustardSimplify_Exceptions(bpy.types.PropertyGroup):
    exceptions: bpy.props.CollectionProperty(type=MustardSimplify_Exception)


def register():
    bpy.utils.register_class(MustardSimplify_ModifierStatus)

    bpy.utils.register_class(MustardSimplify_ShapeKeysStatus)

    bpy.utils.register_class(MustardSimplify_ObjectStatus)
    bpy.types.Object.MustardSimplify_Status = bpy.props.PointerProperty(type=MustardSimplify_ObjectStatus)

    bpy.utils.register_class(MustardSimplify_SceneStatus)
    bpy.types.Scene.MustardSimplify_Status = bpy.props.PointerProperty(type=MustardSimplify_SceneStatus)

    bpy.utils.register_class(MustardSimplify_Exception)

    bpy.utils.register_class(MustardSimplify_Exceptions)
    bpy.types.Scene.MustardSimplify_Exceptions = bpy.props.PointerProperty(type=MustardSimplify_Exceptions)


def unregister():
    del bpy.types.Scene.MustardSimplify_Exceptions
    bpy.utils.unregister_class(MustardSimplify_Exceptions)

    bpy.utils.unregister_class(MustardSimplify_Exception)

    del bpy.types.Scene.MustardSimplify_Status
    bpy.utils.unregister_class(MustardSimplify_SceneStatus)

    del bpy.types.Object.MustardSimplify_Status
    bpy.utils.unregister_class(MustardSimplify_ObjectStatus)

    bpy.utils.unregister_class(MustardSimplify_ShapeKeysStatus)

    bpy.utils.unregister_class(MustardSimplify_ModifierStatus)
