# SPDX-FileCopyrightText: 2016-2026, Thomas Larsson
#
# SPDX-License-Identifier: GPL-2.0-or-later

from random import random

import bpy
import numpy as np


class SimpleOperatorState:
    def store_state(self, context):
        self._active = context.view_layer.objects.active
        self._selected = [ob for ob in context.selected_objects]

    def restore_state(self, context):
        for ob in context.view_layer.objects:
            ob.select_set(False)

        for ob in self._selected:
            if ob.name in bpy.data.objects:
                ob.select_set(True)

        if self._active and self._active.name in bpy.data.objects:
            context.view_layer.objects.active = self._active


def move_objects_to_collection(objs, coll):
    for ob in objs:
        # unlink from all current collections
        for c in list(ob.users_collection):
            c.objects.unlink(ob)

        coll.objects.link(ob)


def update_scene(context):
    context.evaluated_depsgraph_get().update()


def lock_all_transforms(ob):
    ob.lock_location = (True, True, True)
    ob.lock_rotation = (True, True, True)
    ob.lock_scale = (True, True, True)


def strip_name(name):
    words = name.rsplit(".", 1)
    if len(words) == 2 and len(words[1]) >= 3 and words[1].isdigit():
        name = words[0]

    words = name.rsplit("-", 1)
    if len(words) == 2 and words[1].isdigit():
        name = words[0]

    return name


def get_selected_meshes(context):
    return [
        ob
        for ob in context.view_layer.objects
        if ob.select_get()
        and ob.type == "MESH"
        and not (ob.hide_get() or ob.hide_viewport)
    ]


def get_selected_objects(context):
    return [
        ob
        for ob in context.view_layer.objects
        if ob.select_get() and not (ob.hide_get() or ob.hide_viewport)
    ]


def get_modifier(ob, mod_type):
    for mod in ob.modifiers:
        if mod.type == mod_type:
            return mod
    return None


def get_collection(context, ob):
    for coll in bpy.data.collections:
        if ob.name in coll.objects.keys():
            return coll
    return context.scene.collection


def create_subcollection(coll, name):
    def recurse(parent):
        for child in parent.children:
            if child.name == name:
                return child

        for child in parent.children:
            found = recurse(child)
            if found:
                return found

        return None

    found = recurse(coll)

    if found:
        return found

    subcoll = bpy.data.collections.new(name)
    coll.children.link(subcoll)
    return subcoll


def enable_all_rig_layers(rig, value=True):
    for coll in rig.data.collections:
        coll.is_visible = value


def get_rig_layers(rig):
    return [(coll, coll.is_visible) for coll in rig.data.collections]


def set_rig_layers(rig, layers):
    for coll, visible in layers:
        coll.is_visible = visible


def activate_object(context, ob):
    if ob is None:
        return False

    try:
        ob.hide_viewport = False
        ob.hide_set(False)

        context.view_layer.objects.active = ob

        if context.object and context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")

        ob.select_set(True)

        return True

    except Exception:
        print(f"Could not activate {ob.name}")
        return False


def set_world_matrix(ob, wmat):
    if ob.parent:
        if ob.parent_type == "BONE":
            pb = ob.parent.pose.bones.get(ob.parent_bone)

            if pb:
                ob.matrix_parent_inverse = pb.matrix.inverted()

        else:
            ob.matrix_parent_inverse = ob.parent.matrix_world.inverted()

    ob.matrix_world = wmat

    ob.location = [x if abs(x) > 1e-6 else 0.0 for x in ob.location]

    ob.rotation_euler = [x if abs(x) > 1e-4 else 0.0 for x in ob.rotation_euler]

    ob.scale = [x if abs(x - 1.0) > 1e-4 else 1.0 for x in ob.scale]


def set_parent(context, ob, rig, bone_name=None, update=True):
    if update:
        update_scene(context)

    if ob.parent == rig:
        return

    world = ob.matrix_world.copy()

    ob.parent = rig

    if bone_name:
        ob.parent_bone = bone_name
        ob.parent_type = "BONE"
    else:
        ob.parent_type = "OBJECT"

    set_world_matrix(ob, world)


