from . import ops_data_removal, ops_fast_normals, ops_proxy


def register():
    ops_data_removal.register()
    ops_fast_normals.register()
    ops_proxy.register()


def unregister():
    ops_proxy.unregister()
    ops_fast_normals.unregister()
    ops_data_removal.unregister()
