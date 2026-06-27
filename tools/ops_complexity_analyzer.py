# Complexity Analyzer
#
# Based on the original "Complexity View" add-on by AUREUS_WOLF.
# Source: https://open3dlab.com/project/f96d3adf-750e-4115-8dc3-f96f32bf0261/
# Adapted for Mustard Simplify.

import colorsys

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

PROP_BACKUP_KEY = "_mustard_simplify_complexity_backup_color"
GRAY_COLOR = (0.2, 0.2, 0.2, 1.0)

# Object types in Blender that can hold modifiers.
MODIFIER_SUPPORTED_TYPES = {
    "MESH",
    "CURVE",
    "SURFACE",
    "FONT",
    "LATTICE",
    "VOLUME",
    "GPENCIL",
    "GREASEPENCIL",
}

LIVE_TIMER_INTERVAL = 1.0  # seconds between live re-applies


# ---------------------- Live update timer ----------------------

_live_timer_active = False


def _live_timer():
    """Periodic callback while Live update is on. Returns the interval to
    reschedule, or None to unregister. Cannot cause depsgraph cycles because
    timers fire outside the depsgraph update phase."""
    global _live_timer_active
    try:
        settings = bpy.context.scene.MustardSimplify_Settings
    except Exception:
        _live_timer_active = False
        return None
    if (
        not settings.complexity_analyzer_active
        or not settings.complexity_analyzer_live_update
    ):
        _live_timer_active = False
        return None
    try:
        apply_heatmap(bpy.context)
    except Exception:
        pass
    return LIVE_TIMER_INTERVAL


def register_live_handler():
    global _live_timer_active
    if _live_timer_active:
        return
    _live_timer_active = True
    bpy.app.timers.register(_live_timer, first_interval=LIVE_TIMER_INTERVAL)


def unregister_live_handler():
    global _live_timer_active
    # Timer auto-unregisters on its next tick (returns None when checked).
    _live_timer_active = False


# ---------------------- Value collection ----------------------


def eval_poly_count(obj, depsgraph):
    if obj.type != "MESH":
        return 0
    try:
        eo = obj.evaluated_get(depsgraph)
        if eo.data is None:
            return 0
        return len(eo.data.polygons)
    except Exception:
        return 0


def texture_pixels_in_material(mat):
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return 0
    total = 0
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            try:
                w, h = node.image.size[0], node.image.size[1]
                total += int(w) * int(h)
            except Exception:
                continue
    return total


def mesh_texture_pixels(obj):
    if obj.type != "MESH" or obj.data is None:
        return 0
    total = 0
    for slot in obj.data.materials:
        if slot is not None:
            total += texture_pixels_in_material(slot)
    return total


def object_modifier_count(obj):
    if obj.type not in MODIFIER_SUPPORTED_TYPES:
        return 0
    try:
        return len(obj.modifiers)
    except (AttributeError, TypeError):
        return 0


def is_object_visible(obj):
    """True if the object is not hidden in the viewport and on a visible
    collection."""
    try:
        if obj.hide_get():
            return False
        if obj.hide_viewport:
            return False
        return obj.visible_get()
    except Exception:
        return True


def collect_objects(context):
    """Return a list of (obj, value) for the visible objects according to the
    current mode. POLYS and TEXTURES are mesh-only; MODIFIERS includes every
    type that can carry modifiers. Hidden objects are excluded from the
    calculation."""
    settings = context.scene.MustardSimplify_Settings
    depsgraph = context.evaluated_depsgraph_get()

    data = []
    for obj in context.scene.objects:
        if not is_object_visible(obj):
            continue
        if settings.complexity_analyzer_mode == "POLYS":
            if obj.type != "MESH":
                continue
            data.append((obj, eval_poly_count(obj, depsgraph)))
        elif settings.complexity_analyzer_mode == "TEXTURES":
            if obj.type != "MESH":
                continue
            data.append((obj, mesh_texture_pixels(obj)))
        else:  # MODIFIERS
            if obj.type not in MODIFIER_SUPPORTED_TYPES:
                continue
            data.append((obj, object_modifier_count(obj)))
    return data


