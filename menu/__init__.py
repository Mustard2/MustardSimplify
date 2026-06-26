class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Simplify"


from . import (  # noqa: E402
    menu_camera_hide,
    menu_complexity_analyzer,
    menu_simplify,
    menu_tools,
)


def register():
    menu_simplify.register()
    menu_camera_hide.register()
    menu_complexity_analyzer.register()
    menu_tools.register()


def unregister():
    menu_tools.unregister()
    menu_complexity_analyzer.unregister()
    menu_camera_hide.unregister()
    menu_simplify.unregister()
