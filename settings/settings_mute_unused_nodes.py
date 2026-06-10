import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, PointerProperty

is_first_run = True


def is_used_node(node):
    end_types = [
        "OUTPUT_MATERIAL",
        "OUTPUT",
        "VIEWER",
        "COMPOSITE",
        "SPLITVIEWER",
        "OUTPUT_FILE",
        "LEVELS",
        "OUTPUT_LIGHT",
        "OUTPUT_WORLD",
        "GROUP_INPUT",
        "GROUP_OUTPUT",
        "FRAME",
        "WARNING",
    ]
    if node.type in end_types:
        return True

    for output in node.outputs:
        if output.links:
            return True
    return False


def get_all_parent_nodes(node, parents_list=None):
    if parents_list is None:
        parents_list = []
    for input in node.inputs:
        if input.is_linked:
            for link in input.links:
                parent = link.from_node
                if parent not in parents_list:
                    parents_list.append(parent)
                    get_all_parent_nodes(parent, parents_list)
    return parents_list


def mute_unused_nodes(material):
    if material and material.node_tree:
        nodes = material.node_tree.nodes
        unused_nodes = []
        for node in nodes:
            if not is_used_node(node):
                unused_nodes.append(node)
        for node in unused_nodes:
            node.mute = True
            parent_nodes = get_all_parent_nodes(node)
            for parent in parent_nodes:
                parent.mute = True


@persistent
def updater(self, context):
    settings = context.scene.MustardSimplify_MuteUnusedNodesSettings
    global is_first_run
    if settings.mute_unused_shader_nodes:
        if is_first_run:
            # Run for all the materials to mute all the unused nodes on the activation
            for material in bpy.data.materials:
                mute_unused_nodes(material=material)
            is_first_run = False
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for update in depsgraph.updates:
            # Check if the ID is a Material datablock
            if isinstance(update.id.original, bpy.types.Material):
                material_name = update.id.original.name
                material = bpy.data.materials.get(material_name)
                mute_unused_nodes(material)


class MustardSimplify_MuteUnusedNodesSettings(bpy.types.PropertyGroup):
    mute_unused_shader_nodes: BoolProperty(
        name="Mute Unused Shader Nodes",
        description="Mute shader nodes that are not connected.\nThis can help improve "
        "performance by preventing unnecessary shader calculations.",
        default=False,
        update=updater,
    )


def register():
    global is_first_run
    is_first_run = True
    if updater not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(updater)
    bpy.utils.register_class(MustardSimplify_MuteUnusedNodesSettings)
    bpy.types.Scene.MustardSimplify_MuteUnusedNodesSettings = PointerProperty(
        type=MustardSimplify_MuteUnusedNodesSettings
    )


def unregister():
    del bpy.types.Scene.MustardSimplify_MuteUnusedNodesSettings
    bpy.utils.unregister_class(MustardSimplify_MuteUnusedNodesSettings)
    if updater in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(updater)
