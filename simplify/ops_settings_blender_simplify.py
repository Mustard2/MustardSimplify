import bpy


class MUSTARDSIMPLIFY_OT_MenuBlenderSimplifySettings(bpy.types.Operator):
    """Modify Blender Simplify settings"""
    bl_idname = "mustard_simplify.menu_blender_simplify_settings"
    bl_label = "Blender Simplify Settings"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        return {'FINISHED'}

    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):

        scene = context.scene
        modifiers = scene.MustardSimplify_SetModifiers.modifiers
        settings = bpy.context.scene.MustardSimplify_Settings

        layout = self.layout
        layout.use_property_split = True
        rd = scene.render

        # Viewport
        box = layout.box()

        box.label(text="Viewport", icon="RESTRICT_VIEW_ON")

        flow = box.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(rd, "simplify_subdivision", text="Max Subdivision")
        col = flow.column()
        col.prop(rd, "simplify_child_particles", text="Max Child Particles")
        col = flow.column()
        col.prop(rd, "simplify_volumes", text="Volume Resolution")
        if context.engine in 'BLENDER_EEVEE_NEXT':
            col = flow.column()
            col.prop(rd, "simplify_shadows", text="Shadow Resolution")

        # Render
        box = layout.box()

        box.label(text="Render", icon="RESTRICT_RENDER_ON")

        flow = box.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(rd, "simplify_subdivision_render", text="Max Subdivision")
        col = flow.column()
        col.prop(rd, "simplify_child_particles_render", text="Max Child Particles")
        if context.engine in 'BLENDER_EEVEE_NEXT':
            col = flow.column()
            col.prop(rd, "simplify_shadows_render", text="Shadow Resolution")


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_MenuBlenderSimplifySettings)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_MenuBlenderSimplifySettings)
