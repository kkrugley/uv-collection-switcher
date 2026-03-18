# UV Collection Switcher

Blender addon for texture baking workflows where one base mesh gets baked against different swappable overlays — one click instead of manually toggling collections and UV maps before every bake.

## The Problem

Concrete use case: eyewear visualization. The base collection is a glasses frame (`Glasses Frame Low-poly`). The secondary collections are decorative front masks — each one snaps over the frame and changes the look completely. To bake a specific frame+mask combination you need:

1. The right collections visible in the viewport
2. The matching UV map active on every mesh
3. All other collections excluded so they don't interfere

Doing this by hand across 8+ variants is slow and error-prone.

## The Solution

Open `N → UV Switcher`, pick your main and secondary collection, press **Activate**. The addon does the rest.

## Features

### Add UVs
Creates a UV map on each mesh in the selected collections, named after the secondary collection. The main collection gets a UV map named after the secondary collection; the secondary collection gets a UV map named after itself. Skips maps that already exist, so it's safe to re-run.

### Remove UVs
Removes UV maps named after the selected collections from all meshes in those collections. The inverse of **Add UVs** — mirrors the same naming logic, so it only removes what **Add UVs** would have created for the current selection.

### Activate
Given a selected main + secondary collection pair:
1. Collects all meshes from both collections while they're still accessible
2. Sets the UV map named after the secondary collection as active (`active` + `active_render`) on every mesh
3. Excludes all other collections from the view layer
4. Selects all meshes from both collections and sets the active object

### Activate All / Disable All
Bulk-toggle `exclude` on all collections in the view layer — useful for resetting state before a new bake round.

### UV Preview
Before you press Activate, the panel shows which UV map will be activated and whether it exists on the active object.

## Installation

1. Download `uv_collection_switcher.py`
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the `.py` file
4. Enable **UV Collection Switcher** by checking its box

## Usage

Open **View3D → Sidebar (N) → UV Switcher**.

1. Press **Add UVs** to generate named UV maps for the selected collections (do this once per collection pair, or re-run after adding new collections)
2. Choose your **Main Collection** from the first dropdown
3. Choose the **2nd Collection** from the second dropdown
4. Check the UV preview box — it shows the target UV and whether it exists on the active mesh
5. Press **Activate**
6. Run your bake (e.g., via SimpleBake)

### UV Map Naming

UV maps must be named exactly after their collection. `Add UV Maps` creates them with the correct names automatically. If you rename collections afterwards, re-run `Add UV Maps`.

## Requirements

- Blender 3.0 or newer
- No external dependencies — pure Python, `bpy` only
