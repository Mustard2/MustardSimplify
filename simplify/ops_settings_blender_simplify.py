import bpy


class MUSTARDSIMPLIFY_OT_MenuBlenderSimplifySettings(bpy.types.Operator):
    """Modify Blender Simplify settings"""

    bl_idname = "mustard_simplify.menu_blender_simplify_settings"
    bl_label = "Blender Simplify Settings"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        settings = context.scene.MustardSimplify_Settings
        settings.blender_simplify_engine = (
            "CYCLES" if context.scene.render.engine == "CYCLES" else "EEVEE"
        )
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):

        scene = context.scene
        settings = scene.MustardSimplify_Settings

        layout = self.layout
        layout.use_property_split = True
        rd = scene.render
        cscene = scene.cycles if hasattr(scene, "cycles") else None

        layout.row(align=True).prop(settings, "blender_simplify_engine", expand=True)
        show_cycles = (
            cscene is not None and settings.blender_simplify_engine == "CYCLES"
        )

        # Viewport
        box = layout.box()

        box.label(text="Viewport", icon="RESTRICT_VIEW_ON")

        flow = box.grid_flow(
            row_major=True, columns=0, even_columns=False, even_rows=False, align=True
        )

        col = flow.column()
        col.prop(rd, "simplify_subdivision", text="Max Subdivision")
        col = flow.column()
        col.prop(rd, "simplify_child_particles", text="Max Child Particles")
        col = flow.column()
        col.prop(rd, "simplify_volumes", text="Volume Resolution")
        col = flow.column()
        col.prop(rd, "use_simplify_normals", text="Normals")
        if show_cycles:
            if hasattr(cscene, "texture_resolution"):
                col = flow.column()
                col.prop(cscene, "texture_resolution", text="Texture Resolution")
            col = flow.column()
            col.prop(cscene, "texture_limit", text="Texture Size Limit")

        # Render
        box = layout.box()

        box.label(text="Render", icon="RESTRICT_RENDER_ON")

        flow = box.grid_flow(
            row_major=True, columns=0, even_columns=False, even_rows=False, align=True
        )

        col = flow.column()
        col.prop(rd, "simplify_subdivision_render", text="Max Subdivision")
        col = flow.column()
        col.prop(rd, "simplify_child_particles_render", text="Max Child Particles")
        if show_cycles:
            if hasattr(cscene, "texture_resolution_render"):
                col = flow.column()
                col.prop(cscene, "texture_resolution_render", text="Texture Resolution")
            col = flow.column()
            col.prop(cscene, "texture_limit_render", text="Texture Size Limit")

        # Culling
        if show_cycles:
            box = layout.box()

            box.label(text="Culling", icon="HIDE_ON")

            col = box.column()

            row = col.row(heading="Camera Culling")
            row.prop(cscene, "use_camera_cull", text="")
            sub = row.column()
            sub.active = cscene.use_camera_cull
            sub.prop(cscene, "camera_cull_margin", text="")

            row = col.row(heading="Distance Culling")
            row.prop(cscene, "use_distance_cull", text="")
            sub = row.column()
            sub.active = cscene.use_distance_cull
            sub.prop(cscene, "distance_cull_margin", text="")


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_MenuBlenderSimplifySettings)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_MenuBlenderSimplifySettings)
