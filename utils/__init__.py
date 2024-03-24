from . import ops_link
from . import ops_reset


def register():
    ops_link.register()
    ops_reset.register()


def unregister():
    ops_reset.unregister()
    ops_link.unregister()
