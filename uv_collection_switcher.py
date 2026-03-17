bl_info = {
    "name": "UV Collection Switcher",
    "author": "Pavel Kruhlei",
    "version": (1, 0, 0),
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
        # Skip the master Scene Collection itself
        if lc.collection.name != context.scene.collection.name:
            lc.exclude = excluded
        for child in lc.children:
            recurse(child)
    recurse(root)


def find_matching_uv(obj, col1_name: str, col2_name: str):
    if not obj or obj.type != 'MESH':
        return None

    c1 = col1_name.lower() if col1_name and col1_name != "NONE" else ""
    c2 = col2_name.lower() if col2_name and col2_name != "NONE" else ""

    for uv in obj.data.uv_layers:
        uv_lower = uv.name.lower()
        match1 = (c1 == "") or (c1 in uv_lower or uv_lower in c1)
        match2 = (c2 == "") or (c2 in uv_lower or uv_lower in c2)
        if match1 and match2:
            return uv

    return None


def apply_setup(context):
    props = context.scene.uvs_props

    main_name = props.main_collection
    second_name = props.second_collection

    selected = set()
    if main_name and main_name != "NONE":
        selected.add(main_name)
    if second_name and second_name != "NONE":
        selected.add(second_name)

    # Exclude all, then include only selected
    set_all_collections_excluded(context, True)
    for name in selected:
        set_collection_excluded(context, name, False)

    # UV matching
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return None, "No active mesh object"

    matched_uv = find_matching_uv(obj, main_name, second_name)
    if matched_uv:
        obj.data.uv_layers.active = matched_uv
        return matched_uv.name, None
    else:
        return None, "No matching UV map found"


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
    """Exclude all collections except selected ones, activate matching UV"""
    bl_idname = "uvs.activate"
    bl_label = "Activate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        uv_name, error = apply_setup(context)
        props = context.scene.uvs_props

        if error:
            props.last_result = ""
            props.last_error = error
            self.report({'WARNING'}, error)
        else:
            props.last_result = uv_name
            props.last_error = ""
            self.report({'INFO'}, f"Active UV: {uv_name}")

        return {'FINISHED'}


class UVS_OT_ActivateAll(Operator):
    """Include all collections in view layer"""
    bl_idname = "uvs.activate_all"
    bl_label = "Activate All Collections"
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
    bl_label = "Disable All Collections"
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
    bl_label = "UV Selector"
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

        # ── UV preview ────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Selected UV:", icon='GROUP_UVS')
        if obj and obj.type == 'MESH':
            matched = find_matching_uv(
                obj,
                props.main_collection,
                props.second_collection,
            )
            if matched:
                box.label(text=matched.name, icon='CHECKMARK')
            else:
                box.label(text="No match found", icon='QUESTION')
        else:
            box.label(text="Select a mesh object", icon='INFO')

        layout.separator()

        # ── Activate button ───────────────────────────────────────────────
        row = layout.row()
        row.scale_y = 1.8
        row.operator("uvs.activate", icon='PLAY')

        # ── Result / error feedback ───────────────────────────────────────
        if props.last_error:
            row2 = layout.row()
            row2.alert = True
            row2.label(text=props.last_error, icon='ERROR')
        elif props.last_result:
            layout.label(text=f"Active: {props.last_result}", icon='CHECKMARK')

        layout.separator()

        # ── Utility buttons ───────────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("uvs.activate_all", icon='HIDE_OFF')
        row.operator("uvs.disable_all", icon='HIDE_ON')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    UVSProps,
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