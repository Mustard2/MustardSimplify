from . import ui_exceptions
from . import simplify_status
from . import ops_settings_blender_simplify
from . import ops_settings_modifiers
from . import ops_settings_shape_keys
from . import ops_simplify


def register():
    simplify_status.register()
    ops_settings_shape_keys.register()
    ops_settings_modifiers.register()
    ops_settings_blender_simplify.register()
    ui_exceptions.register()
    ops_simplify.register()


def unregister():
    ops_simplify.unregister()
    ui_exceptions.unregister()
    ops_settings_blender_simplify.unregister()
    ops_settings_modifiers.unregister()
    ops_settings_shape_keys.unregister()
    simplify_status.unregister()
