import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
)


def _complexity_analyzer_mode_update(context):
    # Re-apply the heatmap instantly when the mode changes while active.
    from ..tools import ops_complexity_analyzer

    if context.scene.MustardSimplify_Settings.complexity_analyzer_active:
        ops_complexity_analyzer.apply_heatmap(context)


def _complexity_analyzer_live_update_update(context):
    # Register/unregister the live timer when the toggle flips.
    from ..tools import ops_complexity_analyzer

    if context.scene.MustardSimplify_Settings.complexity_analyzer_live_update:
        ops_complexity_analyzer.register_live_handler()
    else:
        ops_complexity_analyzer.unregister_live_handler()


class MustardSimplify_Settings(bpy.types.PropertyGroup):
    # Modifiers
    blender_simplify: BoolProperty(
        name="Blender Simplify", description="Enable Blender Simplify", default=True
    )
    blender_simplify_engine: EnumProperty(
        name="Engine",
        description="Render engine whose Simplify settings should be shown",
        default="CYCLES",
        items=(
            ("EEVEE", "Eevee", "Show Eevee Simplify settings", "SHADING_RENDERED", 0),
            ("CYCLES", "Cycles", "Show Cycles Simplify settings", "SCENE", 1),
        ),
    )
    # Modifiers
    modifiers: BoolProperty(
        name="Modifiers", description="Disable modifiers", default=True
    )
    # Shape Keys
    shape_keys: BoolProperty(
        name="Shape Keys",
        description="Mute un-used shape keys (value different from 0)",
        default=True,
    )
    shape_keys_disable_not_null: BoolProperty(
        name="Disable only when Null",
        description="Disable only Shape Keys with value equal to 0.\nThis applies only "
        "to non-driven Shape Keys (i.e., without drivers or animation keyframes)",
        default=True,
    )
    shape_keys_disable_with_drivers: BoolProperty(
        name="Disable if with Drivers",
        description="Disable Shape Keys driven by drivers",
        default=True,
    )
    shape_keys_disable_with_drivers_not_null: BoolProperty(
        name="Disable only when Null",
        description="Disable Shape Keys driven by drivers only when null",
        default=False,
    )
    shape_keys_disable_with_keyframes: BoolProperty(
        name="Disable if with Animation Key-Frames",
        description="Disable Shape Keys driven by animation keyframes regardless of "
        "other settings.\nThis is not affected by Disable when Null setting: if the "
        "setting is on, these Shape Keys are muted regardless of their value",
        default=False,
    )
    # Physics
    physics: BoolProperty(
        name="Physics (Rigid Bodies)",
        description="Disable Physics: controls rigid bodies only",
        default=True,
    )
    # Drivers
    drivers: BoolProperty(name="Drivers", description="Disable Drivers", default=True)

    # Objects
    objects: BoolProperty(name="Objects", description="Hide objects", default=False)

    # Exceptions
    exception_type: EnumProperty(
        name="Exception",
        description="Exception Type",
        default="OBJECT",
        items=(
            ("OBJECT", "Objects", "Objects with exceptions", "OBJECT_DATAMODE", 0),
            (
                "COLLISION",
                "Collection",
                "Collection with exceptions",
                "OUTLINER_COLLECTION",
                1,
            ),
        ),
    )

    exception_collection: PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="Collection whose Objects will be considered full exceptions",
    )
    exception_include_subcollections: BoolProperty(
        default=True,
        name="Include Objects in Sub-collections",
        description="Objects in Sub-section of the selected collection are considered "
        "full exceptions.\nDisable to add only the Objects directly in the added "
        "collection",
    )

    # Complexity Analyzer
    complexity_analyzer_mode: EnumProperty(
        name="Show",
        description="What property to visualize across the scene",
        items=(
            (
                "POLYS",
                "Polygon count",
                "Color meshes by the number of polygons (modifiers included)",
                "MESH_DATA",
                0,
            ),
            (
                "TEXTURES",
                "Texture resolution",
                "Color meshes by the total pixel count of every texture across their "
                "materials",
                "TEXTURE",
                1,
            ),
            (
                "MODIFIERS",
                "Modifier number",
                "Color meshes by the number of active modifiers on each object",
                "MODIFIER",
                2,
            ),
        ),
        default="POLYS",
        update=lambda self, context: _complexity_analyzer_mode_update(context),
    )
    complexity_analyzer_live_update: BoolProperty(
        name="Live update",
        description="Continuously refresh the heatmap as the scene changes.\n"
        "Performance cost: re-evaluates every mesh on every update",
        default=False,
        update=lambda self, context: _complexity_analyzer_live_update_update(context),
    )
    complexity_analyzer_active: BoolProperty(default=False)

    # Internal Settings
    simplify_fastnormals_status: BoolProperty(default=False)
    simplify_status: BoolProperty(default=False)

    # Modifiers to not simplify by default
    modifiers_ignore = ["ARMATURE", "HOOK"]

    # Objects to not simplify by default
    objects_ignore = [
        "MESH",
        "LIGHT",
        "CAMERA",
        "EMPTY",
        "ARMATURE",
        "CURVE",
        "SURFACE",
        "FONT",
    ]

    # Execution Time
    execution_times: BoolProperty(
        name="Enable Animations Update",
        description="Automatically update the Execution Times during animations",
        default=False,
    )
    execution_times_frames_rate: IntProperty(
        name="Update Frame-rate",
        description="Frames between Execution Time computation updates.\nA small "
        "number can affect Viewport performance.\nSet to 0 to update at every frame",
        default=30,
        min=0,
    )
    execution_time_order: EnumProperty(
        name="Execution Time list order",
        default="NAME",
        items=(
            ("NAME", "Name", "Order by name", "SORTALPHA", 0),
            ("TIME", "Time", "Order by time", "TIME", 1),
        ),
    )

    # Camera Hide
    live_frustum_running: BoolProperty(default=False)
    live_frustum_should_stop: BoolProperty(default=False)
    live_frustum_interval: FloatProperty(
        name="Update Interval",
        description="Time in seconds between Camera Hide updates",
        default=0.2,
        min=0.01,
        max=5.0,
        step=0.01,
        precision=2,
    )

    # Internal
    execution_times_frames: IntProperty(default=0)
    execution_times_overhead: FloatProperty(default=0.0)

    # Camera Hidden
    live_frustum_single_applied: BoolProperty(default=False)


def register():
    bpy.utils.register_class(MustardSimplify_Settings)
    bpy.types.Scene.MustardSimplify_Settings = PointerProperty(
        type=MustardSimplify_Settings
    )


def unregister():
    del bpy.types.Scene.MustardSimplify_Settings
    bpy.utils.unregister_class(MustardSimplify_Settings)
