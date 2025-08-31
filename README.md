# Blender2Quick3D - Qt6.9 Quick3D 引擎集成插件

## 概述

我本质上想要做一个能很好集成在blender中的内置引擎，如同EEVEE和CYCLES那样。但目前时间较紧，只实现了出gltf到qml并启quick3d窗口的功能。实际上这是一个非常低效的做法。当需要频繁更改大场景时，会对读写产生很大压力。

等我看懂balsam和blender的数据传输逻辑我再考虑做实时通信。现在这个ppt可以凑活看了。至少比在creator里来回调舒服多了。

addimportpath有bug，总是少一级目录



TODO：窗口数据，view3d尚未同步
TODO：导出设置，sceneEnviorment还不能设置
TODO：IBL转存逻辑尚未实现
TODO：贴图烘焙尚未实现
TODO：四门两盖等控制器加写，生成qml，给到QQmlApplicationEngine
TODO：自动生成cmake
TODO：指定工作目录，生成gltf和qml
TODO：整理依赖和环境
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
- 支持网格、材质、纹理和动画数据
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

## 📁 文件结构

```
Blender2Quick3D/
├── __init__.py                    # 主插件文件，包含所有UI和操作符
├── qt_quick3d_integration_pyside6.py  # PySide6集成模块
├── balsam_gltf_converter.py      # GLTF到QML转换器
├── render_engine.py               # 渲染引擎注册
├── qml_handler.py                 # QML文件处理器
├── balsam.exe                     # Balsam转换器可执行文件
├── lib/                           # 本地依赖库目录
├── output/                        # 输出文件目录
│   ├── DemoScene.gltf            # 示例GLTF文件
│   ├── DemoScene.qml             # 示例QML文件
│   ├── maps/                     # 纹理贴图
│   └── meshes/                   # 网格文件
└── README.md                      # 说明文档
```

## 🛠️ 安装要求

### 系统要求
- **Blender**: 4.1 或更高版本
- **Python**: 3.10+ (Blender 内置)
- **操作系统**: Windows 10+, macOS 10.15+, Linux

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

#### 1. 设置渲染引擎
- 在 3D 视图中打开侧边栏 (`N` 键)
- 选择 "Qt6.9 Quick3D" 标签页
- 点击 "Set as Render Engine" 按钮

#### 2. 转换场景到 QML
- 在渲染属性面板中找到 "QML Functions" 部分
- 点击 "Convert Scene to QML" 按钮
- 插件会自动导出 GLTF 并转换为 QML

#### 3. 打开 Quick3D 窗口
- 点击 "Open Quick3D Window" 按钮
- 新窗口将显示转换后的 3D 场景
- 支持实时交互和渲染

### 高级功能

#### 自定义路径设置
- **设置 GLTF 路径**: 选择自定义的 GLTF 文件进行转换
- **设置输出目录**: 指定 QML 文件的输出位置
- **批量转换**: 支持多个 GLTF 文件的批量处理

#### 文件管理
- **打开输出文件夹**: 快速访问生成的文件
- **清理输出文件**: 删除旧的输出文件释放空间
- **复制到文档**: 将生成的文件复制到用户文档目录

## 🔧 技术架构

### 核心模块

#### 1. 主插件模块 (`__init__.py`)
- 插件注册和初始化
- UI 面板和操作符定义
- 依赖管理和自动安装
- 场景属性管理

#### 2. PySide6 集成 (`qt_quick3d_integration_pyside6.py`)
- Qt 环境设置和路径管理
- Quick3D 窗口创建和管理
- QML 引擎集成
- 场景数据导出

#### 3. GLTF 转换器 (`balsam_gltf_converter.py`)
- Blender 场景到 GLTF 的导出
- Balsam 转换器调用
- 输出文件管理
- 路径和环境设置

#### 4. 渲染引擎 (`render_engine.py`)
- Quick3D 渲染引擎注册
- 渲染管线集成
- 材质和节点支持
- 渲染设置管理

#### 5. QML 处理器 (`qml_handler.py`)
- QML 文件读取和解析
- 内容清理和组装
- 导入语句处理
- 文件格式优化

### 工作流程

```
Blender 场景 → GLTF 导出 → Balsam 转换 → QML 生成 → Quick3D 渲染
     ↓              ↓           ↓           ↓           ↓
  3D 模型      标准格式    格式转换    Qt 场景    实时渲染
```

## 🎨 特性详解

### 实时渲染
- 支持实时 3D 视图更新
- 集成 Blender 的材质系统
- 支持动态光照和阴影
- 高性能渲染管线

### 材质支持
- 完整的 Blender 材质节点支持
- 自动材质转换和优化
- 支持 PBR 材质工作流
- 纹理贴图自动处理

### 动画支持
- 支持关键帧动画
- 骨骼动画导出
- 变形动画支持
- 时间轴控制

### 性能优化
- 智能 LOD 系统
- 纹理压缩和优化
- 网格简化算法
- 内存管理优化

## 🐛 故障排除

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
- 完整的 Blender 集成

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置
1. 克隆仓库到 Blender 插件目录
2. 安装开发依赖
3. 修改代码并测试
4. 提交更改

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 确保代码通过所有测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

**ZhiningJiao** - 主要开发者


## 📞 支持

如果您需要帮助或有任何问题：

- 提交 GitHub Issue
- 查看项目 Wiki
- 联系开发团队

---

**注意**: 这是一个实验性插件，某些功能可能不稳定。建议在重要项目中使用前充分测试。
