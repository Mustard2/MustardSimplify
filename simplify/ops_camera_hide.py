import bpy
import mathutils
import mathutils.geometry as geom


def camera_as_planes(scene, cam_obj):
    cam = cam_obj.data
    matrix = cam_obj.matrix_world.normalized()
    frame = [matrix @ v for v in cam.view_frame(scene=scene)]
    origin = matrix.to_translation()

    planes = []
    for i in range(4):
        p1 = origin if cam.type != 'ORTHO' else frame[i] + matrix.col[2].xyz
        p2 = frame[i - 1]
        p3 = frame[i]
        normal = geom.normal(p1, p2, p3)
        d = -normal.dot(p1)
        planes.append((normal, d))
    return planes


def is_bbox_in_frustum(obj, planes):
    box = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    for normal, d in planes:
        if all(normal.dot(corner) + d < 0 for corner in box):
            return False
    return True


def store_objects_visibility():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj["was_hidden_before_culling"] = obj.hide_viewport


def apply_frustum_culling():
    def find_exception_obj(collection, obj):
        for el in collection:
            if el.exception == obj:
                return el
        return None

    scene = bpy.context.scene

    settings = scene.MustardSimplify_Settings

    cam_obj = scene.camera
    if cam_obj is None:
        return
    planes = camera_as_planes(scene, cam_obj)
    for obj in [x for x in scene.objects if x and x.type == 'MESH']:
        exception_collection = settings.exception_collection
        exception = find_exception_obj(scene.MustardSimplify_Exceptions.exceptions, obj)
        if (exception is not None and not exception.camera_hide) or (
                exception_collection is not None and obj in [x for x in (
                settings.exception_collection.all_objects if settings.exception_include_subcollections else settings.exception_collection.objects)]):
            continue
        was_hidden_before = obj.get("was_hidden_before_culling", False)
        if was_hidden_before and not obj.hide_viewport:
            obj.hide_viewport = True
        elif not was_hidden_before and not obj.hide_viewport == (not is_bbox_in_frustum(obj, planes)):
            obj.hide_viewport = not is_bbox_in_frustum(obj, planes)


def restore_objects_visibility():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            was_hidden = obj.get("was_hidden_before_culling")
            if was_hidden is not None:
                obj.hide_viewport = was_hidden
                del obj["was_hidden_before_culling"]


class MUSTARDSIMPLIFY_OT_CameraHideModel(bpy.types.Operator):
    bl_idname = "mustard_simplify.live_frustum_culling"
    bl_label = "Live Frustum Culling Modal Operator"
    bl_options = {'INTERNAL'}

    _timer = None

    def modal(self, context, event):
        scene = context.scene
        settings = scene.MustardSimplify_Settings
        wm = context.window_manager

        if settings.live_frustum_should_stop:
            settings.live_frustum_should_stop = False
            if self._timer:
                wm.event_timer_remove(self._timer)
                self._timer = None
            return {'CANCELLED'}

        if event.type == 'TIMER':
            apply_frustum_culling()
            return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        settings = scene.MustardSimplify_Settings
        wm = context.window_manager

        interval = settings.live_frustum_interval
        self._timer = wm.event_timer_add(interval, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class MUSTARDSIMPLIFY_OT_CameraHide(bpy.types.Operator):
    bl_idname = "mustard_simplify.toggle_live_frustum_culling"
    bl_label = "Toggle Live Camera Hide"
    bl_description = "Toggle live Camera Hide on/off"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        settings = scene.MustardSimplify_Settings

        if not settings.live_frustum_running:
            store_objects_visibility()
            bpy.ops.mustard_simplify.live_frustum_culling('INVOKE_DEFAULT')
            settings.live_frustum_running = True
        else:
            settings.live_frustum_should_stop = True
            restore_objects_visibility()
            settings.live_frustum_running = False

        return {'FINISHED'}


class MUSTARDSIMPLIFY_OT_ApplyCameraHide(bpy.types.Operator):
    bl_idname = "mustard_simplify.apply_frustum_culling"
    bl_label = "Apply Camera Hide"
    bl_description = "Hide mesh objects outside the active camera frustum"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        settings = scene.MustardSimplify_Settings

        if not settings.live_frustrum_single_applied:
            store_objects_visibility()
            settings.live_frustrum_single_applied = True

        apply_frustum_culling()

        self.report({'INFO'}, "Mustard Simplify - Camera Hide applied")
        return {'FINISHED'}


class MUSTARDSIMPLIFY_OT_RestoreCameraHide(bpy.types.Operator):
    bl_idname = "mustard_simplify.restore_frustum_culling"
    bl_label = "Restore Camera Hide"
    bl_description = "Restore Camera Hide"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        settings = scene.MustardSimplify_Settings

        restore_objects_visibility()
        settings.live_frustrum_single_applied = False

        self.report({'INFO'}, "Mustard Simplify - Camera Hide restored")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_CameraHideModel)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_CameraHide)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_ApplyCameraHide)
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_RestoreCameraHide)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_RestoreCameraHide)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_ApplyCameraHide)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_CameraHide)
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_CameraHideModel)
