class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Simplify"


from . import menu_simplify
from . import menu_tools
from . import menu_settings


def register():
    menu_simplify.register()
    menu_tools.register()
    menu_settings.register()


def unregister():
    menu_settings.unregister()
    menu_tools.unregister()
    menu_simplify.unregister()
