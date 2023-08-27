# Mustard Simplify
# https://github.com/Mustard2/MustardSimplify

bl_info = {
    "name": "Mustard Simplify",
    "description": "A set of tools to simplify scenes for better viewport performance",
    "author": "Mustard",
    "version": (0, 0, 2),
    "blender": (3, 6, 0),
    "warning": "",
    "category": "3D View",
}

import bpy
import addon_utils
import sys
import os
import re
import time
import math
from bpy.props import *
from mathutils import Vector, Color
import webbrowser

# ------------------------------------------------------------------------
#    Main Settings
# ------------------------------------------------------------------------

# Class with all the settings variables
class MustardSimplify_Settings(bpy.types.PropertyGroup):
    
    # Main Settings definitions
    # UI definitions
    ms_advanced: bpy.props.BoolProperty(name="Advanced Options",
                                        description="Unlock advanced options",
                                        default=False)
    ms_debug: bpy.props.BoolProperty(name="Debug mode",
                                        description="Unlock debug mode.\nThis will generate more messaged in the console.\nEnable it only if you encounter problems, as it might degrade general Blender performance",
                                        default=False)
    
    
    # Settings to simplify
    modifiers: bpy.props.BoolProperty(name="Modifiers",
                                        description="Disable modifiers",
                                        default=True)
    shape_keys: bpy.props.BoolProperty(name="Shape Keys",
                                        description="Mute un-used shape keys (value different from 0)",
                                        default=True)
    physics: bpy.props.BoolProperty(name="Physics",
                                        description="Disable Physics",
                                        default=True)
    normals_auto_smooth: bpy.props.BoolProperty(name="Normals Auto Smooth",
                                        description="Disable Normals Auto Smooth",
                                        default=True)
    
    # UI Settings
    collapse_options: bpy.props.BoolProperty(name="Collapse",
                                        default=True)
    
    # Internal Settings
    simplify_fastnormals_status: bpy.props.BoolProperty(default=False)
    simplify_status: bpy.props.BoolProperty(default=False)
            
bpy.utils.register_class(MustardSimplify_Settings)
bpy.types.Scene.MustardSimplify_Settings = bpy.props.PointerProperty(type=MustardSimplify_Settings)

# ------------------------------------------------------------------------
#    Status Properties
# ------------------------------------------------------------------------

# Modifier status
class MustardSimplify_ModifierStatus(bpy.types.PropertyGroup):
    status: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty(default="")
bpy.utils.register_class(MustardSimplify_ModifierStatus)

# Shape Keys
class MustardSimplify_ShapeKeysStatus(bpy.types.PropertyGroup):
    status: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty(default="")
bpy.utils.register_class(MustardSimplify_ShapeKeysStatus)

# Class with all the settings variables
class MustardSimplify_ObjectStatus(bpy.types.PropertyGroup):
    
    # Normals Auto Smooth
    normals_auto_smooth: bpy.props.BoolProperty(default=True)
    # Modifiers status
    modifiers: bpy.props.CollectionProperty(type=MustardSimplify_ModifierStatus)
    # Shape Keys status
    shape_keys: bpy.props.CollectionProperty(type=MustardSimplify_ShapeKeysStatus)
            
bpy.utils.register_class(MustardSimplify_ObjectStatus)
bpy.types.Object.MustardSimplify_Status = bpy.props.PointerProperty(type=MustardSimplify_ObjectStatus)

# Class with all the settings variables
class MustardSimplify_SceneStatus(bpy.types.PropertyGroup):
    rigidbody_world: bpy.props.BoolProperty(default=False)
            
bpy.utils.register_class(MustardSimplify_SceneStatus)
bpy.types.Scene.MustardSimplify_Status = bpy.props.PointerProperty(type=MustardSimplify_SceneStatus)

# ------------------------------------------------------------------------
#    Normal Maps Optimizer (thanks to theoldben)
# ------------------------------------------------------------------------
# Original implementation: https://github.com/theoldben/BlenderNormalGroups

