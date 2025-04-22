import bpy
from bpy.props import *
from .. import utils
from ..utils.execution_time import update_all_execution_time
from .. import __package__ as base_package


class MustardSimplify_SetModifier(bpy.types.PropertyGroup):
    name: StringProperty(default="")
    disp_name: StringProperty(default="")
    icon: StringProperty(default="")
    simplify: BoolProperty(default=True)
    type: StringProperty(default="OBJECT")
    execution_time: BoolProperty(default=False)

    time: FloatProperty(default=0.0)


class MustardSimplify_SetModifiers(bpy.types.PropertyGroup):
    modifiers: CollectionProperty(type=MustardSimplify_SetModifier)


def define_modifiers(scene):

    def add_modifier(collection, name, disp_name, icon, simplify, type):
        for el in collection:
            if el.name == name:
                return False
        add_item = collection.add()
        add_item.name = name
        add_item.disp_name = disp_name
        add_item.icon = icon
        add_item.simplify = simplify
        add_item.type = type
        return True

    settings = scene.MustardSimplify_Settings
    modifiers = scene.MustardSimplify_SetModifiers.modifiers
    addon_prefs = bpy.context.preferences.addons[base_package].preferences

    # Extract type of modifiers for Objects
    rna = bpy.ops.object.modifier_add.get_rna_type()
    mods_list = rna.bl_rna.properties['type'].enum_items.keys()

    # Make the list
    # This is done at run-time, so it should be version agnostic
    if len(mods_list) != len(modifiers):

        modifiers.clear()

        for m in mods_list:

            # Standard modifiers
            if not "GREASE_PENCIL_" in m and not "LINEART" in m:

                # Change the displayed name
                disp_name = m.replace("_", " ")
                disp_name = disp_name.title()
                disp_name = disp_name.replace("Uv", "UV")

                icon = "MOD_" + m
                simplify = True

                # Manage single exceptions
                if m in ["MESH_CACHE", "MESH_SEQUENCE_CACHE", "LAPLACIANDEFORM", "MESH_DEFORM", "SURFACE_DEFORM",
                         "SURFACE"]:
                    icon = "MOD_MESHDEFORM"
                if m in ["LAPLACIANDEFORM"]:
                    icon = "MOD_MESHDEFORM"
                    disp_name = "Laplacian Deform"
                elif m in ["NORMAL_EDIT", "WEIGHTED_NORMAL"]:
                    icon = "MOD_NORMALEDIT"
                elif m in ["UV_PROJECT", "UV_WARP"]:
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
                elif m in ["FLUID"]:
                    icon = "MOD_FLUIDSIM"

                if m in settings.modifiers_ignore:
                    simplify = False

                add_modifier(modifiers, m, disp_name, icon, simplify, "OBJECT")

            # Grease Pencil modifiers
            else:

                # Change the displayed name
                disp_name = m[14:].replace("_", " ")
                if "LINEART" in m:
                    disp_name = m.replace("_", " ")
                disp_name = disp_name.title()
                disp_name = disp_name.replace("Uv", "UV")

                icon = "MOD_" + m[14:]
                if "LINEART" in m:
                    icon = "MOD_" + m
                simplify = True

                # Manage single exceptions
                if m in ["GREASE_PENCIL_TEXTURE"]:
                    icon = "TEXTURE"
                elif m in ['GREASE_PENCIL_VERTEX_WEIGHT_ANGLE', 'GREASE_PENCIL_VERTEX_WEIGHT_PROXIMITY']:
                    icon = "MOD_VERTEX_WEIGHT"
                elif m in ["GREASE_PENCIL_MULTIPLY"]:
                    icon = "GP_MULTIFRAME_EDITING"
                elif m in ["GREASE_PENCIL_SUBDIV"]:
                    icon = "MOD_SUBSURF"
                elif m in ["GREASE_PENCIL_THICK"]:
                    icon = "MOD_THICKNESS"
                elif m in ["GREASE_PENCIL_HOOK"]:
                    icon = m[14:]
                elif m in ["GREASE_PENCIL_COLOR"]:
                    icon = "MOD_HUE_SATURATION"

                if m in settings.modifiers_ignore:
                    simplify = False

                add_modifier(modifiers, m, disp_name, icon, simplify, "GPENCIL")

        if addon_prefs.debug:
            print("Mustard Simplify - Modifiers List generated")


