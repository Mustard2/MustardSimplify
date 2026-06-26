import bpy.utils


# Modifier status
class MustardSimplify_ModifierStatus(bpy.types.PropertyGroup):
    status: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty(default="")


# Shape Keys
class MustardSimplify_ShapeKeysStatus(bpy.types.PropertyGroup):
    status: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty(default="")


# Per-object status.
# Stored on the Object itself for normal objects (backwards compatible), and on
# the Scene (keyed by the object pointer) for library-override objects, whose
# custom property collections are read-only.
class MustardSimplify_ObjectStatus(bpy.types.PropertyGroup):
    # Object visibility status
    visibility: bpy.props.BoolProperty(default=True)

    # Modifiers status
    modifiers: bpy.props.CollectionProperty(type=MustardSimplify_ModifierStatus)
    # Shape Keys status
    shape_keys: bpy.props.CollectionProperty(type=MustardSimplify_ShapeKeysStatus)

    # Object reference (used as key when stored on the Scene)
    object: bpy.props.PointerProperty(type=bpy.types.Object)


# Class to store the scene status
class MustardSimplify_SceneStatus(bpy.types.PropertyGroup):
    rigidbody_world: bpy.props.BoolProperty(default=False)

    # Per-object status entries (keyed by the object pointer)
    # This is a fallback when the per-Object simplification options can not be
    # saved directly on the Object (for instace for linked Objects)
    objects: bpy.props.CollectionProperty(type=MustardSimplify_ObjectStatus)


# Classes to manage exceptions
class MustardSimplify_Exception(bpy.types.PropertyGroup):
    exception: bpy.props.PointerProperty(type=bpy.types.Object)
    modifiers: bpy.props.BoolProperty(
        name="Modifiers", description="Disable modifiers", default=False
    )
    shape_keys: bpy.props.BoolProperty(
        name="Shape Keys",
        description="Mute un-used shape keys (value different from 0)",
        default=False,
    )
    drivers: bpy.props.BoolProperty(
        name="Drivers", description="Disable Drivers", default=False
    )
    visibility: bpy.props.BoolProperty(
        name="Visibility", description="Hide the Object", default=False
    )
    camera_hide: bpy.props.BoolProperty(
        name="Camera Hide", description="Apply the Camera Hide operation", default=False
    )


class MustardSimplify_Exceptions(bpy.types.PropertyGroup):
    exceptions: bpy.props.CollectionProperty(type=MustardSimplify_Exception)


def register():
    bpy.utils.register_class(MustardSimplify_ModifierStatus)

    bpy.utils.register_class(MustardSimplify_ShapeKeysStatus)

    bpy.utils.register_class(MustardSimplify_ObjectStatus)
    bpy.types.Object.MustardSimplify_Status = bpy.props.PointerProperty(
        type=MustardSimplify_ObjectStatus
    )

    bpy.utils.register_class(MustardSimplify_SceneStatus)
    bpy.types.Scene.MustardSimplify_Status = bpy.props.PointerProperty(
        type=MustardSimplify_SceneStatus
    )

    bpy.utils.register_class(MustardSimplify_Exception)

    bpy.utils.register_class(MustardSimplify_Exceptions)
    bpy.types.Scene.MustardSimplify_Exceptions = bpy.props.PointerProperty(
        type=MustardSimplify_Exceptions
    )


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