class MUSTARDSIMPLIFY_OT_FastNormals(bpy.types.Operator):
    bl_description = "Switch normal map nodes to a faster custom node"
    bl_idname = 'mustard_simplify.fast_normals'
    bl_label = "Eevee Fast Normals"
    bl_options = {'UNDO'}
    
    custom: bpy.props.BoolProperty(
        name="To Custom",
        description="Set all normals to custom group, or revert back to normal",
        default=True,
    )
    
    @classmethod
    def poll(self, context):
        return (bpy.data.materials or bpy.data.node_groups)

    def execute(self, context):
        def mirror(new, old):
            """Copy attributes of the old node to the new node"""
            new.parent = old.parent
            new.label = old.label
            new.mute = old.mute
            new.hide = old.hide
            new.select = old.select
            new.location = old.location

            # inputs
            for (name, point) in old.inputs.items():
                input = new.inputs.get(name)
                if input:
                    input.default_value = point.default_value
                    for link in point.links:
                        new.id_data.links.new(link.from_socket, input)

            # outputs
            for (name, point) in old.outputs.items():
                output = new.outputs.get(name)
                if output:
                    output.default_value = point.default_value
                    for link in point.links:
                        new.id_data.links.new(output, link.to_socket)

        def get_custom():
            name = 'Normal Map Optimized'
            group = bpy.data.node_groups.get(name)

            if not group and self.custom:
                group = default_custom_nodes()

            return group

        def set_custom(nodes):
            group = get_custom()
            if not group:
                return

            for node in nodes:
                new = None
                if self.custom:
                    if isinstance(node, bpy.types.ShaderNodeNormalMap):
                        new = nodes.new(type='ShaderNodeGroup')
                        new.node_tree = group
                else:
                    if isinstance(node, bpy.types.ShaderNodeGroup):
                        if node.node_tree == group:
                            new = nodes.new(type='ShaderNodeNormalMap')

                if new:
                    name = node.name
                    mirror(new, node)
                    nodes.remove(node)
                    new.name = name

        for mat in bpy.data.materials:
            set_custom(getattr(mat.node_tree, 'nodes', []))
        for group in bpy.data.node_groups:
            set_custom(group.nodes)

        if (not self.custom) and get_custom():
            bpy.data.node_groups.remove(get_custom())
        
        settings = bpy.context.scene.MustardSimplify_Settings
        settings.simplify_fastnormals_status = self.custom
        self.custom = not self.custom
        
        return {'FINISHED'}