def get_material_type(mat):
    skin_materials = {
        "eyelash": "BLACK",
        "eyelashes": "BLACK",
        "eyemoisture": "INVIS",
        "lacrimal": "INVIS",
        "lacrimals": "INVIS",
        "cornea": "INVIS",
        "tear": "INVIS",
        "eyereflection": "INVIS",
        "fingernail": "RED",
        "fingernails": "RED",
        "toenail": "RED",
        "toenails": "RED",
        "lip": "RED",
        "lips": "RED",
        "mouth": "MOUTH",
        "tongue": "MOUTH",
        "innermouth": "MOUTH",
        "gums": "MOUTH",
        "teeth": "WHITE",
        "pupil": "BLACK",
        "pupils": "BLACK",
        "sclera": "WHITE",
        "iris": "BLUE",
        "irises": "BLUE",
        "eye_left": "BLUE",
        "eye_right": "BLUE",
        "highlight": "WHITE",
        "shadow": "SHADOW",
        "skinface": "SKIN",
        "face": "SKIN",
        "head": "SKIN",
        "ears": "SKIN",
        "skinleg": "SKIN",
        "legs": "SKIN",
        "skintorso": "SKIN",
        "torso": "SKIN",
        "body": "SKIN",
        "skinarm": "SKIN",
        "arms": "SKIN",
        "feet": "SKIN",
        "skinhip": "SKIN",
        "hips": "SKIN",
        "shoulders": "SKIN",
        "skinhand": "SKIN",
        "hands": "SKIN",
    }

    name = mat.name.lower().split("-")[0].split(".")[0].split(" ")[0].split("&")[0]

    if name in skin_materials:
        return skin_materials[name]

    name2 = name.rsplit("_", 2)[-1]

    if name2 in skin_materials:
        return skin_materials[name2]

    return "CLOTHES"


def disable_render_deforming_modifiers(ob):
    state = []
    for mod in ob.modifiers:
        # disable only heavy geometry-affecting modifiers
        if mod.type in {"SUBSURF", "MULTIRES", "ARMATURE", "MESH_DEFORM", "SHRINKWRAP"}:
            state.append((mod, mod.show_viewport))
            mod.show_viewport = False
    return state


def restore_modifiers(state):
    for mod, val in state:
        mod.show_viewport = val


