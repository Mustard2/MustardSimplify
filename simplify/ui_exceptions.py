import bpy
from bpy.props import *


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

        def add_exception(collection, obj):
            for el in collection:
                if el.exception == obj:
                    return False
            add_item = collection.add()
            add_item.exception = obj
            return True

        def find_exception(collection, obj):
            for el in collection:
                if el.exception == obj:
                    return el.exception
            return None

        settings = bpy.context.scene.MustardSimplify_Settings
        scene = context.scene

        if settings.exception_select is not None:
            res = add_exception(scene.MustardSimplify_Exceptions.exceptions, settings.exception_select)
            if not res:
                self.report({'ERROR'}, 'Mustard Simplify - Object already added to exceptions.')

        settings.exception_select = None

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

        return {'FINISHED'}


class MUSTARDSIMPLIFY_UL_Exceptions_UIList(bpy.types.UIList):
    """UIList for exceptions."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        def draw_icon(layout, icon, cdx):
            if cdx:
                layout.label(text="", icon=icon)
            else:
                layout.label(text="", icon="BLANK1")

        scene = context.scene
        settings = scene.MustardSimplify_Settings

        item_in_exception_collection = False
        if settings.exception_collection is not None:
            item_in_exception_collection = item.exception in [x for x in settings.exception_collection.objects]

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item.exception, 'name', text="", icon="OUTLINER_OB_" + item.exception.type, emboss=False,
                        translate=False)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item.exception, 'name', text="", icon="OUTLINER_OB_" + item.exception.type, emboss=False,
                        translate=False)

        row = layout.row(align=True)
        draw_icon(row, "COLLECTION_COLOR_01", item_in_exception_collection)
        draw_icon(row, "MODIFIER", item.modifiers)
        draw_icon(row, "SHAPEKEY_DATA", item.shape_keys)
        draw_icon(row, "DRIVER", item.drivers)
        draw_icon(row, "NORMALS_FACE", item.normals_auto_smooth)


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_AddException)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_RemoveException)
    bpy.utils.register_class(MUSTARDSIMPLIFY_UL_Exceptions_UIList)

    # Indexes for UI Lists
    bpy.types.Scene.mustardsimplify_exception_uilist_index = IntProperty(name="", default=0)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_UL_Exceptions_UIList)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_RemoveException)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_AddException)
