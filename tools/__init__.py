from . import ops_data_removal, ops_fast_normals, ops_mannequin


def register():
    ops_data_removal.register()
    ops_fast_normals.register()
    ops_mannequin.register()


def unregister():
    ops_mannequin.unregister()
    ops_fast_normals.unregister()
    ops_data_removal.unregister()
