import bpy
from bpy.props import *


class MUSTARDSIMPLIFY_OT_DataRemoval(bpy.types.Operator):
    """Remove heavy data from objects"""
    bl_idname = "mustard_simplify.data_removal"
    bl_label = "Remove Data"
    bl_options = {'UNDO'}

    remove_diffeomorphic_data: BoolProperty(default=True,
                                            name="Diffeomorphic",
                                            description="Remove Diffeomorphic data")
    remove_diffeomorphic_data_preserve_morphs: BoolProperty(default=True,
                                                            name="Preserve Morphs",
                                                            description="Prevent Morphs deletion")
    remove_custom_string_data: StringProperty(default="",
                                              name="Custom Removal",
                                              description="Remove all data blocks which contains this custom string")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        def remove_data(obj, attr):
            try:
                del obj[attr]
                return 1
            except:
                return 0

        scene = context.scene
        addon_prefs = context.preferences.addons["MustardSimplify"].preferences

        if addon_prefs.debug:
            print("\n ----------- MUSTARD SIMPLIFY DATA REMOVAL LOG -----------\n")

        # Decide which data to remove
        to_remove = []
        to_preserve = []
        if self.remove_custom_string_data != "" and addon_prefs.advanced:
            to_remove.append(self.remove_custom_string_data)
            if addon_prefs.debug:
                print("Removing data with string: " + self.remove_custom_string_data)
        if self.remove_diffeomorphic_data:
            to_remove.append("Daz")
            if addon_prefs.debug:
                print("Removing Diffeomorphic data")
            if self.remove_diffeomorphic_data_preserve_morphs:
                to_preserve.append("DazExpressions")
                to_preserve.append("DazFacs")
                to_preserve.append("DazFacsexpr")
                to_preserve.append("DazFlexions")
                to_preserve.append("DazUnits")
                to_preserve.append("DazVisemes")
                to_preserve.append("DazMorphCats")
                to_preserve.append("DazCustomMorphs")
                to_preserve.append("DazCustom")
                to_preserve.append("DazActivated")

        if not len(to_remove):
            self.report({'WARNING'}, "Mustard Simplify - No Data Block to remove was selected.")
            return {'FINISHED'}

        # Gather Objects
        objects = []
        for obj in bpy.data.objects:
            objects.append(obj)
            if obj.data is not None:
                objects.append(obj.data)

        # Remove data
        data_deleted = 0
        for obj in objects:
            items_to_remove = []
            for k, v in obj.items():
                for el in to_remove:
                    if el in k:
                        items_to_remove.append(k)
            items_to_remove.reverse()
            if addon_prefs.debug and len(items_to_remove) > 0:
                print("\n Removing from Object: " + obj.name)
            for k in items_to_remove:
                if not k in to_preserve:
                    data_deleted = data_deleted + remove_data(obj, k)
                if addon_prefs.debug:
                    print("   - " + k)
            obj.update_tag()

        if data_deleted > 0:
            self.report({'INFO'}, "Mustard Simplify - Data Blocks removed: " + str(data_deleted))
        else:
            self.report({'WARNING'}, "Mustard Simplify - No Data Block to remove was found.")

        return {'FINISHED'}

    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):

        addon_prefs = context.preferences.addons["MustardSimplify"].preferences

        layout = self.layout

        if addon_prefs.advanced:
            box = layout.box()
            box.label(text="General", icon="SETTINGS")
            box.prop(self, 'remove_custom_string_data')

        box = layout.box()
        col = box.column()
        col.label(text="External Add-on", icon="WORLD_DATA")
        col.prop(self, 'remove_diffeomorphic_data')
        row = col.row(align=True)
        row.enabled = self.remove_diffeomorphic_data
        row.label(text="", icon="BLANK1")
        row.prop(self, 'remove_diffeomorphic_data_preserve_morphs')


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_DataRemoval)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_DataRemoval)
