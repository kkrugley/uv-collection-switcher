# UV Collection Switcher

Blender addon that automates collection visibility and UV map activation for texture baking pipelines — one click instead of manual switching before every bake.

## Problem

A common baking workflow: one main mesh, baked against different combinations of mask meshes. Before each bake you need to:

1. Exclude irrelevant collections from the view layer
2. Include only the right collections
3. Activate the matching UV map on the main mesh

Doing this by hand before every bake is slow and easy to get wrong.

## Solution

Pick two collections from dropdowns → press **Activate**. The addon excludes everything else, includes your selection, and activates the matching UV map automatically.

## Features

- Two collection dropdowns (main + mask/secondary)
- **UV Preview** — shows which UV map will be activated *before* you press the button
- **Activate** — excludes all other collections, includes selected ones, activates matching UV
- **Activate All / Disable All** — quickly toggle all collection visibility
- Error feedback when no matching UV map is found
- Compatible with SimpleBake (run baking manually after activation)
- Undo support

## Installation

1. Download `uv_collection_switcher.py`
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the downloaded `.py` file
4. Enable **UV Collection Switcher** by checking its box

## Usage

Open **View3D → Sidebar (N key) → UV Switcher** tab.

1. Choose your **Main Collection** from the first dropdown
2. Choose the **2nd Collection** (mask) from the second dropdown
3. The preview box shows which UV map will be activated
4. Press **Activate**
5. Run your bake (e.g., via SimpleBake)

### UV Map Naming Convention

UV matching uses case-insensitive substring search. If a collection is named `BrickWall_Mask`,
any UV map whose name contains `brickwall_mask` (or vice versa) will match.

**Example:**

| Collection name | UV map name      | Match? |
|-----------------|------------------|--------|
| `Wall`          | `UV_Wall_Detail` | ✓      |
| `Wall`          | `UV_Floor`       | ✗      |
| `Mask_AO`       | `ao_mask_01`     | ✓      |

### Utility Buttons

- **Activate All Collections** — re-include all collections (undo exclusions)
- **Disable All Collections** — exclude all collections from the view layer

## Requirements

- Blender 3.0 or newer
- Python 3.x (bundled with Blender)

## Planned

- Auto-create missing UV maps on meshes in the main collection, named after mask collections
- UVPackmaster3 integration

## Author

Pavel Kruhlei — v1.0.0