def default_custom_nodes():
    use_new_nodes = (bpy.app.version >= (2, 81))

    group = bpy.data.node_groups.new('Normal Map Optimized', 'ShaderNodeTree')

    nodes = group.nodes
    links = group.links

    # Input
    input = group.inputs.new('NodeSocketFloat', 'Strength')
    input.default_value = 1.0
    input.min_value = 0.0
    input.max_value = 1.0
    input = group.inputs.new('NodeSocketColor', 'Color')
    input.default_value = ((0.5, 0.5, 1.0, 1.0))

    # Output
    group.outputs.new('NodeSocketVector', 'Normal')

    # Add Nodes
    frame = nodes.new('NodeFrame')
    frame.name = 'Matrix * Normal Map'
    frame.label = 'Matrix * Normal Map'
    frame.location = Vector((540.0, -80.0))
    frame.hide = False
    frame.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node = nodes.new('ShaderNodeVectorMath')
    node.name = 'Vector Math'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-60.0, 20.0))
    node.operation = 'DOT_PRODUCT'
    node.inputs[0].default_value = (0.5, 0.5, 0.5)  # Vector
    node.inputs[1].default_value = (0.5, 0.5, 0.5)  # Vector
    if use_new_nodes:
        node.inputs[2].default_value = (1.0, 1.0, 1.0)  # Scale
    node = nodes.new('ShaderNodeVectorMath')
    node.name = 'Vector Math.001'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-60.0, -20.0))
    node.operation = 'DOT_PRODUCT'
    node.inputs[0].default_value = (0.5, 0.5, 0.5)  # Vector
    node.inputs[1].default_value = (0.5, 0.5, 0.5)  # Vector
    if use_new_nodes:
        node.inputs[2].default_value = (1.0, 1.0, 1.0)  # Scale
    node = nodes.new('ShaderNodeVectorMath')
    node.name = 'Vector Math.002'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-60.0, -60.0))
    node.inputs[0].default_value = (0.5, 0.5, 0.5)  # Vector
    node.inputs[1].default_value = (0.5, 0.5, 0.5)  # Vector
    if use_new_nodes:
        node.inputs[2].default_value = (1.0, 1.0, 1.0)  # Scale
    node.operation = 'DOT_PRODUCT'
    node = nodes.new('ShaderNodeCombineXYZ')
    node.name = 'Combine XYZ'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((100.0, -20.0))
    node.inputs[0].default_value = 0.0  # X
    node.inputs[1].default_value = 0.0  # Y
    node.inputs[2].default_value = 0.0  # Z

    frame = nodes.new('NodeFrame')
    frame.name = 'Generate TBN from Bump Node'
    frame.label = 'Generate TBN from Bump Node'
    frame.location = Vector((-192.01412963867188, -77.50459289550781))
    frame.hide = False
    frame.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node = nodes.new('ShaderNodeUVMap')
    node.name = 'UV Map'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-247.98587036132812, -2.4954071044921875))
    node = nodes.new('ShaderNodeSeparateXYZ')
    node.name = 'UV Gradients'
    node.label = 'UV Gradients'
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-87.98587036132812, -2.4954071044921875))
    node.inputs[0].default_value = (0.0, 0.0, 0.0)  # Vector
    # node.outputs.remove((node.outputs['Z']))
    node = nodes.new('ShaderNodeNewGeometry')
    node.name = 'Normal'
    node.label = 'Normal'
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((72.01412963867188, -62.49540710449219))
    # for out in node.outputs:
    #     if out.name not in ['Normal']:
    #         node.outputs.remove(out)
    node = nodes.new('ShaderNodeBump')
    node.name = 'Bi-Tangent'
    node.label = 'Bi-Tangent'
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((72.01412963867188, -22.495407104492188))
    node.invert = True
    node.inputs[0].default_value = 1.0  # Strength
    node.inputs[1].default_value = 1000.0  # Distance
    node.inputs[2].default_value = 1.0  # Height
    #if use_new_nodes:
        #node.inputs[3].default_value = 1.0  # Height_dx
        #node.inputs[4].default_value = 1.0  # Height_dy
        #node.inputs[5].default_value = (0.0, 0.0, 0.0)  # Normal
    #else:
        #node.inputs[3].default_value = (0.0, 0.0, 0.0)  # Normal
    # for inp in node.inputs:
    #     if inp.name not in ['Height']:
    #         node.inputs.remove(inp)
    node = nodes.new('ShaderNodeBump')
    node.name = 'Tangent'
    node.label = 'Tangent'
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((72.01412963867188, 17.504592895507812))
    node.invert = True
    # for inp in node.inputs:
    #     if inp.name not in ['Height']:
    #         node.inputs.remove(inp)

    frame = nodes.new('NodeFrame')
    frame.name = 'Node'
    frame.label = 'Normal Map Processing'
    frame.location = Vector((180.0, -260.0))
    frame.hide = False
    frame.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node = nodes.new('NodeGroupInput')
    node.name = 'Group Input'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-400.0, 20.0))
    node = nodes.new('ShaderNodeMixRGB')
    node.name = 'Influence'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.location = Vector((-240.0, 20.0))
    node.inputs[1].default_value = (0.5, 0.5, 1.0, 1.0)  # Color1
    node = nodes.new('ShaderNodeVectorMath')
    node.name = 'Vector Math.003'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-80.0, 20.0))
    node.operation = 'SUBTRACT'
    node.inputs[0].default_value = (0.5, 0.5, 0.5)  # Vector
    node.inputs[1].default_value = (0.5, 0.5, 0.5)  # Vector
    if use_new_nodes:
        node.inputs[2].default_value = (1.0, 1.0, 1.0)  # Scale
    # node.inputs.remove(node.inputs[1])
    node = nodes.new('ShaderNodeVectorMath')
    node.name = 'Vector Math.004'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((80.0, 20.0))
    node.inputs[0].default_value = (0.5, 0.5, 0.5)  # Vector
    node.inputs[1].default_value = (0.5, 0.5, 0.5)  # Vector
    if use_new_nodes:
        node.inputs[2].default_value = (1.0, 1.0, 1.0)  # Scale

    frame = nodes.new('NodeFrame')
    frame.name = 'Transpose Matrix'
    frame.label = 'Transpose Matrix'
    frame.location = Vector((180.0, -80.0))
    frame.hide = False
    frame.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node = nodes.new('ShaderNodeCombineXYZ')
    node.name = 'Combine XYZ.001'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((80.0, 20.0))
    node.inputs[0].default_value = 0.0  # X
    node.inputs[1].default_value = 0.0  # Y
    node.inputs[2].default_value = 0.0  # Z
    node = nodes.new('ShaderNodeCombineXYZ')
    node.name = 'Combine XYZ.002'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((80.0, -20.0))
    node.inputs[0].default_value = 0.0  # X
    node.inputs[1].default_value = 0.0  # Y
    node.inputs[2].default_value = 0.0  # Z
    node = nodes.new('ShaderNodeCombineXYZ')
    node.name = 'Combine XYZ.003'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((80.0, -60.0))
    node.inputs[0].default_value = 0.0  # X
    node.inputs[1].default_value = 0.0  # Y
    node.inputs[2].default_value = 0.0  # Z
    node = nodes.new('ShaderNodeSeparateXYZ')
    node.name = 'Separate XYZ.001'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-80.0, 20.0))
    node.inputs[0].default_value = (0.0, 0.0, 0.0)  # Vector
    node = nodes.new('ShaderNodeSeparateXYZ')
    node.name = 'Separate XYZ.002'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-80.0, -20.0))
    node.inputs[0].default_value = (0.0, 0.0, 0.0)  # Vector
    node = nodes.new('ShaderNodeSeparateXYZ')
    node.name = 'Separate XYZ.003'
    node.label = ''
    node.parent = frame
    node.hide = True
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.location = Vector((-80.0, -60.0))
    node.inputs[0].default_value = (0.0, 0.0, 0.0)  # Vector

    node = nodes.new('NodeGroupOutput')
    node.name = 'Group Output'
    node.label = ''
    node.location = Vector((840.0, -80.0))
    node.hide = False
    node.color = Color((0.6079999804496765, 0.6079999804496765, 0.6079999804496765))
    node.inputs[0].default_value = (0.0, 0.0, 0.0)  # Normal

    # Connect the nodes
    links.new(nodes['Group Input'].outputs['Strength'], nodes['Influence'].inputs[0])
    links.new(nodes['Group Input'].outputs['Color'], nodes['Influence'].inputs[2])
    links.new(nodes['Influence'].outputs['Color'], nodes['Vector Math.003'].inputs[0])
    links.new(nodes['UV Gradients'].outputs['X'], nodes['Tangent'].inputs['Height'])
    links.new(nodes['UV Gradients'].outputs['Y'], nodes['Bi-Tangent'].inputs['Height'])
    links.new(nodes['UV Map'].outputs['UV'], nodes['UV Gradients'].inputs['Vector'])
    links.new(nodes['Tangent'].outputs['Normal'], nodes['Separate XYZ.001'].inputs[0])
    links.new(nodes['Bi-Tangent'].outputs['Normal'], nodes['Separate XYZ.002'].inputs[0])
    links.new(nodes['Normal'].outputs['Normal'], nodes['Separate XYZ.003'].inputs[0])
    links.new(nodes['Vector Math.004'].outputs['Vector'], nodes['Vector Math'].inputs[1])
    links.new(nodes['Combine XYZ.001'].outputs['Vector'], nodes['Vector Math'].inputs[0])
    links.new(nodes['Vector Math.004'].outputs['Vector'], nodes['Vector Math.001'].inputs[1])
    links.new(nodes['Combine XYZ.002'].outputs['Vector'], nodes['Vector Math.001'].inputs[0])
    links.new(nodes['Vector Math.004'].outputs['Vector'], nodes['Vector Math.002'].inputs[1])
    links.new(nodes['Combine XYZ.003'].outputs['Vector'], nodes['Vector Math.002'].inputs[0])
    links.new(nodes['Vector Math.003'].outputs['Vector'], nodes['Vector Math.004'].inputs[0])
    links.new(nodes['Vector Math.003'].outputs['Vector'], nodes['Vector Math.004'].inputs[1])
    links.new(nodes['Vector Math'].outputs['Value'], nodes['Combine XYZ'].inputs['X'])
    links.new(nodes['Vector Math.001'].outputs['Value'], nodes['Combine XYZ'].inputs['Y'])
    links.new(nodes['Vector Math.002'].outputs['Value'], nodes['Combine XYZ'].inputs['Z'])
    links.new(nodes['Separate XYZ.001'].outputs['X'], nodes['Combine XYZ.001'].inputs['X'])
    links.new(nodes['Separate XYZ.002'].outputs['X'], nodes['Combine XYZ.001'].inputs['Y'])
    links.new(nodes['Separate XYZ.003'].outputs['X'], nodes['Combine XYZ.001'].inputs['Z'])
    links.new(nodes['Separate XYZ.001'].outputs['Y'], nodes['Combine XYZ.002'].inputs['X'])
    links.new(nodes['Separate XYZ.002'].outputs['Y'], nodes['Combine XYZ.002'].inputs['Y'])
    links.new(nodes['Separate XYZ.003'].outputs['Y'], nodes['Combine XYZ.002'].inputs['Z'])
    links.new(nodes['Separate XYZ.001'].outputs['Z'], nodes['Combine XYZ.003'].inputs['X'])
    links.new(nodes['Separate XYZ.002'].outputs['Z'], nodes['Combine XYZ.003'].inputs['Y'])
    links.new(nodes['Separate XYZ.003'].outputs['Z'], nodes['Combine XYZ.003'].inputs['Z'])
    links.new(nodes['Combine XYZ'].outputs['Vector'], nodes['Group Output'].inputs['Normal'])

    return group