class MUSTARDSIMPLIFY_OT_AddProxy(
    bpy.types.Operator,
    SimpleOperatorState,
):
    bl_idname = "mustard_simplify.add_proxy"
    bl_label = "Add Proxys"
    bl_description = "Add proxys to selected meshes"
    bl_options = {"UNDO"}

    headType: bpy.props.EnumProperty(
        items=[
            ("SOLID", "Solid", "Solid head"),
            ("JAW", "Jaw", "Head with jaws and eyes"),
            ("FULL", "Full", "Head with all face bones"),
        ],
        name="Head Type",
        default="JAW",
    )

    mannColl: bpy.props.StringProperty(
        name="Proxy Collection",
        default="Proxy",
    )

    useNormals: bpy.props.BoolProperty(
        name="Normals",
        default=False,
    )

    useNormalsAutoSmooth: bpy.props.BoolProperty(
        name="Auto Smooth Normals",
        default=True,
    )

    useVertexGroups: bpy.props.BoolProperty(
        name="Vertex Groups",
        default=False,
    )

    useVertexColors: bpy.props.BoolProperty(
        name="Vertex Colors",
        default=False,
    )

    useUvLayers: bpy.props.BoolProperty(
        name="UV Layers",
        default=True,
    )

    ignoreBoneGroups: bpy.props.BoolProperty(
        name="Ignore Bone Groups",
        default=False,
    )

    threshold: bpy.props.FloatProperty(
        name="Threshold",
        min=0.0,
        max=1.0,
        precision=4,
        default=1e-3,
    )

    useOriginalArmature: bpy.props.BoolProperty(
        name="Use Original Armature",
        description="Do not duplicate armature, and use the existing one",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(
            text="This tool creates a proxy armature to increase viewport performance.",
            icon="ARMATURE_DATA",
        )
        col.label(
            text="To get the full benefits, disable the original Collection in "
            "Viewport,",
            icon="BLANK1",
        )
        col.label(text="and use the proxy one instead.", icon="BLANK1")
        col.label(
            text="It is important to disable the Collection with the Checkbox button,",
            icon="CHECKBOX_HLT",
        )
        col.label(
            text="not just hide the original Objects, to avoid Blender still "
            "processing ",
            icon="BLANK1",
        )
        col.label(text="them in the Viewport.", icon="BLANK1")

        box = layout.box()
        box.label(text="Settings", icon="MODIFIER")
        box.prop(self, "useOriginalArmature")
        box.prop(self, "mannColl")
        box.prop(self, "headType")
        box.prop(self, "useNormalsAutoSmooth")

        box = layout.box()
        box.label(text="Transfer", icon="MOD_DATA_TRANSFER")
        col = box.column(align=True)
        col.prop(self, "useUvLayers")
        col.prop(self, "useNormals")
        col.prop(self, "useVertexColors")
        col.prop(self, "useVertexGroups")

        if self.useVertexGroups:
            col.prop(self, "ignoreBoneGroups")
            col.prop(self, "threshold")

    def invoke(self, context, event):
        if context.object:
            name = strip_name(context.object.name)

            if name.endswith(" Mesh"):
                name = name[:-5]

            self.mannColl = f"{name} Proxy"

        return context.window_manager.invoke_props_dialog(self, width=390)

    def execute(self, context):
        self.store_state(context)

        try:
            self.run(context)

        finally:
            self.restore_state(context)

        return {"FINISHED"}

    def run(self, context):
        selected = get_selected_objects(context)

        meshes = get_selected_meshes(context)

        if not meshes:
            self.report({"ERROR"}, "Mustard Simplify - Select at least one mesh")
            self.restore_state(context)
            return {"CANCELLED"}

        ob = context.object

        if not ob:
            self.report({"ERROR"}, "Mustard Simplify - No active object")
            return {"CANCELLED"}

        rig = ob.parent

        if not rig or rig.type != "ARMATURE":
            self.report(
                {"ERROR"},
                "Mustard Simplify - Active mesh must have an armature parent",
            )
            return {"CANCELLED"}

        # Ensure at least one selected mesh has deform-bone vertex groups
        valid_meshes = []

        for mob in meshes:
            has_deform_group = False

            for vgrp in mob.vertex_groups:
                bone = rig.data.bones.get(vgrp.name)

                if bone and bone.use_deform:
                    has_deform_group = True
                    break

            if has_deform_group:
                valid_meshes.append(mob)

        if not valid_meshes:
            self.report(
                {"ERROR"},
                "Mustard Simplify - Selected meshes have no deform-bone vertex groups",
            )
            return {"CANCELLED"}

        meshes = valid_meshes

        if self.useOriginalArmature:
            new_rig = rig
        else:
            new_rig = rig.copy()
            new_rig.data = rig.data.copy()
            new_rig.name = f"{rig.name} Proxy"
            context.scene.collection.objects.link(new_rig)

        old_layers = get_rig_layers(rig)
        old_pose = rig.data.pose_position

        enable_all_rig_layers(rig)
        if not self.useOriginalArmature:
            rig.data.pose_position = "REST"

        # Save modifiers before creating the proxy, to avoid issues with
        # transfers
        mod_state = disable_render_deforming_modifiers(ob) if ob else None

        try:
            scene_coll = context.scene.collection

            # Root collection
            root_coll = create_subcollection(
                scene_coll,
                f"{self.mannColl} Root",
            )

            root_coll.objects.link(new_rig)

            # Child collections
            manncoll = create_subcollection(root_coll, self.mannColl)

            generated = {}

            for ob in meshes:
                masks = []

                for mod in ob.modifiers:
                    if mod.type == "MASK":
                        masks.append((mod, mod.vertex_group))
                        mod.vertex_group = ""

                generated[ob.name] = self.add_proxy(
                    context,
                    ob,
                    new_rig,
                    manncoll,
                )

                for mod, group in masks:
                    mod.vertex_group = group

            for ob in get_selected_objects(context):
                ob.select_set(ob in selected)

            if (
                self.useNormals
                or self.useVertexGroups
                or self.useVertexColors
                or self.useUvLayers
            ):
                bone_names = rig.data.bones.keys() if self.ignoreBoneGroups else []

                for src in meshes:
                    self.transfer_data(
                        context,
                        src,
                        generated[src.name],
                        bone_names,
                    )

            if not self.useOriginalArmature:
                context.scene.collection.objects.unlink(new_rig)

        finally:
            restore_modifiers(mod_state) if mod_state else None
            set_rig_layers(rig, old_layers)
            rig.data.pose_position = old_pose

    def add_proxy(self, context, ob, rig, coll):
        faceverts = [list(f.vertices) for f in ob.data.polygons]

        vertfaces = {vn: [] for vn in range(len(ob.data.vertices))}

        for fn, verts in enumerate(faceverts):
            for vn in verts:
                vertfaces[vn].append(fn)

        majors = {}
        skip = []

        for vgrp in ob.vertex_groups:
            bone = rig.data.bones.get(vgrp.name)

            if bone and bone.use_deform:
                majors[vgrp.index] = []

            else:
                skip.append(vgrp.index)

        for v in ob.data.vertices:
            best_weight = 1e-3
            best_group = None

            for g in v.groups:
                if g.weight > best_weight and g.group not in skip:
                    best_weight = g.weight
                    best_group = g.group

            if best_group is not None:
                majors[best_group].append(v)

        special = {
            "SOLID": ["head"],
            "JAW": ["head", "lowerjaw", "leye", "reye"],
            "FULL": [],
        }

        def remap_bones(bone, remap):
            if bone.name.lower() in special[self.headType]:
                if bone.name in ob.vertex_groups.keys():
                    remap = ob.vertex_groups[bone.name].index

            elif remap is not None:
                if bone.name in ob.vertex_groups.keys():
                    gn = ob.vertex_groups[bone.name].index

                    if gn in majors:
                        majors[remap] += majors[gn]
                        del majors[gn]

            for child in bone.children:
                remap_bones(child, remap)

        for root in [b for b in rig.data.bones if b.parent is None]:
            remap_bones(root, None)

        mob = ob.evaluated_get(context.evaluated_depsgraph_get())

        face_mats = {}

        if ob.data.materials:
            for rnd in range(3, 8):
                face_mats[rnd] = {}

                for f in mob.data.polygons:
                    try:
                        mat = ob.material_slots[f.material_index].material

                    except IndexError:
                        continue

                    nn = tuple(round(x, rnd) for x in f.normal)

                    face_mats[rnd][nn] = mat

        default_material = None
        generated = []

        for vgrp in ob.vertex_groups:
            if vgrp.name not in rig.pose.bones.keys() or vgrp.index not in majors:
                continue

            fnums = []

            for v in majors[vgrp.index]:
                fnums.extend(vertfaces[v.index])

            fnums = list(set(fnums))

            nverts = []
            nfaces = []

            for fn in fnums:
                f = ob.data.polygons[fn]

                nverts.extend(f.vertices)
                nfaces.append(f.vertices)

            if not nfaces:
                continue

            nverts = sorted(set(nverts))

            bone = rig.data.bones[vgrp.name]
            head = bone.head_local

            obverts = mob.data.vertices

            verts = [obverts[vn].co - head for vn in nverts]

            assoc = {vn: n for n, vn in enumerate(nverts)}

            faces = [[assoc[vn] for vn in fverts] for fverts in nfaces]

            name = f"{ob.name[:3]}_{vgrp.name}"

            me = bpy.data.meshes.new(name)
            me.from_pydata(verts, [], faces)

            nob = bpy.data.objects.new(name, me)

            coll.objects.link(nob)

            nob.location = head

            lock_all_transforms(nob)

            if face_mats:
                for f in me.polygons:
                    fmat = None

                    for rnd in reversed(range(3, 8)):
                        fmat = face_mats[rnd].get(
                            tuple(round(x, rnd) for x in f.normal)
                        )

                        if fmat:
                            break

                    if not fmat:
                        if default_material is None:
                            mat = bpy.data.materials.new(f"{ob.name}_Proxy")

                            default_material = mat

                            mat.diffuse_color[0:3] = (
                                random(),
                                random(),
                                random(),
                            )

                            for omat in ob.data.materials:
                                if omat:
                                    mat.diffuse_color = omat.diffuse_color

                                    if get_material_type(omat) == "SKIN":
                                        break

                        fmat = default_material

                    if fmat.name not in me.materials:
                        me.materials.append(fmat)

                    for i, mat_slot in enumerate(nob.material_slots):
                        if mat_slot.material == fmat:
                            f.material_index = i
                            break

            generated.append((nob, bone))

        update_scene(context)

        result = []

        for nob, bone in generated:
            set_parent(
                context,
                nob,
                rig,
                bone.name,
                update=False,
            )

            result.append(nob)

        return result

    def transfer_data(self, context, ob, nobs, bone_names):
        print(f"Transfer data from {ob.name} to {len(nobs)} meshes")

        activate_object(context, ob)

        for nob in nobs:
            nob.select_set(True)

        transfer = bpy.ops.object.data_transfer

        # Normals
        if self.useNormals:
            for poly in ob.data.polygons:
                poly.use_smooth = True

            try:
                transfer(data_type="CUSTOM_NORMAL")
            except Exception as e:
                print("Mustard Simplify - Failed to transfer normals:", e)
                pass

        # Vertex groups
        if ob.vertex_groups and self.useVertexGroups:
            transfer(
                data_type="VGROUP_WEIGHTS",
                layers_select_src="ALL",
                layers_select_dst="NAME",
            )

            for nob in nobs:
                nverts = len(nob.data.vertices)

                weights = {
                    gn: np.zeros(nverts, dtype=float)
                    for gn in range(len(nob.vertex_groups))
                }

                valid = [
                    (gn, vgrp.name)
                    for gn, vgrp in enumerate(nob.vertex_groups)
                    if vgrp.name not in bone_names
                ]

                for v in nob.data.vertices:
                    for g in v.groups:
                        weights[g.group][v.index] = g.weight

                for vgrp in list(nob.vertex_groups):
                    nob.vertex_groups.remove(vgrp)

                for gn, name in valid:
                    cweights = weights[gn]

                    cweights[cweights > 1] = 1
                    cweights[cweights < self.threshold] = 0

                    nonzero = np.nonzero(cweights)[0].astype(int)

                    if len(nonzero) > 0:
                        vgrp = nob.vertex_groups.new(name=name)

                        for vn in nonzero:
                            vgrp.add(
                                [int(vn)],
                                cweights[vn],
                                "REPLACE",
                            )

        # Vertex colors
        if self.useVertexColors:
            transfer(
                data_type="COLOR_VERTEX",
                layers_select_src="ALL",
                layers_select_dst="NAME",
            )

            transfer(
                data_type="COLOR_CORNER",
                layers_select_src="ALL",
                layers_select_dst="NAME",
            )

        # UVs
        if ob.data.uv_layers and self.useUvLayers:
            transfer(
                data_type="UV",
                layers_select_src="ALL",
                layers_select_dst="NAME",
            )

        if self.useNormalsAutoSmooth:
            for nob in nobs:
                me = nob.data

                for poly in me.polygons:
                    poly.use_smooth = True

                if hasattr(me, "free_normals_split"):
                    me.free_normals_split()

                me.update()


def register():
    bpy.utils.register_class(MUSTARDSIMPLIFY_OT_AddProxy)


def unregister():
    bpy.utils.unregister_class(MUSTARDSIMPLIFY_OT_AddProxy)
