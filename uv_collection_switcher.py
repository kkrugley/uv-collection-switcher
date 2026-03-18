bl_info = {
    "name": "UV Collection Switcher",
    "author": "Pavel Kruhlei",
    "version": (1, 2, 4),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > UV Switcher",
    "description": "Select collections, activate matching UV map and exclude the rest from view layer",
    "category": "Object",
}

import bpy
from bpy.props import StringProperty, EnumProperty
from bpy.types import Panel, Operator, PropertyGroup
from bpy.utils import register_class, unregister_class


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_all_collections_items(self, context):
    items = [("NONE", "— none —", "")]
    for col in bpy.data.collections:
        items.append((col.name, col.name, ""))
    return items


def find_layer_collection(layer_col, name):
    """Recursively find a layer collection by collection name."""
    if layer_col.collection.name == name:
        return layer_col
    for child in layer_col.children:
        result = find_layer_collection(child, name)
        if result:
            return result
    return None


def set_collection_excluded(context, col_name, excluded: bool):
    root = context.view_layer.layer_collection
    lc = find_layer_collection(root, col_name)
    if lc:
        lc.exclude = excluded


def set_all_collections_excluded(context, excluded: bool):
    root = context.view_layer.layer_collection
    def recurse(lc):
        if lc.collection.name != context.scene.collection.name:
            lc.exclude = excluded
        for child in lc.children:
            recurse(child)
    recurse(root)


def get_all_meshes_in_collection(col):
    """Return all mesh objects directly in a collection (non-recursive)."""
    return [obj for obj in col.objects if obj.type == 'MESH']


def get_all_meshes_in_collection_recursive(col):
    """Return all mesh objects in a collection and all its children."""
    meshes = list(get_all_meshes_in_collection(col))
    for child in col.children:
        meshes.extend(get_all_meshes_in_collection_recursive(child))
    return meshes


def find_matching_uv(obj, col_name: str):
    """Find UV map on obj whose name exactly matches col_name."""
    if not obj or obj.type != 'MESH':
        return None
    return obj.data.uv_layers.get(col_name)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class UVSProps(PropertyGroup):
    main_collection: EnumProperty(
        name="Main Collection",
        items=get_all_collections_items,
    )
    second_collection: EnumProperty(
        name="2nd Collection",
        items=get_all_collections_items,
    )
    last_result: StringProperty(default="")
    last_error: StringProperty(default="")


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class UVS_OT_AddUVMaps(Operator):
    """Add UV maps for selected collections only.\nMain collection gets a UV map named after the 2nd collection.\n2nd collection gets a UV map named after itself.\nEach UV map is named after the 2nd collection."""
    bl_idname = "uvs.add_uv_maps"
    bl_label = "Add UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        created = 0
        skipped = 0

        props = context.scene.uvs_props
        main_col_name = props.main_collection
        second_col_name = props.second_collection

        if main_col_name == "NONE" and second_col_name == "NONE":
            self.report({'WARNING'}, "Select at least one collection")
            return {'CANCELLED'}

        # Determine which UV name to add (named after the 2nd collection, or main if no 2nd)
        uv_name = second_col_name if second_col_name != "NONE" else main_col_name

        # Build list of (collection, uv_names_to_add) pairs
        work = []
        if main_col_name != "NONE":
            main_col = bpy.data.collections.get(main_col_name)
            if main_col:
                # Main gets UV named after 2nd (or itself if no 2nd selected)
                work.append((main_col, {uv_name}))
        if second_col_name != "NONE":
            second_col = bpy.data.collections.get(second_col_name)
            if second_col:
                # 2nd collection gets UV named after itself
                work.append((second_col, {second_col_name}))

        for col, uv_names in work:
            meshes = get_all_meshes_in_collection_recursive(col)
            for obj in meshes:
                for name in uv_names:
                    if obj.data.uv_layers.get(name) is None:
                        obj.data.uv_layers.new(name=name)
                        created += 1
                    else:
                        skipped += 1

        msg = f"Created {created} UV maps, {skipped} already existed"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class UVS_OT_Activate(Operator):
    """Exclude all collections except selected ones,\nactivate matching UV map and select all meshes"""
    bl_idname = "uvs.activate"
    bl_label = "Activate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.uvs_props
        main_name = props.main_collection
        second_name = props.second_collection

        # ── Validate ──────────────────────────────────────────────────────
        if main_name == "NONE" and second_name == "NONE":
            props.last_error = "Select at least one collection"
            props.last_result = ""
            self.report({'WARNING'}, props.last_error)
            return {'CANCELLED'}

        selected_names = set()
        if main_name != "NONE":
            selected_names.add(main_name)
        if second_name != "NONE":
            selected_names.add(second_name)

        # ── Collect meshes and activate UV BEFORE excluding collections ────
        uv_target = second_name if second_name != "NONE" else main_name

        uv_found = False
        all_meshes = []

        for name in selected_names:
            col = bpy.data.collections.get(name)
            if col:
                all_meshes.extend(get_all_meshes_in_collection_recursive(col))

        # Activate UV on all meshes first (while collections still accessible)
        for obj in all_meshes:
            uv = find_matching_uv(obj, uv_target)
            if uv:
                # Set active for editing (selected in list)
                obj.data.uv_layers.active = uv
                # Set active for rendering/baking (camera icon)
                uv.active_render = True
                uv_found = True

        # ── Now exclude all, include only selected ────────────────────────
        set_all_collections_excluded(context, True)
        for name in selected_names:
            set_collection_excluded(context, name, False)

        # ── Select all meshes in both collections ─────────────────────────
        bpy.ops.object.select_all(action='DESELECT')
        first_mesh = None
        for obj in all_meshes:
            obj.select_set(True)
            if first_mesh is None:
                first_mesh = obj

        if first_mesh:
            context.view_layer.objects.active = first_mesh

        # ── Feedback ──────────────────────────────────────────────────────
        if not uv_found:
            props.last_error = f'No UV "{uv_target}" found on meshes'
            props.last_result = ""
            self.report({'WARNING'}, props.last_error)
        else:
            props.last_result = uv_target
            props.last_error = ""
            self.report({'INFO'}, f"Active UV: {uv_target} | Selected {len(all_meshes)} meshes")

        return {'FINISHED'}


