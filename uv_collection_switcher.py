bl_info = {
    "name": "Collection Switcher",
    "author": "Pavel Kruhlei",
    "version": (3, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Collection Switcher",
    "description": "Select collections and exclude the rest from view layer",
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
    return [obj for obj in col.objects if obj.type == "MESH"]


def get_all_meshes_in_collection_recursive(col):
    """Return all mesh objects in a collection and all its children."""
    meshes = list(get_all_meshes_in_collection(col))
    for child in col.children:
        meshes.extend(get_all_meshes_in_collection_recursive(child))
    return meshes


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


class UVS_OT_Activate(Operator):
    """Exclude all collections except selected ones and select all meshes"""

    bl_idname = "uvs.activate"
    bl_label = "Activate"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.uvs_props
        main_name = props.main_collection
        second_name = props.second_collection

        if main_name == "NONE" and second_name == "NONE":
            props.last_error = "Select at least one collection"
            props.last_result = ""
            self.report({"WARNING"}, props.last_error)
            return {"CANCELLED"}

        selected_names = set()
        if main_name != "NONE":
            selected_names.add(main_name)
        if second_name != "NONE":
            selected_names.add(second_name)

        main_meshes = []
        second_meshes = []

        if main_name != "NONE":
            main_col = bpy.data.collections.get(main_name)
            if main_col:
                main_meshes = get_all_meshes_in_collection_recursive(main_col)

        if second_name != "NONE":
            second_col = bpy.data.collections.get(second_name)
            if second_col:
                second_meshes = get_all_meshes_in_collection_recursive(second_col)

        all_meshes = main_meshes + second_meshes

        set_all_collections_excluded(context, True)
        for name in selected_names:
            set_collection_excluded(context, name, False)

        bpy.ops.object.select_all(action="DESELECT")
        first_mesh = None
        for obj in all_meshes:
            obj.select_set(True)
            if first_mesh is None:
                first_mesh = obj

        if first_mesh:
            context.view_layer.objects.active = first_mesh

        props.last_result = main_name if main_name != "NONE" else second_name
        props.last_error = ""
        self.report(
            {"INFO"}, f"Active: {props.last_result} | Selected {len(all_meshes)} meshes"
        )

        return {"FINISHED"}


class UVS_OT_ActivateAll(Operator):
    """Include all collections in view layer"""

    bl_idname = "uvs.activate_all"
    bl_label = "Activate All"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        set_all_collections_excluded(context, False)
        context.scene.uvs_props.last_result = ""
        context.scene.uvs_props.last_error = ""
        self.report({"INFO"}, "All collections activated")
        return {"FINISHED"}


class UVS_OT_DisableAll(Operator):
    """Exclude all collections from view layer"""

    bl_idname = "uvs.disable_all"
    bl_label = "Disable All"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        set_all_collections_excluded(context, True)
        context.scene.uvs_props.last_result = ""
        context.scene.uvs_props.last_error = ""
        self.report({"INFO"}, "All collections disabled")
        return {"FINISHED"}


class UVS_OT_DeleteAllUVMaps(Operator):
    """Delete all UV maps from all meshes"""

    bl_idname = "uvs.delete_all_uv_maps"
    bl_label = "Delete All UV Maps"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        removed = 0
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                while obj.data.uv_layers:
                    obj.data.uv_layers.remove(obj.data.uv_layers[0])
                    removed += 1
        self.report({"INFO"}, f"Removed {removed} UV maps")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------


class UVS_PT_MainPanel(Panel):
    bl_label = "Collection Switcher"
    bl_idname = "UVS_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Collection Switcher"

    def draw(self, context):
        layout = self.layout
        props = context.scene.uvs_props

        layout.label(text="Main collection:", icon="OUTLINER_COLLECTION")
        layout.prop(props, "main_collection", text="")

        layout.separator()

        layout.label(text="2nd collection:", icon="OUTLINER_COLLECTION")
        layout.prop(props, "second_collection", text="")

        layout.separator()

        row = layout.row()
        row.scale_y = 1.8
        row.operator("uvs.activate", icon="PLAY")

        if props.last_error:
            row2 = layout.row()
            row2.alert = True
            row2.label(text=props.last_error, icon="ERROR")
        elif props.last_result:
            layout.label(text=f"Active: {props.last_result}", icon="CHECKMARK")

        layout.separator()

        row = layout.row(align=True)
        row.operator("uvs.activate_all", icon="HIDE_OFF")
        row.operator("uvs.disable_all", icon="HIDE_ON")

        layout.separator()

        layout.operator("uvs.delete_all_uv_maps", icon="X", text="Delete All UV Maps")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    UVSProps,
    UVS_OT_Activate,
    UVS_OT_ActivateAll,
    UVS_OT_DisableAll,
    UVS_OT_DeleteAllUVMaps,
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
