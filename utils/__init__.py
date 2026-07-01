from . import execution_time, ops_reset, pre_render


def register():
    ops_reset.register()
    execution_time.register()
    pre_render.register()


def unregister():
    pre_render.unregister()
    execution_time.unregister()
    ops_reset.unregister()
