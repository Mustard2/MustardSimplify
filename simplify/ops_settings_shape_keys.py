import bpy


class MUSTARDSIMPLIFY_OT_MenuShapeKeysSettings(bpy.types.Operator):
    """Modify Shape Keys settings"""
    bl_idname = "mustard_simplify.menu_shape_keys_settings"
    bl_label = "Shape Keys Settings"

    @classmethod
    def poll(cls, context):
        # Enable operator only when the scene is not simplified
        settings = bpy.context.scene.MustardSimplify_Settings
        return not settings.simplify_status

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        scene = bpy.context.scene
        settings = bpy.context.scene.MustardSimplify_Settings

        layout = self.layout

        box = layout.box()
        box.label(text="Global Settings", icon="SHAPEKEY_DATA")
        col = box.column()
        col.prop(settings, 'shape_keys_disable_not_null')

        box = layout.box()
        box.label(text="Driven Shape-Keys", icon="DRIVER")
        col = box.column()
        col.prop(settings, 'shape_keys_disable_with_keyframes')
        col.prop(settings, 'shape_keys_disable_with_drivers')
        row = col.row()
        row.enabled = settings.shape_keys_disable_with_drivers
        row.label(text="", icon="BLANK1")
        row.scale_x = 0.5
        row.prop(settings, 'shape_keys_disable_with_drivers_not_null')


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_MenuShapeKeysSettings)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_MenuShapeKeysSettings)