class UVS_OT_RemoveSelectedUVMaps(Operator):
    """Remove UV maps named after selected collections from all meshes in those collections."""
    bl_idname = "uvs.remove_selected_uv_maps"
    bl_label = "Remove UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed = 0
        skipped = 0

        props = context.scene.uvs_props
        main_col_name = props.main_collection
        second_col_name = props.second_collection

        if main_col_name == "NONE" and second_col_name == "NONE":
            self.report({'WARNING'}, "Select at least one collection")
            return {'CANCELLED'}

        # Collect (collection, uv_name_to_remove) pairs
        work = []
        if main_col_name != "NONE":
            main_col = bpy.data.collections.get(main_col_name)
            uv_name = second_col_name if second_col_name != "NONE" else main_col_name
            if main_col:
                work.append((main_col, uv_name))
        if second_col_name != "NONE":
            second_col = bpy.data.collections.get(second_col_name)
            if second_col:
                work.append((second_col, second_col_name))

        for col, uv_name in work:
            meshes = get_all_meshes_in_collection_recursive(col)
            for obj in meshes:
                uv = obj.data.uv_layers.get(uv_name)
                if uv:
                    obj.data.uv_layers.remove(uv)
                    removed += 1
                else:
                    skipped += 1

        msg = f"Removed {removed} UV maps, {skipped} not found"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class UVS_OT_ActivateAll(Operator):
    """Include all collections in view layer"""
    bl_idname = "uvs.activate_all"
    bl_label = "Activate All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        set_all_collections_excluded(context, False)
        context.scene.uvs_props.last_result = ""
        context.scene.uvs_props.last_error = ""
        self.report({'INFO'}, "All collections activated")
        return {'FINISHED'}


class UVS_OT_DisableAll(Operator):
    """Exclude all collections from view layer"""
    bl_idname = "uvs.disable_all"
    bl_label = "Disable All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        set_all_collections_excluded(context, True)
        context.scene.uvs_props.last_result = ""
        context.scene.uvs_props.last_error = ""
        self.report({'INFO'}, "All collections disabled")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class UVS_PT_MainPanel(Panel):
    bl_label = "UV Switcher"
    bl_idname = "UVS_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UV Switcher"

    def draw(self, context):
        layout = self.layout
        props = context.scene.uvs_props
        obj = context.active_object

        # ── Main collection ───────────────────────────────────────────────
        layout.label(text="Main collection:", icon='OUTLINER_COLLECTION')
        layout.prop(props, "main_collection", text="")

        layout.separator()

        # ── 2nd collection ────────────────────────────────────────────────
        layout.label(text="2nd collection:", icon='OUTLINER_COLLECTION')
        layout.prop(props, "second_collection", text="")

        layout.separator()

        # ── Add / Remove UV Maps ──────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("uvs.add_uv_maps", icon='ADD')
        row.operator("uvs.remove_selected_uv_maps", icon='REMOVE')

        layout.separator()

        # ── UV preview ────────────────────────────────────────────────────
        uv_target = props.second_collection if props.second_collection != "NONE" else props.main_collection
        box = layout.box()
        box.label(text="UV to activate:", icon='GROUP_UVS')
        if uv_target and uv_target != "NONE":
            # Check if this UV exists on active object
            if obj and obj.type == 'MESH':
                exists = obj.data.uv_layers.get(uv_target) is not None
                icon = 'CHECKMARK' if exists else 'QUESTION'
                box.label(text=uv_target, icon=icon)
                if not exists:
                    box.label(text="Not found on active object", icon='INFO')
            else:
                box.label(text=uv_target)
        else:
            box.label(text="Select a collection", icon='INFO')

        layout.separator()

        # ── Activate button ───────────────────────────────────────────────
        row = layout.row()
        row.scale_y = 1.8
        row.operator("uvs.activate", icon='PLAY')

        # ── Feedback ──────────────────────────────────────────────────────
        if props.last_error:
            row2 = layout.row()
            row2.alert = True
            row2.label(text=props.last_error, icon='ERROR')
        elif props.last_result:
            layout.label(text=f"Active: {props.last_result}", icon='CHECKMARK')

        layout.separator()

        # ── Utility ───────────────────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("uvs.activate_all", icon='HIDE_OFF')
        row.operator("uvs.disable_all", icon='HIDE_ON')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    UVSProps,
    UVS_OT_AddUVMaps,
    UVS_OT_RemoveSelectedUVMaps,
    UVS_OT_Activate,
    UVS_OT_ActivateAll,
    UVS_OT_DisableAll,
    UVS_PT_MainPanel,
)


def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.uvs_props = bpy.props.PointerProperty(type=UVSProps)


def unregister():
    del bpy.types.Scene.uvs_props
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()