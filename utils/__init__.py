from . import ops_link
from . import ops_reset
from . import execution_time


def register():
    ops_link.register()
    ops_reset.register()
    execution_time.register()


def unregister():
    execution_time.unregister()
    ops_reset.unregister()
    ops_link.unregister()
