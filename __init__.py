# Mustard Simplify addon
# GitHub page: https://github.com/Mustard2/MustardSimplify/

# Add-on information
bl_info = {
    "name": "Mustard Simplify",
    "description": "A set of tools to simplify scenes for better viewport performance",
    "author": "Mustard",
    "version": (0, 4, 0),
    "blender": (4, 1, 0),
    "warning": "",
    "doc_url": "https://github.com/Mustard2/MustardSimplify/wiki",
    "category": "3D View",
}


from . import settings
from . import simplify
from . import tools
from . import utils
from . import menu


def register():
    settings.register()
    simplify.register()
    tools.register()
    utils.register()
    menu.register()


def unregister():
    menu.unregister()
    utils.unregister()
    tools.unregister()
    simplify.unregister()
    settings.unregister()
