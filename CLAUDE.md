# UV Collection Switcher — CLAUDE.md

## Project Overview

Blender addon for texture baking pipeline. Automates switching between collection visibility
combinations and active UV maps when baking a main mesh against different mask mesh combinations.

**Use case:** One main mesh gets baked against different combinations of mask meshes. Each
combination needs specific collections visible and a matching UV map active. This addon does
that in one click.

## Architecture

Single-file Blender addon: `uv_collection_switcher.py`

### Key Blender Concepts

- **View Layer Collections**: Each collection can be excluded from the view layer via
  `layer_collection.exclude`. This is separate from object/collection visibility — excluded
  collections don't render or bake.
- **UV Layers**: Mesh objects have multiple UV maps (`obj.data.uv_layers`). Only one is active
  at a time; baking uses the active UV map.
- **Scene Collection**: `bpy.context.scene.collection` is the master collection — it is always
  present and is skipped when excluding all children (see `set_all_collections_excluded`).
- **PropertyGroup on Scene**: All addon state lives in `context.scene.uvs_props` (type `UVSProps`).

### Module Structure (`uv_collection_switcher.py`)

| Lines     | Section       | Responsibility                                                        |
|-----------|---------------|-----------------------------------------------------------------------|
| 20–71     | Helpers        | Pure functions: collection lookup, exclude/include, UV matching      |
| 108–118   | Properties     | `UVSProps` PropertyGroup (main_collection, second_collection, feedback) |
| 125–172   | Operators      | `UVS_OT_Activate`, `UVS_OT_ActivateAll`, `UVS_OT_DisableAll`        |
| 179–240   | Panel          | `UVS_PT_MainPanel` — sidebar UI                                      |
| 246–268   | Registration   | `register()` / `unregister()` + `classes` tuple                      |

## Key Conventions

- **"NONE" sentinel**: Both dropdowns default to `("NONE", "— none —", "")`. Code checks
  `col_name != "NONE"` before using a collection name.
- **UV matching (substring, case-insensitive)**: `find_matching_uv` matches if either string
  is a substring of the other. Both collection names must match (empty = wildcard).
  ```python
  match1 = (c1 == "") or (c1 in uv_lower or uv_lower in c1)
  ```
- **Exclude-then-include**: `apply_setup` always excludes everything first, then re-includes
  only the selected collections. Do not change this order.
- **Operators use `{'REGISTER', 'UNDO'}`**: all state changes are undoable.
- **Enum items are dynamic**: `get_all_collections_items` is called by Blender at draw time,
  returning current `bpy.data.collections`. Do not cache this list.
- **Properties stored on Scene**: access via `context.scene.uvs_props`, not globally.

## Testing

No automated tests — `bpy` is only available inside Blender. Manual testing procedure:

1. Install addon: **Edit → Preferences → Add-ons → Install**, select `uv_collection_switcher.py`
2. Enable the addon checkbox
3. Open **View3D → Sidebar (N) → UV Switcher** tab
4. Test with a scene that has:
   - At least two collections with mesh objects
   - An active mesh object with multiple UV maps named after the collections
5. Reload after code changes: Scripting workspace → open file → **Run Script**
   (or use an addon reload shortcut like [Reload Scripts](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html))

## Planned Features

- **Auto UV creation**: Automatically create missing UV maps on meshes in the main collection,
  naming them after mask-collection names
- **UVPackmaster3 integration**: Possible future integration with UVPackmaster3 for UV packing
  after setup

## Meta

- Version: 1.0.0
- Author: Pavel Kruhlei
- Blender: 3.0+
- Compatible with: SimpleBake (baking triggered manually after activation)
