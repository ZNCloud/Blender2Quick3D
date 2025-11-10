# Blender2Quick3D - Qt6.9 Quick3D Engine Integration Plugin

## Overview

Blender2Quick3D integrates the Qt Quick3D (Qt 6.9) toolchain into Blender. The addon streamlines the export pipeline to QML, launches a standalone Quick3D preview window, and provides helpers for managing PySide6, Balsam, workspaces, and scene environment settings. A custom Blender render engine is no longer part of this release; the focus is on authoring assets in Blender and iterating quickly inside Qt.

The long-term ambition is still to deliver a render engine that feels as native as EEVEE or Cycles. For now, only the GLTF → QML export flow and Quick3D window launcher are implemented. This approach is inefficient for large scenes because of heavy disk I/O, but it already makes presentation-style demos far easier than hopping between Blender and Qt Creator. There is also a known `addimportpath` issue that drops one directory level.

▶ Video walkthrough: https://youtu.be/P_MgBGx-gKo?si=yZgpe6ZUGS6WNVb2

### Roadmap

**Phase 1**
- ~~Window data syncing with View3D~~
- ~~SceneEnvironment export settings~~
- ~~Workspace selection for GLTF/QML generation~~
- ~~IBL transfer logic~~

**Phase 2**
- Texture baking
- Add vehicle-style controllers (four doors, two covers), generate QML, pass to `QQmlApplicationEngine`
- Refactor architecture for better decoupling
- Auto-generate CMake
- Streamline dependency/environment setup

**Phase 3**
- Selective asset conversion
- Real-time communication and rendering

## Feature Highlights

- **PySide6 dependency management**: Detect system-wide PySide6 on startup, inspect all discovered installations, switch between them, or trigger a pip installation directly from the addon preferences with restart guidance.
- **Quick3D preview window**: Launch the external Quick3D UI from `View3D > Sidebar > Qt6.9 Quick3D`, navigate with WASD + mouse, and validate exported content interactively.
- **Balsam conversion workflow**: Run the full GLTF → QML pipeline with one click, open target folders, clean outdated output, and save source assets alongside the generated files.
- **Workspace & QMLProject integration**: Auto-detect `.qmlproject` files, map available asset folders under `Generated/QtQuick3D`, and keep Blender’s workspace path synchronized with the chosen folder.
- **SceneEnvironment controls**: Expose extensive Qt Quick3D environment options (AA, AO, background, tonemapping, color adjustments, DOF, glow, lens flare, LUT, vignette, OIT, etc.) plus configurable WASD controller parameters.
- **IBL asset handling**: Copy all World-linked images into the Balsam output prior to conversion so the QML project references the correct HDR textures.
- **Debug helpers**: Toggle QML debug verbosity, test IBL copying, refresh workspaces, save source scenes, and open the active workspace folder straight from Blender.

## 🛠️ Requirements

- **Blender**: 4.1 or newer (ships with Python 3.10)
- **Operating System**: Windows 10 (other platforms untested)
- **Dependencies**:
  - System-level **PySide6** for Qt 6.9
- **balsam.exe** shipped with Qt (for example `C:\Qt\6.9.2\mingw_64\bin\balsam.exe`)
- Any custom Qt installation works as long as it contains `balsam.exe`

## 📦 Installation & Activation

1. Copy the addon folder into Blender’s addons directory.
2. Enable `Qt6.9 Quick3D Engine` via `Edit > Preferences > Add-ons`.
3. In the addon preferences, inspect the PySide6 status; install via `Install PySide6` if required.
4. Restart Blender after installing PySide6 or switching Python environments.

## 🎯 Getting Started

### 1. Prepare Dependencies
- Use `Show PySide6 Info` in addon preferences to confirm available installations.
- Click `Search Local Balsam` to scan `C:/Qt` for `balsam.exe`, or add a path manually with `Add Balsam Path`.

### 2. Configure Workspace
- Choose a workspace directory with `Set Work Space`.
- If a `.qmlproject` is found, the addon enters QMLProject mode, caches asset folders, and updates the workspace automatically when you pick a folder from the dropdown.

### 3. Convert Scenes
- Hit `Convert Scene to QML` to export GLTF, copy IBL assets, and run Balsam.
- Use `Convert Existing GLTF` when re-processing a pre-exported file.
- Access results via `Open Output Folder`, `Open GLTF Folder`, or `Open QML Folder`, and clean up with `Clean Output Files`.

### 4. Tune the Scene
- Expand `SceneSettings` to tweak Quick3D viewport dimensions and SceneEnvironment parameters.
- Enable and tune the WASD controller (base speeds, per-direction overrides, mouse sensitivity, key mapping) to match your interaction needs.

### 5. Debug & Maintenance
- Toggle QML debug mode, run the IBL copy test, refresh the workspace from the selected asset folder, or save the current source scene (GLTF + blend) using the provided operators.
- On Windows, toggle QML debug mode and reopen the Quick3D window to stream the full QML output in *Window → Toggle System Console* (the Blender system console).
- Restart Blender after significant dependency changes to refresh PySide6 modules.

## ❓ Troubleshooting

- **PySide6 not found**: Ensure PySide6 is installed system-wide; reinstall via the addon and restart Blender.
- **No Balsam options**: Verify Qt Design Studio is installed under `C:/Qt`, or register `balsam.exe` manually.
- **Conversion errors**: Check the system console for details, confirm GLTF export succeeded, and ensure the output directory is writable.
- **Quick3D window fails to open**: Validate that PySide6 imports correctly and that `qt_quick3d_integration_pyside6.py` and its resources are present.

## 🔄 Changelog

### Version 0.0.1
- Initial public release with Quick3D preview window, GLTF → QML automation, dependency helpers, and SceneEnvironment controls.

## 👨‍💻 Author

**ZhiningJiao** – zhining.jiao@qt.io

---

> **Note**  
> Blender2Quick3D is experimental. Test thoroughly before using it in production-critical projects.
