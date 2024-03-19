from . import settings_main
from . import settings_addon


def register():
    settings_addon.register()
    settings_main.register()


def unregister():
    settings_main.unregister()
    settings_addon.unregister()
