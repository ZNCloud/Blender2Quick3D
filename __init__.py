bl_info = {
    "name": "Qt6.9 Quick3D Engine",
    "author": "Zhining_Jiao",
    "version": (0, 0, 1),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Qt6.9 Quick3D",
    "description": "Integrate Qt6.9 Quick3D engine into Blender",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

from doctest import debug
import bpy
import os
import sys
import subprocess
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Panel, Operator, AddonPreferences


from . import path_manager #manage all paths
from . import scene_environment #manage scene environment settings for Qt Quick3D
from . import qmlproject_helper #manage qmlproject related logic

# 检查 PySide6 是否可用
def check_pyside6_availability():
    """检查PySide6是否可用，只使用系统已安装的版本"""
    try:
        import PySide6
        pyside6_path = os.path.dirname(PySide6.__file__)
        print(f"✅ 找到系统PySide6: {pyside6_path}")
        return True, None
    except ImportError as e:
        print(f"❌ 系统没有PySide6: {e}")
        return False, str(e)

# find_all_pyside6_installations 函数已移至 path_manager.py

# get_pyside6_installation_info 函数已移至 path_manager.py

# get_python_executable_info 函数已移至 path_manager.py

# 检查系统是否有PySide6
PYSDIE6_AVAILABLE, PYSDIE6_ERROR = check_pyside6_availability()

# 重启标记 - 用于跟踪是否需要重启
RESTART_NEEDED = False

# 全局变量，用于保持PySide6窗口引用
_qml_window = None
_qml_app = None
SELECTED_BALSAM_PATH = None

# 导入我们的Qt集成模块
try:
    if PYSDIE6_AVAILABLE:
        from . import qt_quick3d_integration_pyside6 as qt_quick3d_integration
        MODULES_AVAILABLE = True
    else:
        MODULES_AVAILABLE = False
        qt_quick3d_integration = None
except ImportError as e:
    print(f"Warning: Some Qt6.9 Quick3D modules not found: {e}")
    MODULES_AVAILABLE = False
    qt_quick3d_integration = None

# Balsam路径管理 - 使用path_manager模块

def _label_for_balsam_path(path_str: str) -> str:
    """生成友好标签，例如 6.5.3-mingw_64 或 6.5.3-msvc2019_64"""
    try:
        p = path_str.replace('\\', '/').lower()
        # 抓版本号
        import re
        m = re.search(r"/(\d+\.\d+\.\d+)/", p)
        ver = m.group(1) if m else "unknown"
        toolchain = "mingw" if "mingw" in p else ("msvc" if "msvc" in p else "qt")
        # 进一步细分架构
        arch = "64" if "_64" in p or "64" in p else ("32" if "_32" in p or "32" in p else "")
        if toolchain == 'msvc':
            # 提取msvc后缀
            m2 = re.search(r"msvc(\d+)_?(\d+)?", p)
            if m2:
                tc = f"msvc{m2.group(1)}{('_' + m2.group(2)) if m2.group(2) else ''}"
            else:
                tc = "msvc"
        elif toolchain == 'mingw':
            tc = "mingw"
        else:
            tc = "qt"
        suffix = f"_{arch}" if arch else ""
        return f"{ver}-{tc}{suffix}"
    except Exception:
        return os.path.basename(path_str)


# 回调函数：资源文件夹变化时自动设置工作空间
def update_qmlproject_assets_folder(self, context):
    """当资源文件夹选择改变时，自动设置工作空间"""
    try:
        from . import qmlproject_helper, path_manager
        
        scene = context.scene
        asset_folder = scene.qmlproject_assets_folder
        
        # 跳过特殊值
        if asset_folder in ["NONE", "EMPTY", "ERROR"]:
            return
        
        # 获取 helper 实例
        helper = qmlproject_helper.get_qmlproject_helper()
        
        if not helper.qtquick3d_assets_dir:
            print("⚠️ QMLProject 未初始化，无法自动设置工作空间")
            return
        
        # 构建完整路径
        asset_path = os.path.join(helper.qtquick3d_assets_dir, asset_folder)
        
        if not os.path.exists(asset_path):
            os.makedirs(asset_path, exist_ok=True)
            print(f"📁 自动创建资源文件夹: {asset_path}")
        
        # 设置工作空间
        pm = path_manager.get_path_manager()
        pm.set_work_space(asset_path)
        scene.work_space_path = asset_path
        
        print(f"✅ 工作空间已自动设置为: {asset_path}")
            
    except Exception as e:
        print(f"❌ 自动设置工作空间失败: {e}")

# 注册场景属性
def register_scene_properties():
    """注册场景属性"""
    # Balsam转换器相关属性
    bpy.types.Scene.work_space_path = StringProperty(
        name="Work Space Path",
        description="Working directory for GLTF and QML files",
        default="",
        subtype='DIR_PATH'
    )
    
    # 保留原有属性以保持向后兼容
    bpy.types.Scene.balsam_gltf_path = StringProperty(
        name="Balsam GLTF Path",
        description="Custom GLTF file path for Balsam conversion",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.balsam_output_dir = StringProperty(
        name="Balsam Output Directory",
        description="Custom output directory for Balsam conversion",
        default="",
        subtype='DIR_PATH'
    )

    bpy.types.Scene.balsam_version = EnumProperty(
        name="Balsam Version",
        description="Choose a Qt Design Studio balsam.exe under C:/Qt or Auto",
        items=path_manager.build_balsam_enum_items,
        default=0,
        update=path_manager.update_balsam_selection,
    )
    
    # QMLProject 相关属性
    bpy.types.Scene.qmlproject_path = StringProperty(
        name="QMLProject Path",
        description="Path to .qmlproject file",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qmlproject_assets_folder = EnumProperty(
        name="Asset Folder",
        description="Select an asset folder from Generated/QtQuick3D (auto-updates workspace)",
        items=qmlproject_helper.build_assets_folder_enum_items,
        default=0,
        update=update_qmlproject_assets_folder,  # 自动设置工作空间
    )
    
    # 注册SceneEnvironment属性
    scene_environment.register_scene_environment_properties()



# 显示 PySide6 信息操作符
class ShowPySide6InfoOperator(bpy.types.Operator):
    bl_idname = "qt_quick3d.show_pyside6_info"
    bl_label = "Show PySide6 Info"
    bl_description = "Display detailed PySide6 installation information"
    
    def execute(self, context):
        # 获取PySide6信息
        pyside6_info = path_manager.get_pyside6_installation_info()
        
        # 获取Python信息
        python_info = path_manager.get_python_executable_info()
        
        # 创建信息消息
        if pyside6_info['available']:
            current = pyside6_info['current']
            message = f"PySide6 {current['version']} found at:\n{current['path']}\n\nInstallation: {current['description']}"
            self.report({'INFO'}, f"PySide6 {current['version']} is available")
        else:
            message = f"PySide6 not available: {pyside6_info['error']}"
            self.report({'WARNING'}, "PySide6 is not available")
        
        # 显示对话框
        def draw(self, context):
            layout = self.layout
            
            # PySide6信息
            box = layout.box()
            box.label(text="PySide6 Information", icon='INFO')
            
            if pyside6_info['available']:
                # 当前使用的安装
                current = pyside6_info['current']
                col = box.column(align=True)
                col.label(text=f"当前使用:", icon='RESTRICT_SELECT_OFF')
                col.label(text=f"  版本: {current['version']}")
                col.label(text=f"  路径: {current['path']}")
                col.label(text=f"  位置: {current['description']}")
                
                # 显示所有可用的安装
                all_installs = pyside6_info['all_installations']
                if len(all_installs) > 1:
                    col.separator()
                    col.label(text=f"所有可用安装 ({len(all_installs)}个):", icon='COLLECTION_NEW')
                    
                    for i, install in enumerate(all_installs):
                        sub_col = col.column(align=True)
                        if install['path'] == current['path']:
                            sub_col.label(text=f"  {i+1}. {install['description']} (当前)", icon='CHECKMARK')
                        else:
                            priority_text = "推荐" if install['priority'] == 1 else "备选"
                            sub_col.label(text=f"  {i+1}. {install['description']} ({priority_text})", icon='INFO')
                            # 添加切换按钮
                            switch_op = sub_col.operator("qt_quick3d.switch_pyside6_installation", 
                                                       text=f"切换到 {install['type'].title()}", 
                                                       icon='ARROW_LEFTRIGHT')
                            switch_op.installation_path = install['path']
                        sub_col.label(text=f"     版本: {install['version']}")
                        sub_col.label(text=f"     路径: {install['path']}")
                
                # 推荐安装
                best = pyside6_info['best_installation']
                if best and best['path'] != current['path']:
                    col.separator()
                    col.label(text="推荐使用:", icon='FUND')
                    col.label(text=f"  {best['description']}")
                    col.label(text=f"  版本: {best['version']}")
                    col.label(text=f"  路径: {best['path']}")
                    # 添加快速切换按钮
                    switch_op = col.operator("qt_quick3d.switch_pyside6_installation", 
                                           text="切换到推荐安装", 
                                           icon='FUND')
                    switch_op.installation_path = best['path']
            else:
                col = box.column(align=True)
                col.label(text=f"状态: 不可用", icon='CANCEL')
                col.label(text=f"错误: {pyside6_info['error']}")
            
            # Python信息
            box = layout.box()
            box.label(text="Python Information", icon='CONSOLE')
            
            col = box.column(align=True)
            col.label(text=f"可执行文件: {python_info['executable']}")
            col.label(text=f"版本: {python_info['version'].split()[0]}")
            col.label(text=f"系统 site-packages:")
            for site_path in python_info['site_packages']:
                col.label(text=f"  • {site_path}")
            if python_info['user_site']:
                col.label(text=f"用户 site-packages: {python_info['user_site']}")
            col.label(text=f"虚拟环境: {'是' if python_info['is_virtual_env'] else '否'}")
        
        # 显示对话框
        context.window_manager.popup_menu(draw, title="PySide6 & Python Info", icon='INFO')
        
        return {'FINISHED'}

# 切换PySide6安装操作符
class SwitchPySide6InstallationOperator(bpy.types.Operator):
    bl_idname = "qt_quick3d.switch_pyside6_installation"
    bl_label = "Switch PySide6 Installation"
    bl_description = "Switch to a different PySide6 installation"
    
    installation_path: bpy.props.StringProperty(
        name="Installation Path",
        description="Path to the PySide6 installation to switch to"
    )
    
    def execute(self, context):
        if not self.installation_path or not os.path.exists(self.installation_path):
            self.report({'ERROR'}, "Invalid PySide6 installation path")
            return {'CANCELLED'}
        
        try:
            # 将新的安装路径添加到sys.path的开头
            install_dir = os.path.dirname(self.installation_path)
            
            # 移除现有的PySide6路径
            import sys
            paths_to_remove = []
            for path in sys.path:
                if 'PySide6' in path or 'site-packages' in path:
                    paths_to_remove.append(path)
            
            for path in paths_to_remove:
                if path in sys.path:
                    sys.path.remove(path)
            
            # 添加新的路径到开头
            if install_dir not in sys.path:
                sys.path.insert(0, install_dir)
            
            # 重新加载PySide6模块
            import importlib
            if 'PySide6' in sys.modules:
                importlib.reload(sys.modules['PySide6'])
            
            self.report({'INFO'}, f"Switched to PySide6 installation: {self.installation_path}")
            
            # 刷新界面
            for area in context.screen.areas:
                area.tag_redraw()
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to switch PySide6 installation: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# 安装 PySide6 操作符
class InstallPySide6Operator(bpy.types.Operator):
    bl_idname = "qt_quick3d.install_pyside"
    bl_label = "Install PySide6"
    bl_description = "Install PySide6 system-wide using pip"
    
    def execute(self, context):
        global PYSDIE6_AVAILABLE, PYSDIE6_ERROR, RESTART_NEEDED
        
        try:
            # 检查是否已经有系统安装的PySide6
            if PYSDIE6_AVAILABLE:
                self.report({'INFO'}, "PySide6 is already available from system installation. No need to install.")
                return {'FINISHED'}
            
            # 显示进度信息
            self.report({'INFO'}, "Starting PySide6 system installation...")
            
            # 使用 Blender 的 Python 执行 pip 系统级安装
            python_exe = sys.executable
            cmd = [python_exe, "-m", "pip", "install", "PySide6"]
            
            # 执行安装
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.report({'INFO'}, "PySide6 installed successfully! Please restart Blender.")
                
                # 更新状态
                PYSDIE6_AVAILABLE, PYSDIE6_ERROR = check_pyside6_availability()
                RESTART_NEEDED = True
                
                # 设置偏好设置中的重启标记
                try:
                    addon_prefs = context.preferences.addons.get(__name__)
                    if addon_prefs:
                        addon_prefs.preferences.restart_needed = True
                except:
                    pass
                
                # 刷新界面
                for area in context.screen.areas:
                    area.tag_redraw()
                    
            else:
                error_msg = result.stderr if result.stderr else "Unknown error occurred"
                self.report({'ERROR'}, f"Installation failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            self.report({'ERROR'}, "Installation timed out. PySide6 is a large package.")
        except Exception as e:
            self.report({'ERROR'}, f"Installation failed: {str(e)}")
            
        return {'FINISHED'}

# 重启 Blender 操作符
class RestartBlenderOperator(bpy.types.Operator):
    bl_idname = "qt_quick3d.restart_blender"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender to complete PySide6 installation"
    
    def execute(self, context):
        try:
            # 保存当前场景
            if bpy.data.is_saved:
                bpy.ops.wm.save_mainfile()
            elif bpy.data.is_dirty:
                # 如果场景未保存但有更改，提示用户
                bpy.ops.wm.save_mainfile('INVOKE_DEFAULT')
                return {'FINISHED'}
            
            # 清除重启标记
            try:
                addon_prefs = context.preferences.addons.get(__name__)
                if addon_prefs:
                    addon_prefs.preferences.restart_needed = False
            except:
                pass
            
            # 获取 Blender 可执行文件路径
            blender_exe = bpy.app.binary_path
            
            if blender_exe and os.path.exists(blender_exe):
                # 构建重启命令
                if sys.platform == "win32":
                    # Windows: 使用 start 命令启动新实例
                    subprocess.Popen(["start", blender_exe], shell=True)
                elif sys.platform == "darwin":
                    # macOS: 使用 open 命令
                    subprocess.Popen(["open", blender_exe])
                else:
                    # Linux: 直接启动
                    subprocess.Popen([blender_exe])
                
                # 延迟关闭当前实例
                bpy.ops.wm.quit_blender()
            else:
                self.report({'ERROR'}, "Could not find Blender executable. Please restart manually.")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to restart Blender: {str(e)}")
            
        return {'FINISHED'}

# 插件偏好设置面板
class QtQuick3DAddonPreferences(AddonPreferences):
    bl_idname = __name__
    
    # 添加重启标记属性
    restart_needed: BoolProperty(
        name="Restart Needed",
        description="Whether Blender needs to be restarted after PySide6 installation",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        
        # 显示依赖状态
        layout.label(text="Dependencies Status:")
        
        if PYSDIE6_AVAILABLE:
            layout.label(text="✓ PySide6: System Installation (Ready)")
            
            # 添加信息按钮
            layout.operator("qt_quick3d.show_pyside6_info", text="Show PySide6 Info", icon='INFO')
            
            # 显示重启按钮（如果刚安装完成）
            if self.restart_needed:
                box = layout.box()
                box.label(text="⚠️ Restart Required")
                
                box.operator("qt_quick3d.restart_blender", text="Restart Blender Now")
                
                layout.separator()
                layout.operator("qt_quick3d.restart_blender", text="Restart Blender")
        else:
            layout.label(text="✗ PySide6: Not Available")
            
            # 安装按钮
            layout.operator("qt_quick3d.install_pyside", text="Install PySide6")
            
            # 安装说明
            box = layout.box()
            box.label(text="Installation Notes:")
            box.label(text="• PySide6 is required for Qt Quick3D functionality")
            box.label(text="• Click 'Install PySide6' to install system-wide")
            box.label(text="• Restart Blender after installation")
        
        # 模块状态
        layout.separator()
        layout.label(text="Module Status:")
        
        if MODULES_AVAILABLE:
            layout.label(text="✓ All modules loaded successfully")
        else:
            layout.label(text="✗ Some modules failed to load")
            
            if not PYSDIE6_AVAILABLE:
                layout.label(text="PySide6 not available")
            else:
                layout.label(text="Warning: Modules not fully loaded")
                layout.operator("qt_quick3d.restart_blender", text="Restart Blender")

class VIEW3D_PT_qt_quick3d_panel(Panel):
    """Qt6.9 Quick3D Engine Panel"""
    bl_label = "Qt6.9 Quick3D Engine"
    bl_idname = "VIEW3D_PT_qt_quick3d_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Qt6.9 Quick3D'

    def draw(self, context):
        layout = self.layout
        
        # 检查依赖状态
        if not PYSDIE6_AVAILABLE:
            layout.label(text="PySide6 not available")
            layout.label(text="Please install PySide6 in addon preferences")
            layout.operator("qt_quick3d.install_pyside", text="Install PySide6")
            return
        
        if not MODULES_AVAILABLE:
            layout.label(text="Warning: Modules not fully loaded")
            layout.label(text="PySide6 is installed but modules need restart")
            layout.operator("qt_quick3d.restart_blender", text="Restart Blender")
            return
        
        # 添加一个按钮来启动Qt Quick3D窗口
        layout.operator("qt_quick3d.open_window", text="Open Quick3D Window")
        
        # 添加渲染引擎选择
        # layout.separator()
        # layout.label(text="Render Engine:")
        # layout.operator("qt_quick3d.set_render_engine", text="Set as Render Engine")
        
        # QML转换功能
        layout.separator()
      #  layout.label(text="QML Export:")
        layout.operator("qt_quick3d.balsam_convert_scene",text="Convert Scene to QML")
        #设置导出路径
        # 设置工作空间路径
        layout.separator()
        layout.label(text="Work Space Settings:")
        
        row = layout.row()
        row.operator("qt_quick3d.balsam_set_work_space", text="Set Work Space")
        
        # 显示提示信息
        box = layout.box()
        box.scale_y = 0.7
        box.label(text="💡 Tip: Auto-detects .qmlproject files", icon='INFO')
        # layout.separator()
        
        

        # row.operator("qt_quick3d.balsam_set_work_space", text="Set Work Space")

        # 显示当前路径信息
        scene = context.scene
        
        # 创建信息框显示路径关系
        info_box = layout.box()
        info_box.label(text="Path Information:", icon='INFO')
        
        # Work Space 路径 - 从 path_manager 获取实际的 workspace
        from . import path_manager
        pm = path_manager.get_path_manager()
        work_space = pm.work_space_path or pm.output_base_dir
        
        if work_space:
            # 显示完整路径
            info_box.label(text=f"Workspace: ...{work_space[-40:]}" if len(work_space) > 40 else f"Workspace: {work_space}", icon='FOLDER_REDIRECT')
        else:
            info_box.label(text="Workspace: (Not set - using default)", icon='ERROR')
        
        # QMLProject 路径（如果设置了）
        qmlproject_path = getattr(scene, "qmlproject_path", None)
        if qmlproject_path:
            qmlproject_name = os.path.basename(qmlproject_path)
            info_box.label(text=f"QMLProject: {qmlproject_name}", icon='FILE')
            
            # 显示资源文件夹（如果选择了）
            asset_folder = getattr(scene, "qmlproject_assets_folder", "NONE")
            if asset_folder and asset_folder not in ["NONE", "EMPTY", "ERROR"]:
                info_box.label(text=f"Asset Folder: {asset_folder}", icon='ASSET_MANAGER')
                
                # 显示路径关系说明
                from . import qmlproject_helper
                helper = qmlproject_helper.get_qmlproject_helper()
                if helper.qtquick3d_assets_dir:
                    # 简化显示：QMLProject目录/Generated/QtQuick3D/AssetFolder
                    qml_dir = os.path.dirname(qmlproject_path)
                    relative_path = f"{os.path.basename(qml_dir)}/Generated/QtQuick3D/{asset_folder}"
                    info_box.label(text=f"  → {relative_path}", icon='FORWARD')

        # 提供调用balsam转换和写入的按钮
        layout.separator()
        layout.label(text="Balsam Conversion:")
        
        # INSERT_YOUR_CODE
        # 添加balsam版本选择下拉框
        layout.separator()
        layout.label(text="Balsam Version:")
        
        # 搜索按钮
        row = layout.row()
        row.operator("qt_quick3d.search_local_balsam", text="Search Local Balsam", icon='VIEWZOOM')
        row.operator("qt_quick3d.add_balsam_path", text="Add Balsam Path", icon='FILE_FOLDER')

        # 确保场景有balsam_version属性，否则显示默认
        if not hasattr(scene, "balsam_version"):
            # 兼容性处理：如果属性不存在，显示提示
            layout.label(text="(Scene property 'balsam_version' not found)")
        else:
            # 下拉框，允许用户选择balsam版本
            layout.prop(scene, "balsam_version", text="Select Version")

        
        #SceneSettings，用于设置弹出的窗口大小，view3d大小，sceneEnvironment设置
        # INSERT_YOUR_CODE

        # SceneSettings 折叠框
        scene_settings_box = layout.box()
        scene_settings_box.prop(scene, "show_scene_settings", icon="TRIA_DOWN" if getattr(scene, "show_scene_settings", False) else "TRIA_RIGHT", emboss=False, text="SceneSettings")

        if getattr(scene, "show_scene_settings", False):
            # 窗口/View3D 大小设置（统一设置，因为View3D覆盖全窗口）
            scene_settings_box.label(text="Size:")
            row = scene_settings_box.row(align=True)
            row.prop(scene, "qtquick3d_view3d_width", text="Width")
            row.prop(scene, "qtquick3d_view3d_height", text="Height")

            # SceneEnvironment 设置
            scene_settings_box.label(text="SceneEnvironment:")
            
            # 基础SceneEnvironment设置
            basic_box = scene_settings_box.box()
            basic_box.label(text="Basic Settings:")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_antialiasing_mode", text="AA Mode")
            row.prop(scene, "qtquick3d_antialiasing_quality", text="AA Quality")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_ao_enabled", text="AO Enabled")
            row.prop(scene, "qtquick3d_ao_strength", text="AO Strength")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_ao_sample_rate", text="AO Sample Rate")
            row.prop(scene, "qtquick3d_ao_distance", text="AO Distance")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_background_mode", text="Background Mode")
            row.prop(scene, "qtquick3d_clear_color", text="Clear Color")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_depth_test_enabled", text="Depth Test")
            row.prop(scene, "qtquick3d_depth_prepass_enabled", text="Depth PrePass")

            # Scissor 设置
            scissor_box = scene_settings_box.box()
            scissor_box.label(text="Scissor:")
            row = scissor_box.row(align=True)
            row.prop(scene, "qtquick3d_scissor_enabled", text="Enable")
            row = scissor_box.row(align=True)
            row.enabled = getattr(scene, 'qtquick3d_scissor_enabled', False)
            row.prop(scene, "qtquick3d_scissor_rect", text="Rect")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_probe_exposure", text="Probe Exposure")
            row.prop(scene, "qtquick3d_probe_horizon", text="Probe Horizon")
            row = basic_box.row(align=True)
            row.prop(scene, "qtquick3d_tonemap_mode", text="Tonemap Mode")
            row.prop(scene, "qtquick3d_oit_method", text="OIT Method")
            
            # 添加 ExtendedSceneEnvironment 复选框
            row = scene_settings_box.row()
            row.prop(scene, "qtquick3d_use_extended_environment", text="Use ExtendedSceneEnvironment")

            if getattr(scene, "qtquick3d_use_extended_environment", False):
                extended_box = scene_settings_box.box()
                extended_box.label(text="Extended Environment Settings:")

                # 颜色调整
                color_box = extended_box.box()
                color_box.label(text="Color Adjustments:")
                row = color_box.row(align=True)
                row.prop(scene, "qtquick3d_color_adjustments_enabled", text="Enable Color Adjustments")
                row = color_box.row(align=True)
                row.prop(scene, "qtquick3d_brightness", text="Brightness")
                row.prop(scene, "qtquick3d_contrast", text="Contrast")
                row.prop(scene, "qtquick3d_saturation", text="Saturation")
                
                # 曝光和锐化
                exposure_box = extended_box.box()
                exposure_box.label(text="Exposure & Sharpness:")
                row = exposure_box.row(align=True)
                row.prop(scene, "qtquick3d_exposure", text="Exposure")
                row.prop(scene, "qtquick3d_sharpness", text="Sharpness")
                row.prop(scene, "qtquick3d_white_point", text="White Point")
                
                # 景深效果
                dof_box = extended_box.box()
                dof_box.label(text="Depth of Field:")
                row = dof_box.row(align=True)
                row.prop(scene, "qtquick3d_dof_enabled", text="Enable DOF")
                row.prop(scene, "qtquick3d_dof_blur_amount", text="Blur Amount")
                row = dof_box.row(align=True)
                row.prop(scene, "qtquick3d_dof_focus_distance", text="Focus Distance")
                row.prop(scene, "qtquick3d_dof_focus_range", text="Focus Range")
                
                # 发光效果
                glow_box = extended_box.box()
                glow_box.label(text="Glow Effect:")
                row = glow_box.row(align=True)
                row.prop(scene, "qtquick3d_glow_enabled", text="Enable Glow")
                row.prop(scene, "qtquick3d_glow_intensity", text="Intensity")
                row = glow_box.row(align=True)
                row.prop(scene, "qtquick3d_glow_strength", text="Strength")
                row.prop(scene, "qtquick3d_glow_bloom", text="Bloom")
                row = glow_box.row(align=True)
                row.prop(scene, "qtquick3d_glow_quality_high", text="High Quality")
                row.prop(scene, "qtquick3d_glow_use_bicubic_upscale", text="Bicubic Upscale")
                
                # 镜头光晕
                lens_box = extended_box.box()
                lens_box.label(text="Lens Flare:")
                row = lens_box.row(align=True)
                row.prop(scene, "qtquick3d_lens_flare_enabled", text="Enable Lens Flare")
                row.prop(scene, "qtquick3d_lens_flare_ghost_count", text="Ghost Count")
                row = lens_box.row(align=True)
                row.prop(scene, "qtquick3d_lens_flare_ghost_dispersal", text="Ghost Dispersal")
                row.prop(scene, "qtquick3d_lens_flare_blur_amount", text="Blur Amount")
                
                # LUT设置
                lut_box = extended_box.box()
                lut_box.label(text="LUT Settings:")
                row = lut_box.row(align=True)
                row.prop(scene, "qtquick3d_lut_enabled", text="Enable LUT")
                row.prop(scene, "qtquick3d_lut_size", text="LUT Size")
                row = lut_box.row(align=True)
                row.prop(scene, "qtquick3d_lut_filter_alpha", text="Filter Alpha")
                row.prop(scene, "qtquick3d_lut_texture", text="LUT Texture")
                
                # 暗角效果
                vignette_box = extended_box.box()
                vignette_box.label(text="Vignette:")
                row = vignette_box.row(align=True)
                row.prop(scene, "qtquick3d_vignette_enabled", text="Enable Vignette")
                row.prop(scene, "qtquick3d_vignette_strength", text="Strength")
                row = vignette_box.row(align=True)
                row.prop(scene, "qtquick3d_vignette_radius", text="Radius")
                row.prop(scene, "qtquick3d_vignette_color", text="Color")
                
                # 其他效果
                other_box = extended_box.box()
                other_box.label(text="Other Effects:")
                row = other_box.row(align=True)
                row.prop(scene, "qtquick3d_dithering_enabled", text="Dithering")
                row.prop(scene, "qtquick3d_fxaa_enabled", text="FXAA")
            
            # WASD控制器设置
            wasd_box = scene_settings_box.box()
            wasd_box.label(text="WASD Controller:")
            row = wasd_box.row(align=True)
            row.prop(scene, "qtquick3d_wasd_enabled", text="Enable WASD Controller")
            
            if getattr(scene, "qtquick3d_wasd_enabled", True):
                # 基础速度设置
                speed_box = wasd_box.box()
                speed_box.label(text="Speed Settings:")
                row = speed_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_speed", text="Base Speed")
                row.prop(scene, "qtquick3d_wasd_shift_speed", text="Shift Speed")
                
                # 方向速度设置
                direction_box = wasd_box.box()
                direction_box.label(text="Direction Speeds:")
                row = direction_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_forward_speed", text="Forward")
                row.prop(scene, "qtquick3d_wasd_back_speed", text="Back")
                row = direction_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_left_speed", text="Left")
                row.prop(scene, "qtquick3d_wasd_right_speed", text="Right")
                row = direction_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_up_speed", text="Up")
                row.prop(scene, "qtquick3d_wasd_down_speed", text="Down")
                
                # 鼠标控制设置
                mouse_box = wasd_box.box()
                mouse_box.label(text="Mouse Controls:")
                row = mouse_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_mouse_enabled", text="Mouse Enabled")
                row = mouse_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_x_speed", text="X Speed")
                row.prop(scene, "qtquick3d_wasd_y_speed", text="Y Speed")
                row = mouse_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_x_invert", text="X Invert")
                row.prop(scene, "qtquick3d_wasd_y_invert", text="Y Invert")
                
                # 键盘控制设置
                keyboard_box = wasd_box.box()
                keyboard_box.label(text="Keyboard Controls:")
                row = keyboard_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_keys_enabled", text="Keys Enabled")
                row = keyboard_box.row(align=True)
                row.prop(scene, "qtquick3d_wasd_accepted_buttons", text="Accepted Buttons")

        # Debug 折叠面板
        debug_box = layout.box()
        debug_box.prop(scene, "show_debug_options", icon="TRIA_DOWN" if getattr(scene, "show_debug_options", False) else "TRIA_RIGHT", emboss=False, text="Debug Options")

        if getattr(scene, "show_debug_options", False):
            # QML调试模式切换
         #   debug_box.label(text="QML Debug:")
            row = debug_box.row()
            row.operator("qt_quick3d.toggle_debug_mode", text="Toggle QML Debug Mode")
            
            # IBL测试
          #  debug_box.label(text="IBL Testing:")
            row = debug_box.row()
            row.operator("qt_quick3d.test_ibl_copy", text="Test IBL Copy")
            
            # 其他调试功能可以在这里添加
          #  debug_box.label(text="Other Debug Tools:")
            row = debug_box.row()
            #Save .gltf and .blend into base_dir/source scene
            row.operator("qt_quick3d.save_source_scene",text="Save source scene")
            row = debug_box.row()
            row.operator("qt_quick3d.open_workspace_folder",text="Open workspace folder")
            
            # QMLProject 信息显示（如果检测到）
            qmlproject_path = getattr(scene, "qmlproject_path", None)
            if qmlproject_path:
                debug_box.separator()
                debug_box.label(text="QMLProject Info:")
                
                box = debug_box.box()
                box.label(text=f"QMLProject: {os.path.basename(qmlproject_path)}", icon='FILE')
                
                # 资源文件夹选择下拉框（选择后自动设置工作空间）
                row = debug_box.row()
                row.prop(scene, "qmlproject_assets_folder", text="Asset Folder")
                
                # 手动设置工作空间按钮（可选，下拉框已自动设置）
                row = debug_box.row()
                asset_folder = scene.qmlproject_assets_folder
                row.enabled = asset_folder not in ["NONE", "EMPTY", "ERROR"]
                row.operator("qt_quick3d.set_workspace_from_asset", text="Refresh Workspace", icon='FILE_REFRESH')

        # 显示一些状态信息
        # layout.separator()
        # layout.label(text="Status: Ready")
        # layout.label(text="Qt Version: 6.9")
        # layout.label(text="Quick3D: Available") #TODO尚需检测环境
        
        # 显示场景信息
        # 注意：qt_quick3d_engine 已被移除，场景信息功能已集成到 qt_quick3d_integration_pyside6 中
        
        # 检查是否需要重启
        # try:
        #     addon_prefs = context.preferences.addons.get(__name__)
        #     if addon_prefs and addon_prefs.preferences.restart_needed:
        #         layout.separator()
        #         box = layout.box()
        #         box.label(text="⚠️ Restart Required")
        #         box.label(text="PySide6 was just installed. Please restart Blender.")
        #         box.operator("qt_quick3d.restart_blender", text="Restart Blender Now")
        # except:
        #     pass
        
        # 添加重启按钮（用于刷新模块状态）
        # layout.separator()
        # layout.operator("qt_quick3d.restart_blender", text="Restart Blender")

class QT_QUICK3D_OT_open_window(Operator):
    """Open Qt6.9 Quick3D Window"""
    bl_idname = "qt_quick3d.open_window"
    bl_label = "Open Quick3D Window"
    bl_description = "Open Quick3D window using the main integration module"
    
    def execute(self, context):
        try:
            print("INFO: 启动Quick3D窗口...")
            
            # 调用主要的Quick3D窗口启动函数
            if hasattr(qt_quick3d_integration, 'show_quick3d_window'):
                success = qt_quick3d_integration.show_quick3d_window()
                if success:
                    self.report({'INFO'}, "Quick3D window opened successfully!")
                    print("INFO: Quick3D窗口启动成功")
                else:
                    self.report({'ERROR'}, "Failed to open Quick3D window")
                    print("ERROR: Quick3D窗口启动失败")
            else:
                self.report({'ERROR'}, "Quick3D integration module not available")
                print("ERROR: Quick3D集成模块不可用")
                
        except Exception as e:
            error_msg = f"Failed to open Quick3D window: {str(e)}"
            self.report({'ERROR'}, error_msg)
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
        
        return {'FINISHED'}

class QT_QUICK3D_OT_toggle_debug_mode(Operator):
    """Toggle QML Debug Mode"""
    bl_idname = "qt_quick3d.toggle_debug_mode"
    bl_label = "Toggle QML Debug Mode"
    bl_description = "Toggle QML debug mode to show/hide full QML content in logs"
    
    def execute(self, context):
        try:
            # 导入qml_handler模块
            from . import qml_handler
            
            # 检查当前调试模式状态
            current_mode = qml_handler.DEFAULT_DEBUG_MODE
            
            if current_mode:
                # 当前是调试模式，切换到简化模式
                qml_handler.disable_qml_debug_mode()
                self.report({'INFO'}, "QML Debug Mode: OFF (Simplified logs)")
            else:
                # 当前是简化模式，切换到调试模式
                qml_handler.enable_qml_debug_mode()
                self.report({'INFO'}, "QML Debug Mode: ON (Full QML content)")
                
        except Exception as e:
            error_msg = f"Failed to toggle debug mode: {str(e)}"
            self.report({'ERROR'}, error_msg)
            print(f"ERROR: {error_msg}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_set_render_engine(Operator):
    """Set Qt Quick3D as the current render engine"""
    bl_idname = "qt_quick3d.set_render_engine"
    bl_label = "Set as Render Engine"
    
    def execute(self, context):
        try:
            # 设置渲染引擎为Qt Quick3D
            context.scene.render.engine = 'QUICK3D'
            self.report({'INFO'}, "Qt Quick3D render engine activated!")
            
            # 显示渲染设置面板
         #   bpy.ops.screen.area_split(direction='VERTICAL', factor=0.7)
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set render engine: {str(e)}")
        
        return {'FINISHED'}



# Balsam转换器操作符
class QT_QUICK3D_OT_balsam_convert_scene(Operator):
    """Convert current scene to QML using Balsam converter"""
    bl_idname = "qt_quick3d.balsam_convert_scene"
    bl_label = "Convert with Balsam"
    bl_description = "Convert current Blender scene to QML using Balsam converter"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            from . import ibl_mappling
            
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            # 优先使用工作空间路径
            work_space = getattr(context.scene, 'work_space_path', None)
            if work_space:
                converter.set_custom_output_dir(work_space)
                print(f"✅ 使用工作空间路径: {work_space}")
            
            # 在转换之前复制world图像
            print("🔄 开始复制World图像到输出目录...")
            copy_result = ibl_mappling.copy_all_world_images_to_balsam_output()
            
            if copy_result['surface_copied']:
                self.report({'INFO'}, f"Surface IBL图像已复制: {os.path.basename(copy_result['surface_image_dest'])}")
                print(f"✅ Surface IBL图像复制成功: {copy_result['surface_image_dest']}")
            
            if copy_result['environment_copied']:
                self.report({'INFO'}, f"Environment IBL图像已复制: {os.path.basename(copy_result['environment_image_dest'])}")
                print(f"✅ Environment IBL图像复制成功: {copy_result['environment_image_dest']}")
            
            if not copy_result['surface_copied'] and not copy_result['environment_copied']:
                print("ℹ️ 没有World图像需要复制")
            
            # 执行Balsam转换
            success = converter.convert(keep_files=True, copy_to_docs=False)
            
            if success:
                self.report({'INFO'}, "Balsam conversion successful!")
                paths = converter.get_output_paths()
                self.report({'INFO'}, f"Output directory: {paths['base_dir']}")
                
                # 显示IBL图像复制结果
                if copy_result['surface_copied'] or copy_result['environment_copied']:
                    ibl_files = ibl_mappling.get_ibl_image_paths_in_output()
                    if ibl_files['iblimage_files']:
                        self.report({'INFO'}, f"IBL图像文件: {len(ibl_files['iblimage_files'])} 个")
                        for file_path in ibl_files['iblimage_files']:
                            print(f"  📁 IBL文件: {os.path.basename(file_path)}")
            else:
                self.report({'ERROR'}, "Balsam conversion failed")
                
        except Exception as e:
            self.report({'ERROR'}, f"Conversion failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return {'FINISHED'}


class QT_QUICK3D_OT_test_ibl_copy(Operator):
    """Test IBL image copy functionality"""
    bl_idname = "qt_quick3d.test_ibl_copy"
    bl_label = "Test IBL Copy"
    bl_description = "Test copying world images to balsam output directory"
    
    def execute(self, context):
        try:
            from . import ibl_mappling
            
            print("🧪 开始测试IBL图像复制功能...")
            print("=" * 60)
            
            # 1. 获取world图像信息
            print("1. 获取World图像信息:")
            world_info = ibl_mappling.get_world_surface_connected_image_paths()
            
            if not world_info['surface_image'] and not world_info['environment_image']:
                self.report({'WARNING'}, "当前World没有连接图像")
                print("⚠️ 当前World没有连接图像")
                return {'CANCELLED'}
            
            # 2. 获取balsam输出目录
            print("\n2. 获取Balsam输出目录:")
            output_dir = ibl_mappling.get_balsam_output_base_dir()
            if not output_dir:
                self.report({'ERROR'}, "无法获取Balsam输出目录")
                print("❌ 无法获取Balsam输出目录")
                return {'CANCELLED'}
            
            # 3. 复制world图像
            print("\n3. 复制World图像到Balsam输出目录:")
            copy_result = ibl_mappling.copy_all_world_images_to_balsam_output()
            
            # 4. 显示结果
            print("\n4. 复制结果:")
            success_count = 0
            
            if copy_result['surface_copied']:
                success_count += 1
                self.report({'INFO'}, f"Surface IBL图像已复制: {os.path.basename(copy_result['surface_image_dest'])}")
                print(f"✅ Surface IBL图像复制成功: {copy_result['surface_image_dest']}")
            
            if copy_result['environment_copied']:
                success_count += 1
                self.report({'INFO'}, f"Environment IBL图像已复制: {os.path.basename(copy_result['environment_image_dest'])}")
                print(f"✅ Environment IBL图像复制成功: {copy_result['environment_image_dest']}")
            
            if success_count == 0:
                self.report({'WARNING'}, "没有图像被复制")
                print("⚠️ 没有图像被复制")
            else:
                self.report({'INFO'}, f"成功复制 {success_count} 个IBL图像文件")
                print(f"🎉 成功复制 {success_count} 个IBL图像文件")
            
            # 5. 显示输出目录中的IBL文件
            print("\n5. 输出目录中的IBL文件:")
            ibl_files = ibl_mappling.get_ibl_image_paths_in_output()
            if ibl_files['iblimage_files']:
                print(f"   找到 {len(ibl_files['iblimage_files'])} 个IBL文件:")
                for file_path in ibl_files['iblimage_files']:
                    print(f"   📁 {os.path.basename(file_path)}")
            else:
                print("   ℹ️ 输出目录中没有IBL文件")
            
            print("\n✅ IBL图像复制测试完成！")
            return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"IBL复制测试失败: {str(e)}")
            print(f"❌ IBL复制测试失败: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class QT_QUICK3D_OT_balsam_open_output(Operator):
    """Open output folder"""
    bl_idname = "qt_quick3d.balsam_open_output"
    bl_label = "Open Output Folder"
    bl_description = "Open the converter's output folder"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            converter.setup_environment()
            
            if converter.open_output_folder():
                self.report({'INFO'}, "Output folder opened")
            else:
                self.report({'ERROR'}, "Could not open output folder")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_open_gltf(Operator):
    """Open GLTF folder"""
    bl_idname = "qt_quick3d.balsam_open_gltf"
    bl_label = "Open GLTF Folder"
    bl_description = "Open the folder containing GLTF files"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            converter.setup_environment()
            
            if converter.open_gltf_folder():
                self.report({'INFO'}, "GLTF folder opened")
            else:
                self.report({'ERROR'}, "Could not open GLTF folder")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_open_qml(Operator):
    """Open QML folder"""
    bl_idname = "qt_quick3d.balsam_open_qml"
    bl_label = "Open QML Folder"
    bl_description = "Open the QML output folder"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            converter.setup_environment()
            
            if converter.open_qml_folder():
                self.report({'INFO'}, "QML folder opened")
            else:
                self.report({'ERROR'}, "Could not open QML folder")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_cleanup(Operator):
    """Clean output files"""
    bl_idname = "qt_quick3d.balsam_cleanup"
    bl_label = "Clean Output Files"
    bl_description = "Clean old output files to free space"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            converter.setup_environment()
            converter.cleanup()
            
            self.report({'INFO'}, "Output files cleaned")
                
        except Exception as e:
            self.report({'ERROR'}, f"Cleanup failed: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_save_source_scene(Operator):
    """Save source scene (.gltf and .blend) to workspace/source_scene folder"""
    bl_idname = "qt_quick3d.save_source_scene"
    bl_label = "Save Source Scene"
    bl_description = "Save .gltf and .blend files to workspace/source_scene folder"
    
    def execute(self, context):
        try:
            from . import path_manager, balsam_gltf_converter
            import os
            import bpy
            
            pm = path_manager.get_path_manager()
            workspace_dir = pm.output_base_dir
            
            # 创建source_scene文件夹
            source_scene_dir = os.path.join(workspace_dir, "source scene")
            os.makedirs(source_scene_dir, exist_ok=True)
            print(f"📁 Source scene directory: {source_scene_dir}")
            
            # 保存.blend文件
            blend_filepath = bpy.data.filepath
            if blend_filepath:
                blend_filename = os.path.basename(blend_filepath)
            else:
                blend_filename = "scene.blend"
            
            blend_save_path = os.path.join(source_scene_dir, blend_filename)
            bpy.ops.wm.save_as_mainfile(filepath=blend_save_path, copy=True)
            print(f"✅ Blend file saved: {blend_save_path}")
            
            # 导出.gltf文件到source_scene文件夹
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            # 临时修改输出目录为source_scene
            original_output_dir = converter.output_base_dir
            converter.output_base_dir = source_scene_dir
            
            if converter.export_scene_to_gltf():
                print(f"✅ GLTF file saved: {converter.gltf_path}")
                self.report({'INFO'}, f"Source scene saved to: {source_scene_dir}")
            else:
                self.report({'ERROR'}, "Failed to export GLTF")
                
            # 恢复原始输出目录
            converter.output_base_dir = original_output_dir
                
        except Exception as e:
            print(f"❌ Save source scene failed: {e}")
            self.report({'ERROR'}, f"Failed to save source scene: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_open_workspace_folder(Operator):
    """Open workspace folder in file explorer"""
    bl_idname = "qt_quick3d.open_workspace_folder"
    bl_label = "Open Workspace Folder"
    bl_description = "Open the workspace/output folder in file explorer"
    
    def execute(self, context):
        try:
            from . import path_manager
            pm = path_manager.get_path_manager()
            
            if pm.open_output_folder():
                self.report({'INFO'}, "Workspace folder opened")
            else:
                self.report({'ERROR'}, "Could not open workspace folder")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
        
        return {'FINISHED'}

# QT_QUICK3D_OT_set_qmlproject_path 已合并到 QT_QUICK3D_OT_balsam_set_work_space
# 保留定义以防止旧代码引用错误
class QT_QUICK3D_OT_set_qmlproject_path(Operator):
    """Deprecated: Use 'Set Work Space' instead (auto-detects .qmlproject files)"""
    bl_idname = "qt_quick3d.set_qmlproject_path"
    bl_label = "Set QMLProject Path (Deprecated)"
    bl_description = "Deprecated: Use 'Set Work Space' instead. It auto-detects .qmlproject files"
    
    def execute(self, context):
        self.report({'WARNING'}, "This function is deprecated. Please use 'Set Work Space' button instead.")
        print("⚠️ QT_QUICK3D_OT_set_qmlproject_path 已弃用，请使用 'Set Work Space' 按钮")
        return {'CANCELLED'}

class QT_QUICK3D_OT_set_workspace_from_asset(Operator):
    """Set workspace to selected asset folder"""
    bl_idname = "qt_quick3d.set_workspace_from_asset"
    bl_label = "Set Workspace to Asset Folder"
    bl_description = "Set the workspace path to the selected asset folder"
    
    def execute(self, context):
        try:
            from . import qmlproject_helper, path_manager
            
            scene = context.scene
            asset_folder = scene.qmlproject_assets_folder
            
            if asset_folder in ["NONE", "EMPTY", "ERROR"]:
                self.report({'WARNING'}, "Please select a valid asset folder")
                return {'CANCELLED'}
            
            # 获取 helper 实例
            helper = qmlproject_helper.get_qmlproject_helper()
            
            if not helper.qtquick3d_assets_dir:
                self.report({'ERROR'}, "QMLProject not initialized. Please set QMLProject path first")
                return {'CANCELLED'}
            
            # 构建完整路径
            asset_path = os.path.join(helper.qtquick3d_assets_dir, asset_folder)
            
            if not os.path.exists(asset_path):
                os.makedirs(asset_path, exist_ok=True)
                print(f"📁 创建资源文件夹: {asset_path}")
            
            # 设置工作空间
            pm = path_manager.get_path_manager()
            pm.set_work_space(asset_path)
            scene.work_space_path = asset_path
            
            self.report({'INFO'}, f"Workspace set to: {asset_folder}")
            print(f"✅ 工作空间设置为: {asset_path}")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set workspace: {str(e)}")
            print(f"❌ 设置工作空间失败: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_set_work_space(Operator):
    """Set work space directory (auto-detects QMLProject files)"""
    bl_idname = "qt_quick3d.balsam_set_work_space"
    bl_label = "Set Work Space"
    bl_description = "Set working directory for GLTF and QML files. Auto-detects .qmlproject files in the directory"
    
    directory: StringProperty(
        name="Work Space Directory",
        description="Directory for GLTF and QML files",
        default="",
        subtype='DIR_PATH'
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            from . import qmlproject_helper, path_manager
            
            if not self.directory:
                self.report({'ERROR'}, "No directory selected")
                return {'CANCELLED'}
            
            if not os.path.exists(self.directory):
                self.report({'ERROR'}, f"Directory does not exist: {self.directory}")
                return {'CANCELLED'}
            
            # 检查目录中是否有 .qmlproject 文件
            qmlproject_files = [f for f in os.listdir(self.directory) if f.endswith('.qmlproject')]
            
            if qmlproject_files:
                # 找到 .qmlproject 文件，使用 QMLProject 模式
                qmlproject_path = os.path.join(self.directory, qmlproject_files[0])
                print(f"🔍 检测到 QMLProject 文件: {qmlproject_path}")
                
                # 清除缓存
                qmlproject_helper.clear_assets_cache()
                
                # 获取 helper 实例并设置路径
                helper = qmlproject_helper.get_qmlproject_helper()
                if helper.setup(qmlproject_path):
                    # 保存到场景属性
                    context.scene.qmlproject_path = qmlproject_path
                    
                    # 设置工作空间为 qmlproject_assets_path
                    pm = path_manager.get_path_manager()
                    if helper.qmlproject_assets_path:
                        pm.set_work_space(helper.qmlproject_assets_path)
                        context.scene.work_space_path = helper.qmlproject_assets_path
                        
                        self.report({'INFO'}, f"QMLProject detected! Workspace set to: {os.path.basename(helper.qmlproject_assets_path)}")
                        print(f"✅ QMLProject模式: 工作空间 = {helper.qmlproject_assets_path}")
                        print(f"📦 找到 {len(helper.assets_folders)} 个资源文件夹")
                    else:
                        self.report({'WARNING'}, "QMLProject initialized but assets path not set")
                else:
                    self.report({'ERROR'}, "Failed to initialize QMLProject")
                    return {'CANCELLED'}
            else:
                # 没有 .qmlproject 文件，使用普通工作空间模式
                print(f"📁 未检测到 QMLProject 文件，使用普通工作空间模式")
                
                # 清除 QMLProject 相关设置
                context.scene.qmlproject_path = ""
                helper = qmlproject_helper.get_qmlproject_helper()
                helper.clear()  # 清除 helper 中的所有 QMLProject 设置
                
                # 设置工作空间
                pm = path_manager.get_path_manager()
                pm.set_work_space(self.directory)
                context.scene.work_space_path = self.directory
                
                self.report({'INFO'}, f"Work space set to: {self.directory}")
                print(f"✅ 普通模式: 工作空间 = {self.directory}")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set work space: {str(e)}")
            print(f"❌ 设置工作空间失败: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_set_gltf_path(Operator):
    """Set custom GLTF file path"""
    bl_idname = "qt_quick3d.balsam_set_gltf_path"
    bl_label = "Set GLTF Path"
    bl_description = "Set custom GLTF file path for conversion"
    
    filepath: StringProperty(
        name="GLTF File",
        description="Select GLTF file to convert",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            if converter.set_custom_gltf_path(self.filepath):
                self.report({'INFO'}, f"GLTF path set to: {self.filepath}")
                # 保存到场景属性中
                context.scene.balsam_gltf_path = self.filepath
            else:
                self.report({'ERROR'}, "Failed to set GLTF path")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set GLTF path: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_set_output_dir(Operator):
    """Set custom output directory"""
    bl_idname = "qt_quick3d.balsam_set_output_dir"
    bl_label = "Set Output Directory"
    bl_description = "Set custom output directory for QML files"
    
    directory: StringProperty(
        name="Output Directory",
        description="Select output directory for QML files",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            if converter.set_custom_output_dir(self.directory):
                self.report({'INFO'}, f"Output directory set to: {self.directory}")
                # 保存到场景属性中
                context.scene.balsam_output_dir = self.directory
            else:
                self.report({'ERROR'}, "Failed to set output directory")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set output directory: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_search_local_balsam(Operator):
    """搜索本地balsam版本"""
    bl_idname = "qt_quick3d.search_local_balsam"
    bl_label = "Search Local Balsam"
    bl_description = "Search for local balsam.exe in C:/Qt and save to cache"
    
    def execute(self, context):
        try:
            print("🔍 开始搜索本地balsam版本...")
            
            # 扫描C:/Qt
            candidates = path_manager.scan_qt_balsam_paths()
            
            if not candidates:
                self.report({'WARNING'}, "No balsam.exe found in C:/Qt")
                return {'CANCELLED'}
            
            # 更新全局映射
            path_manager.BALSAM_PATH_MAP = {}
            for i, exe in enumerate(candidates):
                key = f"QT_{i}"
                path_manager.BALSAM_PATH_MAP[key] = exe
            
            # 重置缓存加载标志
            path_manager.BALSAM_CACHE_LOADED = False
            
            # 保存到缓存文件
            if path_manager.save_balsam_cache():
                self.report({'INFO'}, f"Found {len(candidates)} balsam versions and saved to cache")
                
                # 强制更新balsam_version枚举属性
                if hasattr(context.scene, 'balsam_version'):
                    # 触发枚举更新
                    context.scene.balsam_version = context.scene.balsam_version
                
                # 刷新界面
                for area in context.screen.areas:
                    area.tag_redraw()
            else:
                self.report({'ERROR'}, "Failed to save balsam cache")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Search failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class QT_QUICK3D_OT_add_balsam_path(Operator):
    """手动添加 balsam 可执行路径并写入枚举/缓存"""
    bl_idname = "qt_quick3d.add_balsam_path"
    bl_label = "Add Balsam Path"
    bl_description = "Pick a balsam.exe and add it to versions list"

    filepath: StringProperty(subtype='FILE_PATH', default="")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            path = self.filepath
            if not path:
                self.report({'WARNING'}, "No file selected")
                return {'CANCELLED'}

            key = path_manager.add_balsam_path(path)

            # 强制刷新枚举并选择刚添加的项
            if hasattr(context.scene, 'balsam_version'):
                context.scene.balsam_version = key

            # 刷新界面
            for area in context.screen.areas:
                area.tag_redraw()

            self.report({'INFO'}, f"Added balsam: {key}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_convert_existing(Operator):
    """Convert existing GLTF file"""
    bl_idname = "qt_quick3d.balsam_convert_existing"
    bl_label = "Convert Existing GLTF"
    bl_description = "Convert existing GLTF file to QML"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            from . import ibl_mappling
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            # 优先使用工作空间路径，回退到旧属性
            work_space = getattr(context.scene, 'work_space_path', None)
            gltf_path = getattr(context.scene, 'balsam_gltf_path', None)
            output_dir = work_space or getattr(context.scene, 'balsam_output_dir', None)
            
            if not gltf_path:
                self.report({'ERROR'}, "Please set GLTF path first")
                return {'CANCELLED'}
            
            if work_space:
                print(f"✅ 使用工作空间路径: {work_space}")
            
            # 在转换之前复制world图像
            print("🔄 开始复制World图像到输出目录...")
            copy_result = ibl_mappling.copy_all_world_images_to_balsam_output()
            
            if copy_result['surface_copied']:
                self.report({'INFO'}, f"Surface IBL图像已复制: {os.path.basename(copy_result['surface_image_dest'])}")
                print(f"✅ Surface IBL图像复制成功: {copy_result['surface_image_dest']}")
            
            if copy_result['environment_copied']:
                self.report({'INFO'}, f"Environment IBL图像已复制: {os.path.basename(copy_result['environment_image_dest'])}")
                print(f"✅ Environment IBL图像复制成功: {copy_result['environment_image_dest']}")
            
            if not copy_result['surface_copied'] and not copy_result['environment_copied']:
                print("ℹ️ 没有World图像需要复制")
            
            success = converter.convert_existing_gltf(gltf_path, output_dir)
            
            if success:
                self.report({'INFO'}, "GLTF conversion successful!")
                paths = converter.get_output_paths()
                self.report({'INFO'}, f"Output directory: {paths['qml_dir']}")
            else:
                self.report({'ERROR'}, "GLTF conversion failed")
                
        except Exception as e:
            self.report({'ERROR'}, f"Conversion failed: {str(e)}")
        
        return {'FINISHED'}


class RENDER_PT_qt_quick3d_qml(Panel):
    """Qt Quick3D QML Functions Panel in Render Properties"""
    bl_label = "QML Functions"
    bl_idname = "RENDER_PT_qt_quick3d_qml"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # 移除父面板依赖，使其作为独立面板显示
    
    @classmethod 
    def poll(cls, context):
        return context.scene.render.engine == 'QUICK3D'
    
    def draw(self, context):
        layout = self.layout
        
        # QML转换功能
        box = layout.box()
        box.label(text="Scene to QML Conversion")
        
        # GLTF到QML转换按钮
        layout.operator(
            "qt_quick3d.convert_gltf_to_qml",
            text="Convert Scene to QML",
        )
        
        # 说明文字
        box = layout.box()
        box.label(text="This will:")
        box.label(text="• Export scene to GLTF format")
        box.label(text="• Convert using pyside6-balsam")
        box.label(text="• Generate QML and mesh files")
        box.label(text="• Save to Documents folder")
        
        # 快速访问按钮
        layout.separator()
        layout.label(text="Quick Access:")
        
        row = layout.row(align=True)
        row.operator(
            "qt_quick3d.open_window",
            text="Open Quick3D Window"
        )
        
        row.operator(
            "qt_quick3d.set_render_engine",
            text="Set as Render Engine"
        )
        
        # Balsam转换器集成
        layout.separator()
        box = layout.box()
        box.label(text="Balsam Converter", icon='EXPORT')
        
        # 工作空间设置
        box = layout.box()
        box.label(text="Work Space Settings")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_set_work_space", text="Set Work Space")
        
        # 转换操作
        box = layout.box()
        box.label(text="Conversion")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_convert_scene", text="Convert Scene to QML")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_convert_existing", text="Convert Existing GLTF")
        

        
        # 文件访问
        box = layout.box()
        box.label(text="Output Access")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_open_output", text="Open Output Folder")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_open_gltf", text="Open GLTF Folder")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_open_qml", text="Open QML Folder")
        
        # 维护
        box = layout.box()
        box.label(text="Maintenance")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_cleanup", text="Clean Output Files")
        
        # Quick3D窗口
        box = layout.box()
        box.label(text="Quick3D Window")
        
        row = box.row()
        row.operator("qt_quick3d.open_window", text="Open Quick3D Window")


# 注册类
classes = [
    QtQuick3DAddonPreferences,
    ShowPySide6InfoOperator,
    SwitchPySide6InstallationOperator,
    InstallPySide6Operator,
    RestartBlenderOperator,
    VIEW3D_PT_qt_quick3d_panel,
    RENDER_PT_qt_quick3d_qml,
    QT_QUICK3D_OT_open_window,
    QT_QUICK3D_OT_toggle_debug_mode,
    QT_QUICK3D_OT_set_render_engine,
    # Balsam转换器操作符
    QT_QUICK3D_OT_balsam_convert_scene,
    QT_QUICK3D_OT_test_ibl_copy,
    QT_QUICK3D_OT_balsam_convert_existing,
    QT_QUICK3D_OT_balsam_set_work_space,  # 合并后的按钮，自动检测 .qmlproject
    QT_QUICK3D_OT_balsam_set_gltf_path,
    QT_QUICK3D_OT_balsam_set_output_dir,
    QT_QUICK3D_OT_balsam_open_output,
    QT_QUICK3D_OT_balsam_open_gltf,
    QT_QUICK3D_OT_balsam_open_qml,
    QT_QUICK3D_OT_balsam_cleanup,
    QT_QUICK3D_OT_save_source_scene,
    QT_QUICK3D_OT_open_workspace_folder,
    QT_QUICK3D_OT_set_qmlproject_path,  # 保留以防止旧代码引用错误（已弃用）
    QT_QUICK3D_OT_set_workspace_from_asset,
    QT_QUICK3D_OT_search_local_balsam,
    QT_QUICK3D_OT_add_balsam_path,
]

# 不再需要单独的Balsam UI面板
print("✓ Balsam converter will be integrated into render properties panel")

def register():
    # 加载balsam缓存
    path_manager.load_balsam_cache()
    
    # 注册场景属性（包含 work_space_path 等基础属性，并在内部调用 SceneEnvironment 注册）
    register_scene_properties()
    
    # 初始化全局balsam路径（基于默认选择）
    try:
        # 获取默认场景的balsam版本选择
        if hasattr(bpy.context, 'scene') and bpy.context.scene:
            scene = bpy.context.scene
            selected = getattr(scene, 'balsam_version', 'AUTO')
            if selected != 'AUTO':
                chosen = path_manager.BALSAM_PATH_MAP.get(selected)
                if chosen and os.path.exists(chosen):
                    path_manager.set_selected_balsam_path(chosen)
                    print(f"✅ 初始化全局balsam路径: {chosen}")
            else:
                # 使用AUTO选择
                auto_path = path_manager.find_balsam_executable()
                if auto_path:
                    path_manager.set_selected_balsam_path(auto_path)
                    print(f"✅ 初始化AUTO balsam路径: {auto_path}")
    except Exception as e:
        print(f"⚠️ 初始化全局balsam路径失败: {e}")
    
    # 注册主插件类
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 渲染引擎功能暂时禁用
    print("✓ Qt Quick3D plugin registered successfully (render engine disabled)")

def unregister():
    # 渲染引擎功能已禁用
    
    # 注销主插件类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 注销场景属性
    scene_environment.unregister_scene_environment_properties()
    
    # 渲染引擎相关处理器已禁用
    
    print("Qt Quick3D plugin unregistered")

# 渲染引擎相关函数已禁用

if __name__ == "__main__":
    register()
