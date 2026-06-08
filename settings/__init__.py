from . import settings_addon, settings_main, settings_mute_unused_nodes


def register():
    settings_addon.register()
    settings_main.register()
    settings_mute_unused_nodes.register()


def unregister():
    settings_mute_unused_nodes.unregister()
    settings_main.unregister()
    settings_addon.unregister()
