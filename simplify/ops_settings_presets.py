import os
import shutil

import bpy
from bl_operators.presets import AddPresetBase

# Settings (on scene.MustardSimplify_Settings) that make up a Simplify preset.
# Keep in sync with the Options panel and the Shape Keys settings dialog.
PRESET_VALUES = [
    "settings.blender_simplify",
    "settings.objects",
    "settings.culling",
    "settings.modifiers",
    "settings.shape_keys",
    "settings.shape_keys_disable_not_null",
    "settings.shape_keys_disable_with_drivers",
    "settings.shape_keys_disable_with_drivers_not_null",
    "settings.shape_keys_disable_with_keyframes",
    "settings.drivers",
    "settings.physics",
]

# Blender Simplify settings
BLENDER_SIMPLIFY_PRESET_VALUES = [
    "rd.simplify_subdivision",
    "rd.simplify_child_particles",
    "rd.simplify_volumes",
    "rd.use_simplify_normals",
    "rd.simplify_subdivision_render",
    "rd.simplify_child_particles_render",
]

# Cycles-only settings
CYCLES_SIMPLIFY_PRESET_VALUES = [
    "cscene.texture_limit",
    "cscene.texture_limit_render",
    "cscene.use_camera_cull",
    "cscene.camera_cull_margin",
    "cscene.use_distance_cull",
    "cscene.distance_cull_margin",
]
CYCLES_TEXTURE_RESOLUTION_PRESET_VALUES = [
    "cscene.texture_resolution",
    "cscene.texture_resolution_render",
]

PRESET_SUBDIR = "mustard_simplify/simplify"

# Presets shipped with the addon, copied into the user preset folder on
# register()
BUNDLED_PRESET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "presets",
    PRESET_SUBDIR,
)


def install_default_presets():
    if not os.path.isdir(BUNDLED_PRESET_DIR):
        return

    target_dir = bpy.utils.user_resource(
        "SCRIPTS", path=os.path.join("presets", PRESET_SUBDIR), create=True
    )
    if not target_dir:
        return

    for filename in os.listdir(BUNDLED_PRESET_DIR):
        if not filename.endswith(".py"):
            continue

        target_path = os.path.join(target_dir, filename)
        if os.path.isfile(target_path):
            continue

        shutil.copy(os.path.join(BUNDLED_PRESET_DIR, filename), target_path)


class MUSTARDSIMPLIFY_MT_SimplifyPresets(bpy.types.Menu):
    """Simplify settings presets"""

    bl_label = "Simplify Presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class MUSTARDSIMPLIFY_OT_AddSimplifyPreset(AddPresetBase, bpy.types.Operator):
    """Add or remove a Simplify settings preset"""

    bl_idname = "mustard_simplify.add_simplify_preset"
    bl_label = "Add Simplify Preset"
    preset_menu = "MUSTARDSIMPLIFY_MT_SimplifyPresets"

    preset_defines = [
        "settings = bpy.context.scene.MustardSimplify_Settings",
        "rd = bpy.context.scene.render",
        "cscene = bpy.context.scene.cycles "
        "if hasattr(bpy.context.scene, 'cycles') else None",
    ]
    preset_subdir = PRESET_SUBDIR

    @classmethod
    def poll(cls, context):
        # Disallow editing presets while the scene is simplified
        settings = context.scene.MustardSimplify_Settings
        return not settings.simplify_status

    def execute(self, context):
        # Save Blender Simplify setings
        scene = context.scene
        preset_values = list(PRESET_VALUES) + list(BLENDER_SIMPLIFY_PRESET_VALUES)
        if hasattr(scene, "cycles"):
            preset_values += CYCLES_SIMPLIFY_PRESET_VALUES
            if hasattr(scene.cycles, "texture_resolution"):
                preset_values += CYCLES_TEXTURE_RESOLUTION_PRESET_VALUES
        self.preset_values = preset_values

        result = super().execute(context)

        # Save the per-modifier and per-object settings
        is_remove = self.remove_name or self.remove_active
        if "FINISHED" in result and not is_remove:
            self._append_collections(context)

        return result

    def _append_collections(self, context):
        filepath = self._preset_filepath()

        if filepath is None or not os.path.isfile(filepath):
            return

        scene = context.scene
        try:
            with open(filepath, "a", encoding="utf-8") as file_preset:
                self._write_collection(
                    file_preset,
                    comment="Modifiers selection",
                    refresh_op="bpy.ops.mustard_simplify.refresh_modifiers()",
                    collection_path="bpy.context.scene.MustardSimplify_SetModifiers"
                    ".modifiers",
                    state={
                        m.name: m.simplify
                        for m in scene.MustardSimplify_SetModifiers.modifiers
                    },
                )
                self._write_collection(
                    file_preset,
                    comment="Objects selection",
                    refresh_op="bpy.ops.mustard_simplify.refresh_objects()",
                    collection_path="bpy.context.scene.MustardSimplify_SetObjects"
                    ".objects",
                    state={
                        o.name: o.simplify
                        for o in scene.MustardSimplify_SetObjects.objects
                    },
                )
        except OSError as err:
            self.report(
                {"WARNING"},
                "Mustard Simplify - Could not write selection data to preset: %s" % err,
            )

    @staticmethod
    def _write_collection(file_preset, comment, refresh_op, collection_path, state):
        file_preset.write("\n# %s\n" % comment)
        file_preset.write("%s\n" % refresh_op)
        file_preset.write("mustard_collection = %s\n" % collection_path)
        file_preset.write("mustard_state = %r\n" % state)
        file_preset.write("for mustard_item in mustard_collection:\n")
        file_preset.write("    if mustard_item.name in mustard_state:\n")
        file_preset.write(
            "        mustard_item.simplify = mustard_state[mustard_item.name]\n"
        )

    def _preset_filepath(self):
        name = self.name.strip()
        if not name:
            return None

        filename = self.as_filename(name) + ".py"
        target_path = os.path.join("presets", self.preset_subdir)
        target_path = bpy.utils.user_resource("SCRIPTS", path=target_path)
        if not target_path:
            return None

        return os.path.join(target_path, filename)


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_MT_SimplifyPresets)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_AddSimplifyPreset)
    install_default_presets()


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_AddSimplifyPreset)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_MT_SimplifyPresets)
