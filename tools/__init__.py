from . import ops_complexity_analyzer, ops_data_removal, ops_fast_normals, ops_proxy


def register():
    ops_data_removal.register()
    ops_fast_normals.register()
    ops_proxy.register()
    ops_complexity_analyzer.register()


def unregister():
    ops_complexity_analyzer.unregister()
    ops_proxy.unregister()
    ops_fast_normals.unregister()
    ops_data_removal.unregister()