# ------------------------------------------------------------------------
#    Simplify Scene
# ------------------------------------------------------------------------

class MUSTARDSIMPLIFY_OT_SimplifyScene(bpy.types.Operator):
    """Simplify the scene to increase the viewport performance"""
    bl_idname = "mustard_simplify.scene"
    bl_label = "Simplify Scene"
    bl_options = {'UNDO'}
    
    enable_simplify: bpy.props.BoolProperty(name="Simplify",
                                default=True)
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        def add_prop_status (collection, item):
            for el in collection:
                if el.name == item[0] and el.status == item[1]:
                    return
            add_item = collection.add()
            add_item.name = item[0]
            add_item.status = item[1]
            return
        
        def find_prop_status (collection, mod):
            for el in collection:
                if el.name == mod.name:
                    return el.name, el.status
            return "", None
        
        settings = bpy.context.scene.MustardSimplify_Settings
        
        # OBJECTS
        objects = bpy.data.objects
        
        for obj in objects:
            
            # Modifiers
            if settings.modifiers:
                
                modifiers_ignore = ["ARMATURE"]
                modifiers = [x for x in obj.modifiers if not x.type in modifiers_ignore]
                
                if self.enable_simplify:
                    obj.MustardSimplify_Status.modifiers.clear()
                    for mod in modifiers:
                        add_prop_status(obj.MustardSimplify_Status.modifiers, [mod.name, mod.show_viewport])
                        mod.show_viewport = False
                else:
                    for mod in modifiers:
                        name, status = find_prop_status(obj.MustardSimplify_Status.modifiers, mod)
                        if name != "":
                            mod.show_viewport = status
            
            # Shape Keys
            if settings.modifiers:
                if self.enable_simplify:
                    obj.MustardSimplify_Status.shape_keys.clear()
                    for sk in obj.data.shape_keys.key_blocks:
                        add_prop_status(obj.MustardSimplify_Status.shape_keys, [sk.name, sk.mute])
                        sk.mute = True if sk.value < 1e-5 else False
                else:
                    for sk in obj.data.shape_keys.key_blocks:
                        name, status = find_prop_status(obj.MustardSimplify_Status.shape_keys, sk)
                        if name != "":
                            sk.mute = status
            
            # Normals Auto Smooth
            if settings.normals_auto_smooth:
                if self.enable_simplify:
                    obj.MustardSimplify_Status.normals_auto_smooth = obj.data.use_auto_smooth
                    obj.data.use_auto_smooth = False
                else:
                    obj.data.use_auto_smooth = obj.MustardSimplify_Status.normals_auto_smooth
        
        # SCENE
        if settings.physics:
            
            # Rigid Body World
            if context.scene.rigidbody_world:
                if self.enable_simplify:
                    context.scene.MustardSimplify_Status.rigidbody_world = context.scene.rigidbody_world.enabled
                    context.scene.rigidbody_world.enabled = False
                else:
                    context.scene.rigidbody_world.enabled = context.scene.MustardSimplify_Status.rigidbody_world
        
        if self.enable_simplify:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Enabled.')
        else:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Disabled.')
        
        settings.simplify_status = self.enable_simplify
        self.enable_simplify = not self.enable_simplify
        
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    UI
# ------------------------------------------------------------------------

