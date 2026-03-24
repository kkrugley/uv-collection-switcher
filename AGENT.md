# UV Collection Switcher — CLAUDE.md

## Project Overview

Blender addon for texture baking pipelines. Automates UV map creation, collection visibility
switching, and active UV activation when baking a base mesh against different overlay collections.

**Concrete use case:** Eyewear visualization. A glasses frame (main collection) gets baked against
different decorative front masks (secondary collections). Each combination requires specific
collections visible and a matching UV map active on every mesh. The addon handles this in one click.

## Architecture

Single-file Blender addon: `uv_collection_switcher.py`

### Key Blender Concepts

- **View Layer Collections**: Each collection can be excluded via `layer_collection.exclude`.
  Excluded collections don't render or bake. This is separate from object/collection visibility.
- **UV Layers**: Mesh objects have multiple UV maps (`obj.data.uv_layers`). One is active at a
  time; baking uses the active UV. Two flags matter: `active` (selected in list) and
  `active_render` (camera icon, used by the bake engine).
- **Scene Collection**: `bpy.context.scene.collection` is the master collection — always present,
  always skipped when bulk-excluding children (see `set_all_collections_excluded`).
- **PropertyGroup on Scene**: All addon state lives in `context.scene.uvs_props` (`UVSProps`).

### Module Structure (`uv_collection_switcher.py`)

| Section         | Responsibility                                                                 |
|-----------------|--------------------------------------------------------------------------------|
| Helpers (L17–77)| Pure functions: collection lookup, exclude/include, UV lookup, mesh collection |
| Properties (L83–99) | `UVSProps` PropertyGroup: `main_collection`, `second_collection`, `last_result`, `last_error`, `show_uv_list` |
| Operators (L105–301) | `UVS_OT_AddUVMaps`, `UVS_OT_Activate`, `UVS_OT_ActivateAll`, `UVS_OT_DisableAll`, `UVS_OT_ToggleUVList`, `UVS_OT_DeleteUVMap` |
| Panel (L307–432)| `UVS_PT_MainPanel` — sidebar UI with UV preview and feedback                   |
| Registration (L440–460) | `register()` / `unregister()` + `classes` tuple                        |

## Key Conventions

- **"NONE" sentinel**: Both dropdowns default to `("NONE", "— none —", "")`. Code checks
  `col_name != "NONE"` before using a collection name.
- **UV matching (exact name)**: `find_matching_uv` uses `obj.data.uv_layers.get(col_name)` —
  exact string match. UV maps must be named exactly after their collection.
- **Collect meshes before excluding**: `UVS_OT_Activate` gathers all meshes and activates their
  UV maps *before* calling `set_all_collections_excluded`. After exclusion, collection objects
  may become inaccessible. Do not change this order.
- **Exclude-then-include**: `UVS_OT_Activate` always excludes everything first, then re-includes
  only the selected collections.
- **`active_render` flag**: When activating a UV map, both `obj.data.uv_layers.active = uv` and
  `uv.active_render = True` must be set. The bake engine uses `active_render`; the UI selection
  uses `active`.
- **Clear active_render before setting**: Before setting `active_render = True` on a new UV,
  all existing UV layers must have `active_render = False` to ensure the camera icon switches properly.
- **Operators use `{'REGISTER', 'UNDO'}`**: all state changes are undoable.
- **Enum items are dynamic**: `get_all_collections_items` is called by Blender at draw time,
  returning current `bpy.data.collections`. Do not cache this list.
- **Recursive mesh collection**: `get_all_meshes_in_collection_recursive` traverses child
  collections. `get_all_meshes_in_collection` is flat (direct objects only).
- **Properties stored on Scene**: access via `context.scene.uvs_props`, not globally.
- **Feedback via `last_result` / `last_error`**: mutually exclusive string properties. Set one,
  clear the other. Panel checks `last_error` first (shown with `row.alert = True`), then
  `last_result`.

## Operator Summary

| Operator              | `bl_idname`        | What it does                                                   |
|-----------------------|--------------------|----------------------------------------------------------------|
| `UVS_OT_AddUVMaps`   | `uvs.add_uv_maps`  | Creates UV maps on all meshes. Each collection's meshes get only their own named UV map. |
| `UVS_OT_Activate`    | `uvs.activate`     | Clears UV maps on main collection meshes, adds and activates UV for selected 2nd collection, activates UV on 2nd collection meshes, excludes all other collections. |
| `UVS_OT_ActivateAll` | `uvs.activate_all` | Sets `exclude=False` on all collections.                       |
| `UVS_OT_DisableAll`  | `uvs.disable_all`  | Sets `exclude=True` on all collections.                        |
| `UVS_OT_ToggleUVList`| `uvs.toggle_uv_list` | Shows/hides list of all UV maps with delete options.         |
| `UVS_OT_DeleteUVMap` | `uvs.delete_uv_map` | Deletes a UV map from all meshes in all collections.          |

## UV Activation Logic (UVS_OT_Activate)

1. Collects meshes from `main_collection` and `second_collection`
2. **Main collection meshes**: Clears all UV maps, creates UV named after `second_collection`, activates it
3. **2nd collection meshes**: Finds UV named after `second_collection`, activates it
4. Excludes all collections, includes only selected ones
5. Selects all meshes from both collections

## Testing

No automated tests — `bpy` is only available inside Blender. Manual testing procedure:

1. Install addon: **Edit → Preferences → Add-ons → Install**, select `uv_collection_switcher.py`
2. Enable the addon checkbox
3. Open **View3D → Sidebar (N) → UV Switcher** tab
4. Test with a scene that has:
   - At least two collections with mesh objects
   - UV maps created via **Add UVs for all Collections** button
5. Select main and 2nd collections, press **Activate**
6. Verify camera icon (active_render) is set on correct UV map for meshes in both collections
7. Reload after code changes: Scripting workspace → open file → **Run Script**
   (or use an addon reload shortcut)

## Meta

- Version: 2.0.0
- Author: Pavel Kruhlei
- Blender: 3.0+
