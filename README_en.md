# Blender2Quick3D - Qt6.9 Quick3D Engine Integration Plugin

## Overview

I essentially want to create a built-in engine that integrates well into Blender, like EEVEE and CYCLES. However, due to time constraints, I've only implemented the functionality to export GLTF to QML and launch a Quick3D window. This is actually a very inefficient approach. When frequent changes to large scenes are needed, it puts significant pressure on read/write operations.

I'll consider implementing real-time communication once I understand the data transmission logic between Balsam and Blender. For now, this PPT can work for viewing. At least it's much more comfortable than constantly switching back and forth in Creator.

There's a bug with addimportpath - it always misses one directory level.

## Development Phases

**Phase 1:**
- ~~TODO: Window data, view3d not yet synchronized~~
- ~~TODO: Export settings, sceneEnvironment cannot be set yet~~
- ~~TODO: Specify working directory, generate GLTF and QML~~
- ~~TODO: IBL conversion logic not yet implemented~~

**Phase 2:**
- TODO: Texture baking
- TODO: Add controllers for four doors and two covers, generate QML, pass to QQmlApplicationEngine
- TODO: Organize architecture, further decoupling
- TODO: Auto-generate CMake
- TODO: Organize dependencies and environment

**Phase 3:**
- TODO: Selective asset conversion
- TODO: Real-time communication, real-time rendering

## Core Features

### 1. Qt Quick3D Rendering Engine (In Development, Functionally Incomplete)
- Register Qt Quick3D as a Blender rendering engine
- Support real-time 3D rendering and preview
- Integrate with Blender's material node system
- Support lighting, textures, and material nodes

### 2. GLTF to QML Conversion
- Use Balsam converter to export Blender scenes to GLTF format
- Automatically convert to QML files containing complete 3D scene data
- Support mesh, material, texture, and animation data as well as IBL
- Generate QML files that can be used directly in Qt Quick3D

### 3. Quick3D Window Integration
- Open Qt Quick3D window directly within Blender
- Real-time preview of converted 3D scenes
- Support scene interaction and real-time rendering
- Integrated PySide6 environment management

### 4. Automatic Dependency Management
- Automatically detect and install PySide6 dependencies
- Local dependency management to avoid system-level installation conflicts
- Smart environment variable setup
- Automatic Blender restart to complete installation

## 🛠️ Installation Requirements

### System Requirements
- **Blender**: Version 4.1 or higher
- **Python**: 3.10+ (Built-in with Blender)
- **Operating System**: Windows 10 (Others not tested)

### Dependencies
- **PySide6**: Python bindings for Qt6.9
- **Balsam**: GLTF to QML conversion tool

## 📦 Installation Steps

### 1. Download Plugin
- Download the Blender2Quick3D plugin package
- Extract to Blender's addon directory

### 2. Enable Plugin
- In Blender, open `Edit > Preferences > Add-ons`
- Search for "Qt6.9 Quick3D Engine"
- Check to enable the plugin

### 3. Install Dependencies
- The plugin will automatically detect if PySide6 is available
- If not installed, click the "Install PySide6" button
- Restart Blender after installation is complete

## 🎯 Usage

### Basic Operations

#### 1. Convert Scene to QML
- Find the "QML Functions" section in the render properties panel
- Click the "Convert Scene to QML" button
- The plugin will automatically export GLTF and convert to QML

#### 2. Open Quick3D Window
- Click the "Open Quick3D Window" button
- A new window will display the converted 3D scene
- Supports real-time interaction and rendering using WASD keys

#### 3. Customize sceneEnvironment (if needed)

### Common Issues

#### 1. PySide6 Installation Failed
- Ensure network connection is stable
- Check Blender's Python version
- Try manually installing PySide6
- Restart Blender and retry

#### 2. Conversion Failed
- Check if the scene contains valid 3D objects
- Ensure material settings are correct
- Check output directory permissions
- View console error messages

#### 3. Quick3D Window Won't Open
- Confirm PySide6 is properly installed
- Check Qt environment variable settings
- Restart Blender and retry
- Check system compatibility

### Debug Information
- Enable Blender's system console
- View plugin output log information
- Check file paths and permissions
- Verify dependency library versions

## 🔄 Changelog

### Version 1.0.0
- Initial version release
- Support for Qt6.9 Quick3D engine
- Integrated Balsam GLTF converter

## 👨‍💻 Author

**ZhiningJiao** - Main Developer

## 📞 Support

If you need help or have any questions:

- Submit a GitHub Issue
- Check the project Wiki
- Contact me at zhining.jiao@qt.io

---

**Note**: This is an experimental plugin, some features may be unstable. Please test thoroughly before using in important projects.
