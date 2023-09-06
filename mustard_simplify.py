# Mustard Simplify
# https://github.com/Mustard2/MustardSimplify

bl_info = {
    "name": "Mustard Simplify",
    "description": "A set of tools to simplify scenes for better viewport performance",
    "author": "Mustard",
    "version": (0, 0, 8),
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
    advanced: bpy.props.BoolProperty(name="Advanced Options",
                                        description="Unlock advanced options",
                                        default=False)
    debug: bpy.props.BoolProperty(name="Debug mode",
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
    drivers: bpy.props.BoolProperty(name="Drivers",
                                        description="Disable Drivers",
                                        default=True)
    normals_auto_smooth: bpy.props.BoolProperty(name="Normals Auto Smooth",
                                        description="Disable Normals Auto Smooth",
                                        default=True)
    
    # UI Settings
    collapse_options: bpy.props.BoolProperty(name="Collapse",
                                        default=True)
    collapse_exceptions: bpy.props.BoolProperty(name="Collapse",
                                        default=True)
    # Poll function for the selection of mesh only in pointer properties
    def poll_exception(self, object):
        
        exceptions = bpy.context.scene.MustardSimplify_Exceptions.exceptions
        exceptions = [x.exception for x in exceptions]
        
        return not object in exceptions
    
    exception_select: bpy.props.PointerProperty(type=bpy.types.Object,
                                        poll=poll_exception,
                                        name="",
                                        description="")
    
    # Internal Settings
    simplify_fastnormals_status: bpy.props.BoolProperty(default=False)
    simplify_status: bpy.props.BoolProperty(default=False)
    
    # Modifiers to not simplify by default
    modifiers_ignore = ["ARMATURE", "HOOK"]
            
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

# Class to store the scene status
class MustardSimplify_SceneStatus(bpy.types.PropertyGroup):
    rigidbody_world: bpy.props.BoolProperty(default=False)
            
bpy.utils.register_class(MustardSimplify_SceneStatus)
bpy.types.Scene.MustardSimplify_Status = bpy.props.PointerProperty(type=MustardSimplify_SceneStatus)

# Classes to manage exceptions
class MustardSimplify_Exception(bpy.types.PropertyGroup):
    exception: bpy.props.PointerProperty(type=bpy.types.Object)
bpy.utils.register_class(MustardSimplify_Exception)

class MustardSimplify_Exceptions(bpy.types.PropertyGroup):
    exceptions: bpy.props.CollectionProperty(type=MustardSimplify_Exception)
            
bpy.utils.register_class(MustardSimplify_Exceptions)
bpy.types.Scene.MustardSimplify_Exceptions = bpy.props.PointerProperty(type=MustardSimplify_Exceptions)

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
        
        scene = context.scene
        settings = scene.MustardSimplify_Settings
        
        if not settings.simplify_status:
            return settings.modifiers or settings.shape_keys or settings.physics or settings.drivers or settings.normals_auto_smooth
        else:
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
        
        scene = context.scene
        settings = scene.MustardSimplify_Settings
        
        # OBJECTS
        
        # Create list of exception Objects
        except_objects = []
        exceptions = scene.MustardSimplify_Exceptions.exceptions
        for excpt in exceptions:
            except_objects.append(excpt.exception)
        
        objects = [x for x in bpy.data.objects if not x in except_objects]
        
        # Create list of modifiers to simplify
        if settings.modifiers:
            
            chosen_mods = scene.MustardSimplify_SetModifiers.modifiers
            
            # If the user hasn't used the Modifiers menu, use the default settings
            if not len(chosen_mods):
                modifiers_ignore = settings.modifiers_ignore
            else:
                modifiers_ignore = [x.name for x in chosen_mods if not x.simplify]
        
        if settings.debug:
            print("\n ----------- MUSTARD SIMPLIFY LOG -----------")
        
        for obj in [x for x in objects if not x in except_objects]:
            
            if settings.debug:
                print("\n ----------- Object: " + obj.name + " -----------")
            
            # Modifiers
            if settings.modifiers:
                
                modifiers = [x for x in obj.modifiers if not x.type in modifiers_ignore]
                
                if self.enable_simplify:
                    obj.MustardSimplify_Status.modifiers.clear()
                    for mod in modifiers:
                        status = mod.show_viewport
                        add_prop_status(obj.MustardSimplify_Status.modifiers, [mod.name, status])
                        mod.show_viewport = False
                        if settings.debug:
                            print("Modifier " + mod.name + " disabled (previous viewport_hide: " + str(status) + ").")
                else:
                    for mod in modifiers:
                        name, status = find_prop_status(obj.MustardSimplify_Status.modifiers, mod)
                        if name != "":
                            mod.show_viewport = status
                            if settings.debug:
                                print("Modifier " + mod.name + " reverted to viewport_hide: " + str(status) + ".")
            
            # Shape Keys
            if settings.shape_keys and obj.type == "MESH":
                
                if self.enable_simplify:
                    obj.MustardSimplify_Status.shape_keys.clear()
                    if obj.data.shape_keys != None:
                        for sk in obj.data.shape_keys.key_blocks:
                            status = sk.mute
                            add_prop_status(obj.MustardSimplify_Status.shape_keys, [sk.name, status])
                            sk.mute = True if sk.value < 1e-5 else False
                            if settings.debug:
                                print("Shape key " + sk.name + " disabled (previous mute: " + str(status) + ").")
                else:
                    if obj.data.shape_keys != None:
                        for sk in obj.data.shape_keys.key_blocks:
                            name, status = find_prop_status(obj.MustardSimplify_Status.shape_keys, sk)
                            if name != "":
                                sk.mute = status
                                if settings.debug:
                                    print("Shape key " + sk.name + " reverted to mute: " + str(status) + ".")
            
            # Normals Auto Smooth
            if settings.normals_auto_smooth and obj.type == "MESH":
                
                if self.enable_simplify:
                    status = obj.data.use_auto_smooth
                    obj.MustardSimplify_Status.normals_auto_smooth = obj.data.use_auto_smooth
                    obj.data.use_auto_smooth = False
                    if settings.debug:
                        print("Normals Auto Smooth disabled (previous status: " + str(status) + ").")
                else:
                    obj.data.use_auto_smooth = obj.MustardSimplify_Status.normals_auto_smooth
                    if settings.debug:
                        print("Normals Auto Smooth reverted to status: " + str(obj.data.use_auto_smooth) + ".")
        
        # SCENE
        if settings.physics:
            
            # Rigid Body World
            if context.scene.rigidbody_world:
                
                if settings.debug:
                    print("\n ----------- Scene: " + scene.name + " -----------")
                
                if self.enable_simplify:
                    status = scene.rigidbody_world.enabled
                    scene.MustardSimplify_Status.rigidbody_world = status
                    scene.rigidbody_world.enabled = False
                    if settings.debug:
                        print("Rigid Body World disabled (previous status: " + str(status) + ").")
                else:
                    scene.rigidbody_world.enabled = scene.MustardSimplify_Status.rigidbody_world
                    if settings.debug:
                        print("Rigid Body World disabled reverted to status: " + str(scene.rigidbody_world.enabled) + ").")
        
        # DRIVERS
        if settings.drivers:
            collections = ["scenes","objects","meshes","materials","textures","speakers",
                           "worlds","curves","armatures","particles","lattices","shape_keys","lights","cameras"]
            num_drivers = 0
            
            for col in collections:
                collection = eval("bpy.data.%s"%col)
                if col == "objects":
                    collection = objects
                for ob in collection:
                    if ob.animation_data is not None:
                        for driver in ob.animation_data.drivers:
                            dp = driver.data_path
                            pp = dp
                            if dp.find("[") != 0:pp = ".%s"%dp
                            resolved = False
                            try:
                                dob = ob.path_resolve(dp)
                                resolved = True
                            except:
                                dob = None
                                
                            if not resolved:
                                try:
                                    dob = eval('bpy.data.%s["%s"]%s' % (col,ob.name,pp))
                                    resolved = True
                                except:
                                    dob = None
                                
                            idx = driver.array_index
                            if dob is not None and (isinstance(dob,Vector) or isinstance(dob,Color)):
                                pp = "%s[%d]"%(pp,idx)
                            driver.mute = self.enable_simplify
                            num_drivers = num_drivers + 1
            
            if settings.debug and self.enable_simplify:
                print("\n ----------- Drivers disabled: " + str(num_drivers) + " -----------")
            if settings.debug and not self.enable_simplify:
                print("\n ----------- Drivers reverted: " + str(num_drivers) + " -----------")
        
        if settings.debug:
            print("\n")
        
        settings.simplify_status = self.enable_simplify
        
        if self.enable_simplify:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Enabled.')
        else:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Disabled.')
        
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Modifiers Select
# ------------------------------------------------------------------------

# Classes to manage exceptions
class MustardSimplify_SetModifier(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="")
    disp_name: bpy.props.StringProperty(default="")
    icon: bpy.props.StringProperty(default="")
    simplify: bpy.props.BoolProperty(default=True)
bpy.utils.register_class(MustardSimplify_SetModifier)

class MustardSimplify_SetModifiers(bpy.types.PropertyGroup):
    modifiers: bpy.props.CollectionProperty(type=MustardSimplify_SetModifier)
bpy.utils.register_class(MustardSimplify_SetModifiers)
bpy.types.Scene.MustardSimplify_SetModifiers = bpy.props.PointerProperty(type=MustardSimplify_SetModifiers)

class MUSTARDSIMPLIFY_OT_MenuModifiersSelect(bpy.types.Operator):
    """Select the modifiers affected by the simplification process"""
    bl_idname = "mustard_simplify.menu_modifiers_select"
    bl_label = "Select Modifiers to Simplify"
    
    modifiers: bpy.props.PointerProperty(type=MustardSimplify_SetModifiers)
    
    @classmethod
    def poll(cls, context):
        # Enable operator only when the scene is not simplified
        settings = bpy.context.scene.MustardSimplify_Settings
        return not settings.simplify_status
 
    def execute(self, context):
        
        return{'FINISHED'}
    
    def invoke(self, context, event):
        
        def add_modifier (collection, name, disp_name, icon, simplify):
            for el in collection:
                if el.name == name:
                    return False
            add_item = collection.add()
            add_item.name = name
            add_item.disp_name = disp_name
            add_item.icon = icon
            add_item.simplify = simplify
            return True
        
        scene = bpy.context.scene
        settings = scene.MustardSimplify_Settings
        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        
        # Extract type of modifiers
        rna = bpy.ops.object.modifier_add.get_rna_type()
        mods_list = rna.bl_rna.properties['type'].enum_items.keys()
        
        # Make the list
        # This is done at run-time, so it should be version agnostic
        if len(mods_list) != len(modifiers):
            
            modifiers.clear()
        
            for m in mods_list:
                
                # Change the displayed name
                disp_name = m.replace("_", " ")
                disp_name = disp_name.title()
                
                icon = "MOD_"+m
                simplify = True
                
                # Manage single exceptions
                if m in ["MESH_CACHE", "MESH_SEQUENCE_CACHE", "LAPLACIANDEFORM", "MESH_DEFORM", "SURFACE_DEFORM", "SURFACE"]:
                    icon = "MOD_MESHDEFORM"
                if m in ["LAPLACIANDEFORM"]:
                    icon = "MOD_MESHDEFORM"
                    disp_name = "Laplacian Deform"
                elif m in ["NORMAL_EDIT",  "WEIGHTED_NORMAL"]:
                    icon = "MOD_NORMALEDIT"
                elif m in ["UV_PROJECT",  "UV_WARP"]:
                    icon = "MOD_UVPROJECT"
                elif m in ['VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX', 'VERTEX_WEIGHT_PROXIMITY']:
                    icon = "MOD_VERTEX_WEIGHT"
                elif m in ['DECIMATE']:
                    icon = "MOD_DECIM"
                elif m in ['EDGE_SPLIT']:
                    icon = "MOD_EDGESPLIT"
                elif m in ['NODES']:
                    icon = "GEOMETRY_NODES"
                elif m in ['MULTIRES']:
                    icon = "MOD_MULTIRES"
                elif m in ["MESH_TO_VOLUME", "VOLUME_TO_MESH", "VOLUME_DISPLACE"]:
                    icon = "VOLUME_DATA"
                elif m in ["WELD"]:
                    icon = "AUTOMERGE_OFF"
                elif m in ['SIMPLE_DEFORM']:
                    icon = "MOD_SIMPLEDEFORM"
                elif m in ['SMOOTH', 'CORRECTIVE_SMOOTH']:
                    icon = "MOD_SMOOTH"
                if m in ["LAPLACIANSMOOTH"]:
                    icon = "MOD_SMOOTH"
                    disp_name = "Laplacian Smooth"
                elif m in ["HOOK"]:
                    icon = m
                elif m in ["COLLISION"]:
                    icon = "MOD_PHYSICS"
                elif m in ["DYNAMIC_PAINT"]:
                    icon = "MOD_DYNAMICPAINT"
                elif m in ["PARTICLE_SYSTEM"]:
                    icon = "MOD_PARTICLES"
                elif m in ["SOFT_BODY"]:
                    icon = "MOD_SOFT"
                
                if m in settings.modifiers_ignore:
                    simplify = False
                
                add_modifier(modifiers, m, disp_name, icon, simplify)
                
                if settings.debug:
                    print("Mustard Simplify - Modifiers List generated")
        
        return context.window_manager.invoke_props_dialog(self, width = 800)
            
    def draw(self, context):
        
        scene = bpy.context.scene
        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        settings = bpy.context.scene.MustardSimplify_Settings
        
        layout = self.layout
        box = layout.box()
        
        row = box.row()
        col = row.column()
        idx = 0
        
        for m in modifiers:
            if m.name in ["ARRAY", "ARMATURE", "CLOTH"]:
                col = row.column()
            row2 = col.row()
            row2.prop(m, 'simplify', text="")
            # Avoid missing icon error
            try:
                row2.label(text=m.disp_name, icon=m.icon)
            except:
                row2.label(text=m.disp_name, icon="BLANK1")
        
# ------------------------------------------------------------------------
#    Exceptions
# ------------------------------------------------------------------------

class MUSTARDSIMPLIFY_OT_AddException(bpy.types.Operator):
    """Add Object to the exceptions list"""
    bl_idname = "mustard_simplify.add_exception"
    bl_label = "Add Object"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Enable operator only when the scene is not simplified
        settings = bpy.context.scene.MustardSimplify_Settings
        return not settings.simplify_status

    def execute(self, context):
        
        def add_exception (collection, obj):
            for el in collection:
                if el.exception == obj:
                    return False
            add_item = collection.add()
            add_item.exception = obj
            return True
        
        def find_exception (collection, mod):
            for el in collection:
                if el.exception == obj:
                    return el.exception
            return None
        
        settings = bpy.context.scene.MustardSimplify_Settings
        scene = context.scene
        
        res = add_exception(scene.MustardSimplify_Exceptions.exceptions, settings.exception_select)
        if not res:
            self.report({'ERROR'}, 'Mustard Simplify - Object already added to exceptions.')
        
        return {'FINISHED'}

class MUSTARDSIMPLIFY_OT_RemoveException(bpy.types.Operator):
    """Remove Object to the exceptions list"""
    bl_idname = "mustard_simplify.remove_exception"
    bl_label = "Remove Object"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        scene = context.scene
        index = scene.mustardsimplify_exception_uilist_index
        uilist = scene.MustardSimplify_Exceptions.exceptions
        
        uilist.remove(index)
        index = min(max(0, index - 1), len(uilist) - 1)
        scene.mustardsimplify_exception_uilist_index = index
        
        return{'FINISHED'}

class MUSTARDSIMPLIFY_UL_Exceptions_UIList(bpy.types.UIList):
    """UIList for exceptions."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        
        scene = context.scene
        settings = scene.MustardSimplify_Settings
        
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item.exception, 'name', text ="", icon ="OUTLINER_OB_" + item.exception.type, emboss=False, translate=False)
                
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item.exception, 'name', text ="", icon ="OUTLINER_OB_" + item.exception.type, emboss=False, translate=False)

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
        
        scene = context.scene
        layout = self.layout
        settings = scene.MustardSimplify_Settings
        
        if settings.simplify_status:
            op = layout.operator(MUSTARDSIMPLIFY_OT_SimplifyScene.bl_idname, text = "Un-Simplify Scene", icon="MOD_SIMPLIFY")
        else:
            op = layout.operator(MUSTARDSIMPLIFY_OT_SimplifyScene.bl_idname, text = "Simplify Scene", icon="MOD_SIMPLIFY")
        op.enable_simplify = not settings.simplify_status
        if settings.simplify_fastnormals_status and scene.render.engine == "CYCLES":
            layout.operator(MUSTARDSIMPLIFY_OT_FastNormals.bl_idname, text = "Enable Eevee Fast Normals" if not settings.simplify_fastnormals_status else "Disable Eevee Fast Normals", icon = "ERROR")
        else:
            col = layout.column()
            col.enabled = not scene.render.engine == "CYCLES"
            col.operator(MUSTARDSIMPLIFY_OT_FastNormals.bl_idname, text = "Enable Eevee Fast Normals" if not settings.simplify_fastnormals_status else "Disable Eevee Fast Normals", icon="MOD_NORMALEDIT")
        
        box=layout.box()
        row = box.row()
        row.prop(settings, 'collapse_options', text="", icon="RIGHTARROW" if settings.collapse_options else "DOWNARROW_HLT", emboss=False)
        row.label(text="Options")
        if not settings.collapse_options:
            col = box.column()
            col.enabled = not settings.simplify_status
            row = col.row()
            row.prop(settings,"modifiers")
            row.operator(MUSTARDSIMPLIFY_OT_MenuModifiersSelect.bl_idname, icon="PREFERENCES", text="")
            col.prop(settings,"shape_keys")
            col.prop(settings,"drivers")
            col.prop(settings,"physics")
            col.prop(settings,"normals_auto_smooth")
        
        box=layout.box()
        row = box.row()
        row.prop(settings, 'collapse_exceptions', text="", icon="RIGHTARROW" if settings.collapse_exceptions else "DOWNARROW_HLT", emboss=False)
        row.label(text="Exceptions")
        if not settings.collapse_exceptions:
            
            row = box.row()
            row.enabled = not settings.simplify_status
            row.template_list("MUSTARDSIMPLIFY_UL_Exceptions_UIList", "The_List", scene.MustardSimplify_Exceptions,
                            "exceptions", scene, "mustardsimplify_exception_uilist_index")
            col = row.column(align=True)
            col.operator(MUSTARDSIMPLIFY_OT_RemoveException.bl_idname, icon = "REMOVE", text = "")
            
            row = box.row()
            row.enabled = not settings.simplify_status
            row.prop_search(settings, "exception_select", scene, "objects", text = "")
            row.operator(MUSTARDSIMPLIFY_OT_AddException.bl_idname, text="", icon="ADD")

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
        #col.prop(settings,"advanced")
        col.prop(settings,"debug")

# ------------------------------------------------------------------------
#    Register
# ------------------------------------------------------------------------

classes = (
    MUSTARDSIMPLIFY_OT_FastNormals,
    MUSTARDSIMPLIFY_OT_SimplifyScene,
    MUSTARDSIMPLIFY_OT_MenuModifiersSelect,
    MUSTARDSIMPLIFY_OT_AddException,
    MUSTARDSIMPLIFY_OT_RemoveException,
    MUSTARDSIMPLIFY_UL_Exceptions_UIList,
    MUSTARDSIMPLIFY_PT_Options,
    MUSTARDSIMPLIFY_PT_Settings,
)

def register():
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    # Indexes for UI Lists
    bpy.types.Scene.mustardsimplify_exception_uilist_index = IntProperty(name = "", default = 0)

def unregister():
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()