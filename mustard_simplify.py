# Mustard Tools script
# https://github.com/Mustard2/MustardTools

bl_info = {
    "name": "Mustard Simplify",
    "description": "A set of tools to simplify scenes for better viewport performance",
    "author": "Mustard",
    "version": (0, 0, 1),
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
    normals_auto_smooth: bpy.props.BoolProperty(name="Normals Auto Smooth",
                                        description="Disable Normals Auto Smooth",
                                        default=True)
    
    # UI Settings
    collapse_options: bpy.props.BoolProperty(name="Collapse",
                                        default=True)
            
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
class MustardSimplify_Status(bpy.types.PropertyGroup):
    
    # Normals Auto Smooth
    normals_auto_smooth: bpy.props.BoolProperty(name="Normals Auto Smooth",
                                        description="Disable Normals Auto Smooth",
                                        default=True)
    # Modifiers status
    modifiers: bpy.props.CollectionProperty(type=MustardSimplify_ModifierStatus)
    # Shape Keys status
    shape_keys: bpy.props.CollectionProperty(type=MustardSimplify_ShapeKeysStatus)
            
bpy.utils.register_class(MustardSimplify_Status)
bpy.types.Object.MustardSimplify_Status = bpy.props.PointerProperty(type=MustardSimplify_Status)

# ------------------------------------------------------------------------
#    Merge Images To Grayscale
# ------------------------------------------------------------------------

class MUSTARDSIMPLIFY_OT_SimplifyScene(bpy.types.Operator):
    """Simplify the scene to increase the viewport performance"""
    bl_idname = "mustard_simplify.scene"
    bl_label = "Simplify Scene"
    bl_options = {'REGISTER','UNDO'}
    
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
                if self.enable_simplify:
                    obj.MustardSimplify_Status.modifiers.clear()
                    for mod in obj.modifiers:
                        add_prop_status(obj.MustardSimplify_Status.modifiers, [mod.name, mod.show_viewport])
                        mod.show_viewport = False
                else:
                    for mod in obj.modifiers:
                        name, status = find_prop_status(obj.MustardSimplify_Status.modifiers, mod)
                        if name != "":
                            mod.show_viewport = status
            
            # Modifiers
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
                
        
        if self.enable_simplify:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Enabled.')
        else:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Disabled.')
        
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
        settings = bpy.context.scene.MustardSimplify_Settings
        
        layout.operator(MUSTARDSIMPLIFY_OT_SimplifyScene.bl_idname, text = "Simplify Scene")
        
        box=layout.box()
        row = box.row()
        row.prop(settings, 'collapse_options', text="", icon="RIGHTARROW" if settings.collapse_options else "DOWNARROW_HLT", emboss=False)
        row.label(text="Options")
        if not settings.collapse_options:
            col = box.column()
            col.prop(settings,"modifiers")
            col.prop(settings,"shape_keys")
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