# ---------------------- Color mapping ----------------------


def heatmap_color(value, vmin, vmax):
    if vmax <= vmin:
        t = 0.5
    else:
        t = (value - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
    hue = (1.0 - t) * 0.67  # blue (0.67) -> red (0.0)
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return r, g, b, 1.0


# ---------------------- Backup / restore ----------------------


def backup_object(obj):
    if PROP_BACKUP_KEY not in obj:
        c = obj.color
        obj[PROP_BACKUP_KEY] = (c[0], c[1], c[2], c[3])


def restore_object(obj):
    if PROP_BACKUP_KEY in obj:
        c = obj[PROP_BACKUP_KEY]
        obj.color = (c[0], c[1], c[2], c[3])
        del obj[PROP_BACKUP_KEY]


# ---------------------- Workbench detection ----------------------


def find_view3d_space(context):
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    return space
    return None


def is_workbench(context):
    sp = find_view3d_space(context)
    return sp is not None and sp.shading.type == "SOLID"


def set_workbench_object_color(context):
    sp = find_view3d_space(context)
    if sp is not None:
        sp.shading.type = "SOLID"
        sp.shading.color_type = "OBJECT"


# ---------------------- Apply / disable ----------------------


def apply_heatmap(context):
    settings = context.scene.MustardSimplify_Settings
    data = collect_objects(context)
    if not data:
        settings.complexity_analyzer_active = True
        return 0

    # Restore any previously colored object no longer in scope before re-applying.
    in_data = {d[0] for d in data}
    for obj in context.scene.objects:
        if PROP_BACKUP_KEY in obj and obj not in in_data:
            restore_object(obj)

    if settings.complexity_analyzer_mode in {"TEXTURES", "MODIFIERS"}:
        # Separate zero-value meshes (gray) from real values.
        nonzero = [v for _, v in data if v > 0]
        if nonzero:
            vmin, vmax = min(nonzero), max(nonzero)
        else:
            vmin = vmax = 0
        for obj, val in data:
            backup_object(obj)
            obj.color = GRAY_COLOR if val <= 0 else heatmap_color(val, vmin, vmax)
    else:  # POLYS
        vmin = min(v for _, v in data)
        vmax = max(v for _, v in data)
        for obj, val in data:
            backup_object(obj)
            obj.color = heatmap_color(val, vmin, vmax)

    set_workbench_object_color(context)
    settings.complexity_analyzer_active = True
    _enable_overlay()
    if settings.complexity_analyzer_live_update:
        register_live_handler()
    return len(data)


def disable_heatmap(context):
    settings = context.scene.MustardSimplify_Settings
    n = 0
    for obj in context.scene.objects:
        if PROP_BACKUP_KEY in obj:
            restore_object(obj)
            n += 1
    settings.complexity_analyzer_active = False
    _disable_overlay()
    unregister_live_handler()
    return n


# ---------------------- Viewport overlay (legend) ----------------------

_draw_handle = None


def _draw_callback():
    ctx = bpy.context
    settings = ctx.scene.MustardSimplify_Settings
    if not settings.complexity_analyzer_active:
        return
    sp = find_view3d_space(ctx)
    if sp is None or sp.shading.type != "SOLID":
        return

    region = None
    npanel_w = 0
    for area in ctx.screen.areas:
        if area.type != "VIEW_3D":
            continue
        for r in area.regions:
            if r.type == "WINDOW":
                region = r
            elif r.type == "UI" and r.width > 1:
                npanel_w = r.width  # right-edge offset to avoid the N-panel
        break
    if region is None:
        return

    ui_scale = ctx.preferences.system.ui_scale

    # Layout: gradient strip with two labels above it.
    strip_w = int(220 * ui_scale)
    strip_h = int(12 * ui_scale)
    margin_r = int(16 * ui_scale) + npanel_w
    margin_b = int(40 * ui_scale)
    font_px = int(11 * ui_scale)

    x0 = region.width - margin_r - strip_w
    y0 = margin_b

    # Gradient strip — 64 segments.
    segs = 64
    verts = []
    colors = []
    indices = []
    for i in range(segs):
        t1 = i / segs
        t2 = (i + 1) / segs
        x_a = x0 + t1 * strip_w
        x_b = x0 + t2 * strip_w
        c1 = heatmap_color(t1, 0.0, 1.0)
        c2 = heatmap_color(t2, 0.0, 1.0)
        base = len(verts)
        verts.extend([(x_a, y0), (x_b, y0), (x_b, y0 + strip_h), (x_a, y0 + strip_h)])
        colors.extend([c1, c2, c2, c1])
        indices.extend([(base, base + 1, base + 2), (base, base + 2, base + 3)])

    shader = gpu.shader.from_builtin("SMOOTH_COLOR")
    batch = batch_for_shader(
        shader, "TRIS", {"pos": verts, "color": colors}, indices=indices
    )
    gpu.state.blend_set("ALPHA")
    shader.bind()
    batch.draw(shader)
    gpu.state.blend_set("NONE")

    # Labels above the strip.
    if settings.complexity_analyzer_mode == "POLYS":
        unit_low, unit_high = "Fewer polygons", "More polygons"
    elif settings.complexity_analyzer_mode == "TEXTURES":
        unit_low, unit_high = "Fewer pixels", "More pixels"
    else:  # MODIFIERS
        unit_low, unit_high = "Fewer modifiers", "More modifiers"

    font_id = 0
    try:
        blf.size(font_id, font_px)
    except TypeError:
        blf.size(font_id, font_px, 72)  # Pre-Blender 4.0 signature

    label_y = y0 + strip_h + int(4 * ui_scale)
    text_w_high = blf.dimensions(font_id, unit_high)[0]

    # Draw a black outline via 8-direction offset, then white text on top.
    def draw_with_outline(x, y, txt):
        blf.color(font_id, 0.0, 0.0, 0.0, 0.95)
        for dx, dy in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (1, -1),
            (-1, 1),
            (1, 1),
        ):
            blf.position(font_id, x + dx, y + dy, 0)
            blf.draw(font_id, txt)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, txt)

    draw_with_outline(x0, label_y, unit_low)
    draw_with_outline(x0 + strip_w - text_w_high, label_y, unit_high)


