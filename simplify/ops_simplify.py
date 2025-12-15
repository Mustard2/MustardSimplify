import bpy
from bpy.props import *
from bpy_extras import anim_utils
from mathutils import Vector, Color
from .ops_settings_modifiers import define_modifiers
from ..utils.execution_time import update_all_execution_time
from .. import __package__ as base_package


class MUSTARDSIMPLIFY_OT_SimplifyScene(bpy.types.Operator):
    """Simplify the scene to increase the viewport performance"""
    bl_idname = "mustard_simplify.scene"
    bl_label = "Simplify Scene"
    bl_options = {'UNDO'}

    enable_simplify: BoolProperty(name="Simplify",
                                  default=True)

    @classmethod
    def poll(cls, context):

        scene = context.scene
        settings = scene.MustardSimplify_Settings

        if not settings.simplify_status:
            if settings.objects:
                return settings.objects and settings.modifiers
            return settings.blender_simplify or settings.modifiers or settings.shape_keys or settings.physics or settings.drivers or settings.normals_auto_smooth
        else:
            return True

    def execute(self, context):

        def add_prop_status(collection, item):
            for el in collection:
                if el.name == item[0] and el.status == item[1]:
                    return
            add_item = collection.add()
            add_item.name = item[0]
            add_item.status = item[1]
            return

        def find_prop_status(collection, mod):
            for el in collection:
                if el.name == mod.name:
                    return el.name, el.status
            return "", None

        def find_exception_obj(collection, obj):
            for el in collection:
                if el.exception == obj:
                    return el
            return None

        def has_keyframe(ob, attr):

            if bpy.app.version < (4, 4, 0):
                anim = ob.animation_data

                if anim is not None and anim.action is not None:
                    for fcu in anim.action.fcurves:
                        if fcu.data_path == attr:
                            return len(fcu.keyframe_points) > 0

            # Slots for Blender > 4.4
            else:
                if not ob or not hasattr(ob, "animation_data"):
                    return False
                animation_data = ob.animation_data

                if not hasattr(animation_data, "action"):
                    return False
                action = animation_data.action
                if not action:
                    return False

                for slot in action.slots:
                    for layer in action.layers:
                        for strip in layer.strips:
                            channelbag = strip.channelbag(slot)
                            for fcu in channelbag.fcurves:
                                if fcu.data_path == attr:
                                    return len(fcu.keyframe_points) > 0

            return False

        def has_driver(ob, attr):
            anim = ob.animation_data
            if anim is not None and anim.drivers is not None:
                for fcu in anim.drivers:
                    if fcu.data_path == attr:
                        return True
            return False

        scene = context.scene
        settings = scene.MustardSimplify_Settings
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        # BLENDER SIMPLIFY
        rd = context.scene.render
        if settings.blender_simplify:
            rd.use_simplify = self.enable_simplify

        # OBJECTS

        # Remove objects in the exception collection
        objects = [x for x in context.scene.objects if x.override_library is None]
        if settings.exception_collection is not None:
            objects = [x for x in context.scene.objects if not x in [x for x in (
                settings.exception_collection.all_objects if settings.exception_include_subcollections else settings.exception_collection.objects)]]

        # Create list of objects to simplify
        objects_ignore = settings.modifiers
        if settings.modifiers:

            chosen_objs = scene.MustardSimplify_SetObjects.objects

            # If the user hasn't used the Objects menu, use the default settings
            if not len(chosen_objs):
                objects_ignore = settings.objects_ignore
            else:
                objects_ignore = [x.name for x in chosen_objs if not x.simplify]

        # Create list of modifiers to simplify
        modifiers_ignore = settings.modifiers
        if settings.modifiers:

            chosen_mods = scene.MustardSimplify_SetModifiers.modifiers

            # If the user hasn't used the Modifiers menu, use the default settings
            if not len(chosen_mods):
                modifiers_ignore = settings.modifiers_ignore
            else:
                modifiers_ignore = [x.name for x in chosen_mods if not x.simplify]

        if addon_prefs.debug:
            print("\n ----------- MUSTARD SIMPLIFY LOG -----------")

        # Track processed mesh data to avoid duplicate processing of shared mesh data
        # Dictionary mapping mesh_data -> source_object for O(1) lookup
        processed_mesh_data = {}

        for obj in objects:

            eo = find_exception_obj(scene.MustardSimplify_Exceptions.exceptions, obj)

            if addon_prefs.debug:
                print("\n ----------- Object: " + obj.name + " -----------")

            if settings.objects and (eo.visibility if eo is not None else True) and not obj.type in objects_ignore:
                if self.enable_simplify:
                    status = obj.hide_viewport
                    obj.MustardSimplify_Status.visibility = status
                    obj.hide_viewport = True
                    if addon_prefs.debug:
                        print("Object " + obj.name + " hidden (previous viewport_hide: " + str(status) + ").")
                else:
                    status = obj.MustardSimplify_Status.visibility
                    obj.hide_viewport = status
                    if addon_prefs.debug:
                        print("Object " + obj.name + " reverted to hide_viewport: " + str(status) + ").")

            # Object Modifiers
            if settings.modifiers and (eo.modifiers if eo is not None else True):

                if self.enable_simplify:
                    define_modifiers(scene)

                modifiers = [x for x in obj.modifiers if not x.type in modifiers_ignore]

                if self.enable_simplify:
                    obj.MustardSimplify_Status.modifiers.clear()
                    for mod in modifiers:
                        # Skip Normals Smooth modifier
                        if mod.type == "NODES" and mod.node_group is not None:
                            if mod.node_group.name == "Smooth by Angle":
                                continue
                        status = mod.show_viewport
                        add_prop_status(obj.MustardSimplify_Status.modifiers, [mod.name, status])
                        mod.show_viewport = False
                        if addon_prefs.debug:
                            print("Modifier " + mod.name + " disabled (previous show_viewport: " + str(status) + ").")
                else:
                    for mod in modifiers:
                        # Skip Normals Smooth modifier
                        if mod.type == "NODES" and mod.node_group is not None:
                            if mod.node_group.name == "Smooth by Angle":
                                continue
                        name, status = find_prop_status(obj.MustardSimplify_Status.modifiers, mod)
                        if name != "":
                            mod.show_viewport = status
                            if addon_prefs.debug:
                                print("Modifier " + mod.name + " reverted to show_viewport: " + str(status) + ".")

            # Shape Keys
            if settings.shape_keys and obj.type == "MESH" and (eo.shape_keys if eo is not None else True):

                # Check if this mesh data has already been processed (to handle shared mesh data)
                mesh_data_processed = obj.data in processed_mesh_data
                source_obj = processed_mesh_data.get(obj.data) if mesh_data_processed else None

                if self.enable_simplify:
                    obj.MustardSimplify_Status.shape_keys.clear()
                    if obj.data.shape_keys is not None:
                        # Only process shape keys if this mesh data hasn't been processed yet
                        if not mesh_data_processed:
                            for sk in obj.data.shape_keys.key_blocks:
                                status = sk.mute
                                add_prop_status(obj.MustardSimplify_Status.shape_keys, [sk.name, status])
                                attr = f'key_blocks["{bpy.utils.escape_identifier(sk.name)}"].value'
                                
                                # We didn't use 0 to accomodate for diffeomorphic models shape-keys that use values in the range [-0.00000?, 0.00000?]
                                # with no visual effect (pretty much useless)!
                                # see https://github.com/Mustard2/MustardSimplify/issues/45#issuecomment-2811323931
                                value_bool = sk.value > -1e-5 and sk.value < 1e-5
                                if has_driver(obj.data.shape_keys, attr):
                                    sk.mute = value_bool if (
                                            settings.shape_keys_disable_with_drivers and settings.shape_keys_disable_with_drivers_not_null) else settings.shape_keys_disable_with_drivers
                                elif has_keyframe(obj.data.shape_keys, attr):
                                    sk.mute = settings.shape_keys_disable_with_keyframes
                                else:
                                    sk.mute = value_bool if settings.shape_keys_disable_not_null else True
                                if addon_prefs.debug:
                                    if sk.mute:
                                        print("Shape key " + sk.name + " disabled (previous mute: " + str(status) + ").")
                                    else:
                                        print("Shape key " + sk.name + " not muted (previous mute: " + str(status) + ").")
                            # Mark this mesh data as processed and store source object
                            processed_mesh_data[obj.data] = obj
                        else:
                            # Mesh data already processed, copy the original state from the source object
                            # Use O(1) dictionary lookup instead of O(N) loop
                            if source_obj is not None and len(source_obj.MustardSimplify_Status.shape_keys) > 0:
                                # Copy the original state from the source object
                                for sk in obj.data.shape_keys.key_blocks:
                                    name, status = find_prop_status(source_obj.MustardSimplify_Status.shape_keys, sk)
                                    if name != "":
                                        add_prop_status(obj.MustardSimplify_Status.shape_keys, [sk.name, status])
                                if addon_prefs.debug:
                                    print("Shape keys for object " + obj.name + " (shared mesh data) - original state copied from " + source_obj.name + ".")
                else:
                    if obj.data.shape_keys is not None:
                        # Only restore shape keys if this mesh data hasn't been restored yet
                        if not mesh_data_processed:
                            # Determine source object for restoration: use current obj if it has status,
                            # otherwise use the source_obj from dictionary (O(1) lookup)
                            restore_source_obj = None
                            if len(obj.MustardSimplify_Status.shape_keys) > 0:
                                # Current object has saved status, use it
                                restore_source_obj = obj
                            elif source_obj is not None and len(source_obj.MustardSimplify_Status.shape_keys) > 0:
                                # Current object has no status, use source_obj from dictionary (O(1) lookup)
                                restore_source_obj = source_obj
                                if addon_prefs.debug:
                                    print("Using shape keys status from object " + restore_source_obj.name + " for shared mesh data (from dictionary).")
                            
                            # Restore shape keys if we found a valid source object
                            if restore_source_obj is not None:
                                for sk in obj.data.shape_keys.key_blocks:
                                    name, status = find_prop_status(restore_source_obj.MustardSimplify_Status.shape_keys, sk)
                                    if name != "":
                                        sk.mute = status
                                        if addon_prefs.debug:
                                            print("Shape key " + sk.name + " reverted to mute: " + str(status) + ".")
                                # Mark this mesh data as processed and store source object for future lookups
                                processed_mesh_data[obj.data] = restore_source_obj
                            else:
                                # No valid source object found (edge case: first disable without prior enable)
                                # Mark as processed to avoid repeated attempts, using current obj as placeholder
                                processed_mesh_data[obj.data] = obj
                                if addon_prefs.debug:
                                    print("Shape keys for object " + obj.name + " - no saved status found, skipping restoration.")
                        else:
                            # Mesh data already processed (restored by first object with status)
                            # Shape keys are already restored, no need to restore again
                            if addon_prefs.debug:
                                print("Shape keys for object " + obj.name + " (shared mesh data) - already restored.")

            # Normals Auto Smooth
            if settings.normals_auto_smooth and obj.type == "MESH" and (
                    eo.normals_auto_smooth if eo is not None else True):

                def get_status_norm_autosmooth(obj):
                    for modifier in [x for x in obj.modifiers if x.type == "NODES"]:
                        if modifier.node_group is None:
                            continue
                        if modifier.node_group.name != "Smooth by Angle":
                            continue
                        return modifier.show_viewport
                    return False

                def update_norm_autosmooth(obj, status):

                    if bpy.app.version < (4, 1, 0):
                        obj.data.use_auto_smooth = status
                        return

                    for modifier in [x for x in obj.modifiers if x.type == "NODES"]:
                        if modifier.node_group is None:
                            continue
                        if modifier.node_group.name != "Smooth by Angle":
                            continue
                        modifier.show_viewport = status

                if self.enable_simplify:
                    status = get_status_norm_autosmooth(obj)
                    obj.MustardSimplify_Status.normals_auto_smooth = status
                    update_norm_autosmooth(obj, False)
                    if addon_prefs.debug:
                        print("Normals Auto Smooth disabled (previous status: " + str(status) + ").")
                else:
                    status = obj.MustardSimplify_Status.normals_auto_smooth
                    update_norm_autosmooth(obj, status)
                    if addon_prefs.debug:
                        print("Normals Auto Smooth reverted to status: " + str(status) + ".")

        # SCENE
        if settings.physics:

            # Rigid Body World
            if context.scene.rigidbody_world:

                if addon_prefs.debug:
                    print("\n ----------- Scene: " + scene.name + " -----------")

                if self.enable_simplify:
                    status = scene.rigidbody_world.enabled
                    scene.MustardSimplify_Status.rigidbody_world = status
                    scene.rigidbody_world.enabled = False
                    if addon_prefs.debug:
                        print("Rigid Body World disabled (previous status: " + str(status) + ").")
                else:
                    scene.rigidbody_world.enabled = scene.MustardSimplify_Status.rigidbody_world
                    if addon_prefs.debug:
                        print("Rigid Body World disabled reverted to status: " + str(
                            scene.rigidbody_world.enabled) + ").")

        # DRIVERS
        if settings.drivers:
            collections = ["scenes", "objects", "meshes", "materials", "textures", "speakers",
                           "worlds", "curves", "armatures", "particles", "lattices", "shape_keys", "lights", "cameras"]
            num_drivers = 0

            for col in collections:
                collection = getattr(bpy.data, col)
                if col == "objects":
                    collection = objects
                for ob in collection:
                    if col == "objects":
                        eo = find_exception_obj(scene.MustardSimplify_Exceptions.exceptions, ob)
                    if ob.animation_data is not None:
                        for driver in ob.animation_data.drivers:
                            dp = driver.data_path
                            pp = dp
                            if dp.find("[") != 0:
                                pp = ".%s" % dp
                            resolved = False
                            try:
                                dob = ob.path_resolve(dp)
                                resolved = True
                            except:
                                dob = None

                            if not resolved:
                                try:
                                    dob = getattr(bpy.data, col)[ob.name]
                                    dob = getattr(dob, pp[1:])
                                except:
                                    dob = None

                            idx = driver.array_index
                            if dob is not None and (isinstance(dob, Vector) or isinstance(dob, Color)):
                                pp = "%s[%d]" % (pp, idx)
                            if col == "objects":
                                driver.mute = self.enable_simplify and (eo.drivers if eo is not None else True)
                            else:
                                driver.mute = self.enable_simplify
                            num_drivers = num_drivers + 1

            if addon_prefs.debug and self.enable_simplify:
                print("\n ----------- Drivers disabled: " + str(num_drivers) + " -----------")
            if addon_prefs.debug and not self.enable_simplify:
                print("\n ----------- Drivers reverted: " + str(num_drivers) + " -----------")

        try:
            update_all_execution_time()
            if addon_prefs.debug:
                print("\n Updated modifiers Execution Times.")
        except:
            print("\n Mustard Simplify - An error occurred when updating the execution times")

        if addon_prefs.debug:
            print("\n")

        settings.simplify_status = self.enable_simplify

        if self.enable_simplify:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Enabled.')
        else:
            self.report({'INFO'}, 'Mustard Simplify - Simplify Disabled.')

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_SimplifyScene)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_SimplifyScene)