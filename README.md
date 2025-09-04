# Blender2Quick3D - Qt6.9 Quick3D 引擎集成插件

## 概述

我本质上想要做一个能很好集成在blender中的内置引擎，如同EEVEE和CYCLES那样。但目前时间较紧，只实现了出gltf到qml并启quick3d窗口的功能。实际上这是一个非常低效的做法。当需要频繁更改大场景时，会对读写产生很大压力。

等我看懂balsam和blender的数据传输逻辑我再考虑做实时通信。现在这个ppt可以凑活看了。至少比在creator里来回调舒服多了。

addimportpath有bug，总是少一级目录


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


## 核心功能

### 1. Qt Quick3D 渲染引擎（开发中，功能上不完善）
- 将 Qt Quick3D 注册为 Blender 的渲染引擎
- 支持实时 3D 渲染和预览
- 集成 Blender 的材质节点系统
- 支持光照、纹理和材质节点

### 2. GLTF 到 QML 转换
- 使用 Balsam 转换器将 Blender 场景导出为 GLTF 格式
- 自动转换为 QML 文件，包含完整的 3D 场景数据
- 支持网格、材质、纹理和动画数据以及IBL
- 生成可直接在 Qt Quick3D 中使用的 QML 文件

### 3. Quick3D 窗口集成
- 在 Blender 中直接打开 Qt Quick3D 窗口
- 实时预览转换后的 3D 场景
- 支持场景交互和实时渲染
- 集成 PySide6 环境管理

### 4. 自动依赖管理
- 自动检测和安装 PySide6 依赖
- 本地依赖管理，避免系统级安装冲突
- 智能环境变量设置
- 自动重启 Blender 完成安装


## 🛠️ 安装要求

### 系统要求
- **Blender**: 4.1 或更高版本
- **Python**: 3.10+ (Blender 内置)
- **操作系统**: Windows 10 （其他的未测试）

### 依赖项
- **PySide6**: Qt6.9 的 Python 绑定
- **Balsam**: GLTF 到 QML 转换工具

## 📦 安装步骤

### 1. 下载插件
- 下载 Blender2Quick3D 插件压缩包
- 解压到 Blender 的插件目录

### 2. 启用插件
- 在 Blender 中打开 `编辑 > 偏好设置 > 插件`
- 搜索 "Qt6.9 Quick3D Engine"
- 勾选启用插件

### 3. 安装依赖
- 插件会自动检测 PySide6 是否可用
- 如果未安装，点击 "Install PySide6" 按钮
- 安装完成后重启 Blender

## 🎯 使用方法

### 基本操作


#### 1.转换场景到 QML
- 在渲染属性面板中找到 "QML Functions" 部分
- 点击 "Convert Scene to QML" 按钮
- 插件会自动导出 GLTF 并转换为 QML

#### 2. 打开 Quick3D 窗口
- 点击 "Open Quick3D Window" 按钮
- 新窗口将显示转换后的 3D 场景
- 支持使用键盘wasd实时交互和渲染

#### 3.如果需要，可以自定义sceneEnvironment


### 常见问题

#### 1. PySide6 安装失败
- 确保网络连接正常
- 检查 Blender 的 Python 版本
- 尝试手动安装 PySide6
- 重启 Blender 后重试

#### 2. 转换失败
- 检查场景是否包含有效的 3D 对象
- 确保材质设置正确
- 检查输出目录权限
- 查看控制台错误信息

#### 3. Quick3D 窗口无法打开
- 确认 PySide6 已正确安装
- 检查 Qt 环境变量设置
- 重启 Blender 后重试
- 查看系统兼容性

### 调试信息
- 启用 Blender 的系统控制台
- 查看插件输出的日志信息
- 检查文件路径和权限
- 验证依赖库版本

## 🔄 更新日志

### 版本 1.0.0
- 初始版本发布
- 支持 Qt6.9 Quick3D 引擎
- 集成 Balsam GLTF 转换器

## 👨‍💻 作者

**ZhiningJiao** - 主要开发者


## 📞 支持

如果您需要帮助或有任何问题：

- 提交 GitHub Issue
- 查看项目 Wiki
- 联系我 zhining.jiao@qt.io

---

**注意**: 这是一个实验性插件，某些功能可能不稳定。建议在重要项目中使用前充分测试。
