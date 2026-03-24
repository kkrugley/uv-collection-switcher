# UV Collection Switcher

Blender addon for texture baking workflows where one base mesh gets baked against different swappable overlays — one click instead of manually toggling collections and UV maps before every bake.

## The Problem

Concrete use case: eyewear visualization. The main collection is a glasses frame (`Glasses Frame Low-poly`). The secondary collections are decorative front masks — each one snaps over the frame and changes the look completely. To bake a specific frame+mask combination you need:

1. The right collections visible in the viewport
2. The matching UV map active on every mesh (with camera icon)
3. All other collections excluded so they don't interfere

Doing this by hand across 8+ variants is slow and error-prone.

## The Solution

Open `N → UV Switcher`, pick your main and secondary collection, press **Activate**. The addon does the rest.

## Features

### Add UVs for all Collections
Creates a UV map on each mesh in every collection, named after its collection. Each collection's meshes get only their own named UV map — no cross-contamination of UVs between collections. Skips maps that already exist, so it's safe to re-run.

### Activate
Given a selected main + secondary collection pair:
1. **Main collection meshes**: Clears all existing UV maps, then adds and activates a UV map named after the secondary collection
2. **2nd collection meshes**: Finds and activates the UV map named after the secondary collection
3. Sets `active_render` (camera icon) on the correct UV for all meshes
4. Excludes all other collections from the view layer
5. Selects all meshes from both collections

### Activate All / Disable All
Bulk-toggle `exclude` on all collections in the view layer — useful for resetting state before a new bake round.

### UV List
Toggle to view all UV maps in the scene with delete options for cleanup.

### UV Preview
Before you press Activate, the panel shows which UV map will be activated and whether it exists on the active object.

## Installation

1. Download `uv_collection_switcher.py`
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the `.py` file
4. Enable **UV Collection Switcher** by checking its box

## Usage

Open **View3D → Sidebar (N) → UV Switcher**.

1. Press **Add UVs for all Collections** to generate named UV maps for all collections (do this once per scene setup)
2. Choose your **Main Collection** from the first dropdown (e.g., glasses frame)
3. Choose the **2nd Collection** from the second dropdown (e.g., decorative mask)
4. Check the UV preview box — it shows the target UV and whether it exists on the active mesh
5. Press **Activate**
6. Run your bake (e.g., via SimpleBake)

### UV Map Naming

UV maps must be named exactly after their collection. `Add UVs for all Collections` creates them with the correct names automatically. If you rename collections afterwards, re-run `Add UVs for all Collections`.

### How Activation Works

When you select a 2nd collection and press Activate:
- The main collection's meshes get their UVs replaced with the 2nd collection's UV (only one UV map remains)
- The 2nd collection's meshes activate their matching UV
- The camera icon appears next to the correct UV on all meshes

This ensures every mesh uses the UV layout that matches the current secondary collection being baked.

## Requirements

- Blender 3.0 or newer
- No external dependencies — pure Python, `bpy` only
