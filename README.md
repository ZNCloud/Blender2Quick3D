# Blender2Quick3D - Qt6.9 Quick3D 引擎集成插件

## 概述

Blender2Quick3D 将 Qt Quick3D (Qt 6.9) 工具链整合进 Blender，帮助你把场景快速导出为 QML，并在外部 Qt 窗口中进行交互预览。当前版本聚焦在自动化导出流程、Balsam 转换集成、PySide6 依赖管理以及场景环境配置，不再尝试注册完整的 Blender 渲染引擎。

我本质上想要做一个能很好集成在blender中的内置引擎，如同EEVEE和CYCLES那样。但目前时间较紧，只实现了出gltf到qml并启quick3d窗口的功能。实
际上这是一个非常低效的做法。当需要频繁更改大场景时，会对读写产生很大压力。
等我看懂balsam和blender的数据传输逻辑我再考虑做实时通信。现在至少比在creator里来回调舒服多了。
addimportpath有bug，总是少一级目录

视频教程介绍：https://youtu.be/P_MgBGx-gKo?si=yZgpe6ZUGS6WNVb2

Phase1：
~~TODO：窗口数据，view3d尚未同步~~
~~TODO：导出设置，sceneEnviorment还不能设置~~
~~TODO：指定工作目录，生成gltf和qml~~
~~TODO：IBL转存逻辑尚未实现~~
Phase2：
TODO：贴图烘焙
TODO：四门两盖等控制器加写，生成qml，给到QQmlApplicationEngine
TODO：整理架构，进一步解耦合
TODO：自动生成cmake
TODO：整理依赖和环境
Phase3：
TODO: 选择性转换资产
TODO：实时通信，实时渲染
## 功能亮点

- **PySide6 依赖管理**：启动时检测系统 PySide6，支持在插件偏好设置中查看/切换安装位置，亦可直接调用 pip 安装并提示重启。
- **Quick3D 预览窗口**：`View3D > Sidebar > Qt6.9 Quick3D` 面板中可一键打开外部 Quick3D 窗口，使用 WASD 与鼠标交互。
- **Balsam 转换工作流**：内置 GLTF→QML 全流程，包括导出、调用 `balsam.exe`、打开输出目录、清理旧文件、保存源场景等操作。
- **工作空间与 QMLProject 支持**：自动识别 `.qmlproject`，同步 `Generated/QtQuick3D` 资产目录，可在枚举中选择资产文件夹并自动切换工作空间。
- **SceneEnvironment 配置**：暴露大量 Qt Quick3D 环境参数（抗锯齿、AO、背景、色彩调整、景深、Glow、Lens Flare、LUT、暗角等），以及自定义 WASD 控制器设置。
- **IBL 资源复制**：在转换前自动拷贝 World 中连接的环境贴图到输出目录，确保 QML 项目使用正确的 IBL 资产。
- **调试工具**：提供 QML 调试模式切换、IBL 复制测试、查看/刷新工作空间、快速保存源场景、弹出工作空间文件夹等实用命令。

## 🛠️ 安装要求

- **Blender**：4.1 或更高版本（内置 Python 3.10）
- **操作系统**：Windows 10（其他平台暂未验证）
- **依赖**：
  - 系统级 **PySide6**（Qt 6.9）
  - Qt 附带的 **balsam.exe**（例如位于 `C:\Qt\6.9.2\mingw_64\bin\balsam.exe`）
  - 或者自己安装的Qt。但要保证有balsam.exe转换器

## 📦 安装与启用

1. 将插件文件夹放入 Blender 的 addons 目录。
2. 在 `编辑 > 偏好设置 > 插件` 中搜索 `Qt6.9 Quick3D Engine` 并启用。
3. 打开插件条目可查看 PySide6 状态，如需要可点击 `Install PySide6` 使用 Blender Python 安装。
4. 若刚刚安装 PySide6，按照提示重启 Blender。

## 🎯 使用指南

### 1. 准备依赖
- 在插件偏好设置中点击 `Show PySide6 Info` 获取当前 PySide6 安装位置。
- 使用 `Search Local Balsam` 自动扫描 `C:/Qt` 下的 `balsam.exe`，或通过 `Add Balsam Path` 手动指定。

### 2. 设置工作空间
- 在 `Qt6.9 Quick3D` 面板点击 `Set Work Space` 选择输出目录。
- 如果目录中存在 `.qmlproject`，插件会自动切换到 QMLProject 模式并列出资产文件夹；更改下拉框会同步 Blender 场景的工作空间路径。

### 3. 导出与转换
- 点击 `Convert Scene to QML` 完成 GLTF 导出与 Balsam 转换，IBL 贴图会被一并复制到输出目录。
- 需要复用已有 GLTF 时，可使用 `Convert Existing GLTF` 并手动指定文件。
- 通过 `Open Output Folder / Open GLTF Folder / Open QML Folder` 快速定位导出结果。

### 4. 场景调优
- 展开 `SceneSettings` 自定义 Quick3D 视口大小、SceneEnvironment 基础参数及扩展效果。
- 启用 WASD 控制器可调整各方向速度、鼠标灵敏度以及按键映射，增强 Quick3D 窗口交互体验。

### 5. 调试与维护
- `Debug Options` 中可以开启 QML 调试模式、测试 IBL 复制、同步工作空间、保存源场景等。
- 在windows中，通过toggle qml debug mode按钮开启qml调试，再点击open quick3d window即可在 “windows-toggle system console”中看到完整的qml文件

## ❓ 常见问题

- **PySide6 未检测到**：确认系统已安装 PySide6；必要时通过插件提供的安装按钮完成安装并重启 Blender。
- **Balsam 枚举为空**：检查 `C:/Qt` 是否存在 Qt Design Studio；可手动添加 `balsam.exe`。
- **转换失败**：查看系统控制台输出，确认 GLTF 导出成功且输出目录有写权限。
- **Quick3D 窗口无法启动**：确认 PySide6 可导入、`qt_quick3d_integration_pyside6.py` 存在且依赖满足。

## 🔄 更新日志

### 版本 0.0.1
- 初始版本，提供 Quick3D 窗口启动、GLTF→QML 转换与依赖管理等功能。

## 👨‍💻 作者

**ZhiningJiao**（zhining.jiao@qt.io）

---

> ⚠️ 本插件仍处于实验阶段，建议在关键项目中使用前进行充分验证。
