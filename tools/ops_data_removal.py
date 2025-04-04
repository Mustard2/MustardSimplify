import bpy
from bpy.props import *
from .. import __package__ as base_package


class MustardSimplify_DataRemoval_Entry(bpy.types.PropertyGroup):
    name: StringProperty(default="")
    remove: BoolProperty(default=False)
    count: IntProperty()


class MustardSimplify_DataRemoval(bpy.types.PropertyGroup):
    entries: CollectionProperty(type=MustardSimplify_DataRemoval_Entry)


class MUSTARDSIMPLIFY_OT_DataRemoval_SelectAll(bpy.types.Operator):
    """Select/deselect all data blocks"""
    bl_idname = "mustard_simplify.data_removal_select"
    bl_label = "Select/Deselect All"
    bl_options = {'UNDO'}

    select: BoolProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        scene = context.scene
        entries = scene.MustardSimplify_DataRemoval.entries

        for e in entries:
            e.remove = self.select

        return {'FINISHED'}


class MUSTARDSIMPLIFY_OT_DataRemoval(bpy.types.Operator):
    """Remove data from objects.\nThis is a highly destructive operation, only remove data that you know are not needed!"""
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
        entries = scene.MustardSimplify_DataRemoval.entries
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        if not len([x for x in entries if x.remove]):
            self.report({'WARNING'}, "Mustard Simplify - No Data Block to remove was selected.")
            return {'FINISHED'}

        # Remove data
        data_deleted = 0
        for obj in [x for x in scene.objects if x is not None]:
            items_to_remove = []
            for k, v in obj.items():
                for ll in [x.name for x in entries if x.remove]:
                    if ll == k:
                        items_to_remove.append(k)
            if obj.data is not None:
                for k, v in obj.data.items():
                    for ll in [x.name for x in entries if x.remove]:
                        if ll == k:
                            items_to_remove.append(k)
            items_to_remove.reverse()
            if addon_prefs.debug and len(items_to_remove) > 0:
                print("\n Removing from Object: " + obj.name)
            for k in items_to_remove:
                data_deleted = data_deleted + remove_data(obj, k)
                data_deleted = data_deleted + remove_data(obj.data, k)
                if addon_prefs.debug:
                    print("   - " + k)
            obj.update_tag()

        if data_deleted > 0:
            self.report({'INFO'}, "Mustard Simplify - Data Blocks removed: " + str(data_deleted))
        else:
            self.report({'WARNING'}, "Mustard Simplify - No Data Block to remove was found.")

        return {'FINISHED'}

    def invoke(self, context, event):

        def add_entry(collection, name):
            for c in collection:
                if c.name == name:
                    c.count += 1
                    return False

            add_item = collection.add()
            add_item.name = name
            add_item.count = 1
            return True

        scene = bpy.context.scene
        entries = scene.MustardSimplify_DataRemoval.entries
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        entries.clear()

        for o in [x for x in scene.objects if x is not None]:
            rna_props = o.bl_rna.properties
            for k in o.keys():
                if k in rna_props and rna_props[k].is_runtime:
                    add_entry(entries, k)
            if o.data is not None:
                rna_props = o.data.bl_rna.properties
                for k in o.data.keys():
                    if k in rna_props and rna_props[k].is_runtime:
                        add_entry(entries, k)

        return context.window_manager.invoke_props_dialog(self, width=1024 if addon_prefs.debug else 900)

    def draw(self, context):

        scene = context.scene
        entries = scene.MustardSimplify_DataRemoval.entries

        layout = self.layout
        box = layout.box()

        if len(entries) == 0:
            box.label(text="No Data Blocks found", icon="ERROR")
            return

        box.label(text="This operation is highly destructive! Remove only data-blocks you not need!", icon="ERROR")

        ordered_entries = sorted([x for x in entries], key=lambda x: x.count, reverse=True)
        length_entries = len(ordered_entries)

        cols = [0, 0, 0]
        for i in range(len(cols)):
            cols[i] = int(length_entries/len(cols)) + (cols[i-1] if i > 0 else 0)
        remainder = (length_entries % cols[2]) if cols[2] > 0 else 1
        cols[0] += remainder
        cols[1] += remainder
        cols[2] += remainder

        box = layout.box()
        row = box.row(align=True)
        row.operator("mustard_simplify.data_removal_select", text="Select All").select = True
        row.operator("mustard_simplify.data_removal_select", text="Deselect All").select = False

        row = box.row()
        for i in range(len(cols)):
            col = row.column()
            begin = cols[i-1] if i > 0 else 0
            end = cols[i]
            for e in ordered_entries[begin:end]:
                col.prop(e, 'remove', text=e.name + " (" + str(e.count) + ")")


def register():
    bpy.utils.register_class(MustardSimplify_DataRemoval_Entry)
    bpy.utils.register_class(MustardSimplify_DataRemoval)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_DataRemoval_SelectAll)
    bpy.types.Scene.MustardSimplify_DataRemoval = PointerProperty(type=MustardSimplify_DataRemoval)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_DataRemoval)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_DataRemoval)
    del bpy.types.Scene.MustardSimplify_DataRemoval
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_DataRemoval_SelectAll)
    bpy.utils.unregister_class(MustardSimplify_DataRemoval)
    bpy.utils.unregister_class(MustardSimplify_DataRemoval_Entry)
