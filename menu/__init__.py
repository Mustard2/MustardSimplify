class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Simplify"


from . import menu_simplify
from . import menu_tools
from . import menu_camera_hide


def register():
    menu_simplify.register()
    menu_camera_hide.register()
    menu_tools.register()


def unregister():
    menu_tools.unregister()
    menu_camera_hide.unregister()
    menu_simplify.unregister()