def _enable_overlay():
    global _draw_handle
    if _draw_handle is None:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            _draw_callback, (), "WINDOW", "POST_PIXEL"
        )
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


def _disable_overlay():
    global _draw_handle
    if _draw_handle is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, "WINDOW")
        except Exception:
            pass
        _draw_handle = None
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# ---------------------- Operators ----------------------


class MUSTARDSIMPLIFY_OT_ComplexityAnalyzerToggle(bpy.types.Operator):
    bl_idname = "mustard_simplify.complexity_analyzer_toggle"
    bl_label = "Enable"
    bl_description = (
        "Apply or remove the complexity heatmap.\nThe Viewport might "
        "become unresponsive while the Complexity Analyzer is toggled "
        "on, especially when evaluating the Texture resolution"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.MustardSimplify_Settings
        if settings.complexity_analyzer_active:
            disable_heatmap(context)
        else:
            apply_heatmap(context)
        return {"FINISHED"}


class MUSTARDSIMPLIFY_OT_ComplexityAnalyzerSwitchWorkbench(bpy.types.Operator):
    bl_idname = "mustard_simplify.complexity_analyzer_switch_workbench"
    bl_label = "Switch to Workbench"
    bl_description = "Switch the 3D viewport shading to Workbench (Solid) mode"
    bl_options = {"REGISTER"}

    def execute(self, context):
        sp = find_view3d_space(context)
        if sp is None:
            self.report({"WARNING"}, "Mustard Simplify - No 3D viewport found")
            return {"CANCELLED"}
        sp.shading.type = "SOLID"
        sp.shading.color_type = "OBJECT"
        return {"FINISHED"}


classes = (
    MUSTARDSIMPLIFY_OT_ComplexityAnalyzerToggle,
    MUSTARDSIMPLIFY_OT_ComplexityAnalyzerSwitchWorkbench,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    _disable_overlay()
    unregister_live_handler()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