class MUSTARDSIMPLIFY_OT_MenuModifiersSelect(bpy.types.Operator):
    """Select the modifiers affected by the simplification process"""
    bl_idname = "mustard_simplify.menu_modifiers_select"
    bl_label = "Select Modifiers to Simplify"

    type: EnumProperty(items=[("OBJECT", "Objects", "Object", "MESH_DATA", 0),
                              ("GPENCIL", "Grease Pencil", "Grease Pencil", "OUTLINER_DATA_GREASEPENCIL", 1)])

    @classmethod
    def poll(cls, context):
        # Enable operator only when the scene is not simplified
        settings = bpy.context.scene.MustardSimplify_Settings
        return not settings.simplify_status

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):

        scene = bpy.context.scene
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        define_modifiers(scene)

        update_all_execution_time()

        return context.window_manager.invoke_props_dialog(self, width=1024 if addon_prefs.debug else 900)

    def draw(self, context):

        scene = bpy.context.scene
        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        layout = self.layout

        layout.prop(self, "type", expand=True)

        box = layout.box()

        row = box.row()
        col = row.column()

        if self.type == "OBJECT":

            for m in [x for x in modifiers if x.type == "OBJECT"]:
                if m.name in ["ARRAY", "ARMATURE", "CLOTH"]:
                    col = row.column()
                row2 = col.row()
                row2.prop(m, 'simplify', text="")
                # Avoid missing icon error
                try:
                    row2.label(text=m.disp_name, icon=m.icon)
                    row2.scale_x = 0.2
                    row2.alert = m.time > 0.1
                    if addon_prefs.debug:
                        row2.label(text=str(int(m.time*1000)) + " ms" if m.execution_time else "")
                    row2.scale_x = 1
                    row2.prop(m, 'execution_time', text="", icon="TIME" if m.execution_time else "MOD_TIME")
                except:
                    row2.label(text=m.disp_name, icon="BLANK1")

        if self.type == "GPENCIL":

            mods = [x for x in modifiers if x.type == "GPENCIL"]

            order = [
                # Edit
                'GREASE_PENCIL_TEXTURE', 'GREASE_PENCIL_TIME', 'GREASE_PENCIL_VERTEX_WEIGHT_PROXIMITY',
                'GREASE_PENCIL_VERTEX_WEIGHT_ANGLE',
                # Generate
                'GREASE_PENCIL_ARRAY', 'GREASE_PENCIL_BUILD', 'GREASE_PENCIL_ENVELOPE', 'GREASE_PENCIL_DASH',
                'GREASE_PENCIL_LENGTH', 'LINEART', 'GREASE_PENCIL_MIRROR', 'GREASE_PENCIL_MULTIPLY',
                'GREASE_PENCIL_OUTLINE', 'GREASE_PENCIL_SIMPLIFY', 'GREASE_PENCIL_SUBDIV',
                # Deform
                'GREASE_PENCIL_ARMATURE', 'GREASE_PENCIL_HOOK', 'GREASE_PENCIL_LATTICE', 'GREASE_PENCIL_NOISE',
                'GREASE_PENCIL_OFFSET', 'GREASE_PENCIL_SHRINKWRAP', 'GREASE_PENCIL_SMOOTH',
                'GREASE_PENCIL_THICKNESS',
                # Color
                'GREASE_PENCIL_COLOR', 'GREASE_PENCIL_OPACITY', 'GREASE_PENCIL_TINT']

            order_index = {name: idx for idx, name in enumerate(order)}
            mods = sorted(mods, key=lambda modifier: order_index.get(modifier.name, float('inf')))

            for m in mods:
                if m.name in ["GREASE_PENCIL_ARRAY", "GREASE_PENCIL_ARMATURE", "GREASE_PENCIL_COLOR"]:
                    col = row.column()
                row2 = col.row()
                row2.prop(m, 'simplify', text="")
                # Avoid missing icon error
                try:
                    row2.label(text=m.disp_name, icon=m.icon)
                except:
                    row2.label(text=m.disp_name, icon="BLANK1")


def register():
    bpy.utils.register_class(MustardSimplify_SetModifier)

    bpy.utils.register_class(MustardSimplify_SetModifiers)
    bpy.types.Scene.MustardSimplify_SetModifiers = PointerProperty(type=MustardSimplify_SetModifiers)

    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_MenuModifiersSelect)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_MenuModifiersSelect)

    del bpy.types.Scene.MustardSimplify_SetModifiers
    bpy.utils.unregister_class(MustardSimplify_SetModifiers)

    bpy.utils.unregister_class(MustardSimplify_SetModifier)
