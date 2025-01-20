import bpy
from bpy.props import *
from .. import __package__ as base_package


class MustardSimplify_SetObject(bpy.types.PropertyGroup):
    name: StringProperty(default="")
    disp_name: StringProperty(default="")
    icon: StringProperty(default="")
    simplify: BoolProperty(default=True)


class MustardSimplify_SetObjects(bpy.types.PropertyGroup):
    objects: CollectionProperty(type=MustardSimplify_SetObject)


class MUSTARDSIMPLIFY_OT_MenuObjectSelect(bpy.types.Operator):
    """Select the Objects affected by the simplification process"""
    bl_idname = "mustard_simplify.menu_objects_select"
    bl_label = "Select Objects to Simplify"

    @classmethod
    def poll(cls, context):
        # Enable operator only when the scene is not simplified
        settings = bpy.context.scene.MustardSimplify_Settings
        return not settings.simplify_status

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):

        def add_object(collection, name, disp_name, icon, simplify):
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
        objects = scene.MustardSimplify_SetObjects.objects
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        # Extract type of Objects
        rna = bpy.ops.object.add.get_rna_type()
        objs_list = rna.bl_rna.properties['type'].enum_items.keys()

        # Make the list
        # This is done at run-time, so it should be version agnostic
        if len(objs_list) != len(objects):

            objects.clear()

            for m in objs_list:

                # Change the displayed name
                disp_name = m.replace("_", " ")
                disp_name = disp_name.title()

                icon = m + "_DATA"
                simplify = True

                # Manage single exceptions
                if m in ["LIGHT_PROBE"]:
                    icon = "OUTLINER_DATA_LIGHTPROBE"
                elif m in ["SPEAKER"]:
                    icon = "OUTLINER_DATA_SPEAKER"
                elif m in ["GPENCIL", "GREASEPENCIL"]:
                    disp_name = "Grease Pencil"
                    if m == "GPENCIL":
                        disp_name += " (old)"
                    icon = "OUTLINER_DATA_GREASEPENCIL"

                if m in settings.objects_ignore:
                    simplify = False

                add_object(objects, m, disp_name, icon, simplify)

            if addon_prefs.debug:
                print("Mustard Simplify - Objects List generated for Objects")

        return context.window_manager.invoke_props_dialog(self, width=780)

    def draw(self, context):

        scene = bpy.context.scene
        objects = scene.MustardSimplify_SetObjects.objects

        layout = self.layout
        box = layout.box()

        row = box.row()
        col = row.column()

        for i, m in enumerate(objects, 0):
            if m.name == "GREASEPENCIL":
                col = row.column()
            row2 = col.row()
            row2.prop(m, 'simplify', text="")
            # Avoid missing icon error
            try:
                row2.label(text=m.disp_name, icon=m.icon)
            except:
                row2.label(text=m.disp_name, icon="BLANK1")


def register():
    bpy.utils.register_class(MustardSimplify_SetObject)

    bpy.utils.register_class(MustardSimplify_SetObjects)
    bpy.types.Scene.MustardSimplify_SetObjects = PointerProperty(type=MustardSimplify_SetObjects)

    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_MenuObjectSelect)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_MenuObjectSelect)
    bpy.utils.unregister_class(MustardSimplify_SetObjects)
    bpy.utils.unregister_class(MustardSimplify_SetObject)