class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mustard Simplify"

class MUSTARDSIMPLIFY_PT_Options(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_Options"
    bl_label = "Simplify"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        
        layout = self.layout
        settings = context.scene.MustardSimplify_Settings
        
        layout.operator(MUSTARDSIMPLIFY_OT_SimplifyScene.bl_idname, text = "Simplify Scene" if not settings.simplify_status else "Un-Simplify Scene")
        if settings.simplify_fastnormals_status and context.scene.render.engine == "CYCLES":
            layout.operator(MUSTARDSIMPLIFY_OT_FastNormals.bl_idname, text = "Enable Eevee Fast Normals" if not settings.simplify_fastnormals_status else "Disable Eevee Fast Normals", icon = "ERROR")
        else:
            col = layout.column()
            col.enabled = not context.scene.render.engine == "CYCLES"
            col.operator(MUSTARDSIMPLIFY_OT_FastNormals.bl_idname, text = "Enable Eevee Fast Normals" if not settings.simplify_fastnormals_status else "Disable Eevee Fast Normals")
        
        box=layout.box()
        row = box.row()
        row.prop(settings, 'collapse_options', text="", icon="RIGHTARROW" if settings.collapse_options else "DOWNARROW_HLT", emboss=False)
        row.label(text="Options")
        if not settings.collapse_options:
            col = box.column()
            col.enabled = not settings.simplify_status
            col.prop(settings,"modifiers")
            col.prop(settings,"shape_keys")
            col.prop(settings,"physics")
            col.prop(settings,"normals_auto_smooth")

class MUSTARDSIMPLIFY_PT_Settings(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDSIMPLIFY_PT_Settings"
    bl_label = "Settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.MustardSimplify_Settings
        
        box=layout.box()
        box.label(text="Main Settings", icon="SETTINGS")
        col = box.column()
        col.prop(settings,"ms_advanced")
        col.prop(settings,"ms_debug")

# ------------------------------------------------------------------------
#    Register
# ------------------------------------------------------------------------

classes = (
    MUSTARDSIMPLIFY_OT_FastNormals,
    MUSTARDSIMPLIFY_OT_SimplifyScene,
    MUSTARDSIMPLIFY_PT_Options,
    MUSTARDSIMPLIFY_PT_Settings,
)

def register():
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()