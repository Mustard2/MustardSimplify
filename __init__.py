# Mustard Simplify addon
# GitHub page: https://github.com/Mustard2/MustardSimplify/

# Add-on information
bl_info = {
    "name": "Mustard Simplify",
    "description": "A set of tools to simplify scenes for better viewport performance",
    "author": "Mustard",
    "version": (2025, 2, 0),
    "blender": (4, 3, 0),
    "warning": "",
    "doc_url": "https://github.com/Mustard2/MustardSimplify/wiki",
    "category": "Scene",
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
