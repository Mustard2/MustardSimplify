from . import (
    ops_camera_hide,
    ops_settings_blender_simplify,
    ops_settings_modifiers,
    ops_settings_objects,
    ops_settings_presets,
    ops_settings_shape_keys,
    ops_simplify,
    ops_viewport_button,
    simplify_status,
    ui_exceptions,
)


def register():
    simplify_status.register()
    ops_settings_presets.register()
    ops_settings_shape_keys.register()
    ops_settings_modifiers.register()
    ops_settings_objects.register()
    ops_settings_blender_simplify.register()
    ui_exceptions.register()
    ops_simplify.register()
    ops_camera_hide.register()
    ops_viewport_button.register()


def unregister():
    ops_viewport_button.unregister()
    ops_camera_hide.unregister()
    ops_simplify.unregister()
    ui_exceptions.unregister()
    ops_settings_blender_simplify.unregister()
    ops_settings_objects.unregister()
    ops_settings_modifiers.unregister()
    ops_settings_shape_keys.unregister()
    ops_settings_presets.unregister()
    simplify_status.unregister()
