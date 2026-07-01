import os

import bpy
from bl_operators.presets import AddPresetBase

# Settings (on scene.MustardSimplify_Settings) that make up a Simplify preset.
# Keep in sync with the Options panel and the Shape Keys settings dialog.
PRESET_VALUES = [
    "settings.blender_simplify",
    "settings.objects",
    "settings.modifiers",
    "settings.shape_keys",
    "settings.shape_keys_disable_not_null",
    "settings.shape_keys_disable_with_drivers",
    "settings.shape_keys_disable_with_drivers_not_null",
    "settings.shape_keys_disable_with_keyframes",
    "settings.drivers",
    "settings.physics",
]

PRESET_SUBDIR = "mustard_simplify/simplify"


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

    preset_defines = ["settings = bpy.context.scene.MustardSimplify_Settings"]
    preset_values = PRESET_VALUES
    preset_subdir = PRESET_SUBDIR

    @classmethod
    def poll(cls, context):
        # Disallow editing presets while the scene is simplified
        settings = context.scene.MustardSimplify_Settings
        return not settings.simplify_status

    def execute(self, context):
        result = super().execute(context)

        # The per-modifier and per-object "simplify" selections live in
        # CollectionProperties, which AddPresetBase cannot serialize. On add, append
        # them to the generated preset file so they are restored together with the
        # other settings.
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
        # Mirror the path AddPresetBase uses to write the preset file
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


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_AddSimplifyPreset)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_MT_SimplifyPresets)
