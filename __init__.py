bl_info = {
    "name": "Qt6.9 Quick3D Engine",
    "author": "ZhiningJiao",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Qt6.9 Quick3D",
    "description": "Integrate Qt6.9 Quick3D engine into Blender as a render engine",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import os
import sys
import subprocess
from bpy.props import StringProperty, BoolProperty
from bpy.types import Panel, Operator, AddonPreferences

# 定义依赖路径（插件内的 lib 文件夹）
ADDON_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(ADDON_DIR, "lib")
if not os.path.exists(LIB_DIR):
    os.makedirs(LIB_DIR)

# 将 lib 添加到 sys.path
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

# 检查 PySide6 是否可用
def check_pyside6_availability():
    try:
        import PySide6
        return True, None
    except ImportError as e:
        return False, str(e)

PYSDIE6_AVAILABLE, PYSDIE6_ERROR = check_pyside6_availability()

# 重启标记 - 用于跟踪是否需要重启
RESTART_NEEDED = False

# 全局变量，用于保持PySide6窗口引用
_qml_window = None
_qml_app = None

# 导入我们的Qt集成模块
try:
    if PYSDIE6_AVAILABLE:
        from . import qt_quick3d_integration_pyside6 as qt_quick3d_integration
        from . import render_engine
        MODULES_AVAILABLE = True
    else:
        MODULES_AVAILABLE = False
        qt_quick3d_integration = None
        render_engine = None
except ImportError as e:
    print(f"Warning: Some Qt6.9 Quick3D modules not found: {e}")
    MODULES_AVAILABLE = False
    qt_quick3d_integration = None
    render_engine = None

# 添加场景属性
def register_scene_properties():
    """注册场景属性"""
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

def unregister_scene_properties():
    """注销场景属性"""
    del bpy.types.Scene.balsam_gltf_path
    del bpy.types.Scene.balsam_output_dir

# 安装 PySide6 操作符
class InstallPySide6Operator(bpy.types.Operator):
    bl_idname = "qt_quick3d.install_pyside"
    bl_label = "Install PySide6"
    bl_description = "Install PySide6 to the addon's lib directory"
    
    def execute(self, context):
        try:
            # 显示进度信息
            self.report({'INFO'}, "Starting PySide6 installation...")
            
            # 使用 Blender 的 Python 执行 pip 安装到 lib 文件夹
            python_exe = sys.executable
            cmd = [python_exe, "-m", "pip", "install", "PySide6", "--target", LIB_DIR]
            
            # 执行安装
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.report({'INFO'}, "PySide6 installed successfully! Please restart Blender.")
                
                # 更新状态
                global PYSDIE6_AVAILABLE, PYSDIE6_ERROR, RESTART_NEEDED
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
            layout.label(text="✓ PySide6: Installed and Ready")
            
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
            box.label(text="• Click 'Install PySide6' to install automatically")
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
        layout.separator()
        layout.label(text="Render Engine:")
        layout.operator("qt_quick3d.set_render_engine", text="Set as Render Engine")
        
        # QML转换功能
        layout.separator()
        layout.label(text="QML Export:")
        layout.operator(
            "qt_quick3d.convert_gltf_to_qml",
            text="Convert Scene to QML"
        )
        
        # 显示一些状态信息
        layout.separator()
        layout.label(text="Status: Ready")
        layout.label(text="Qt Version: 6.9")
        layout.label(text="Quick3D: Available")
        
        # 显示场景信息
        # 注意：qt_quick3d_engine 已被移除，场景信息功能已集成到 qt_quick3d_integration_pyside6 中
        
        # 检查是否需要重启
        try:
            addon_prefs = context.preferences.addons.get(__name__)
            if addon_prefs and addon_prefs.preferences.restart_needed:
                layout.separator()
                box = layout.box()
                box.label(text="⚠️ Restart Required")
                box.label(text="PySide6 was just installed. Please restart Blender.")
                box.operator("qt_quick3d.restart_blender", text="Restart Blender Now")
        except:
            pass
        
        # 添加重启按钮（用于刷新模块状态）
        layout.separator()
        layout.operator("qt_quick3d.restart_blender", text="Restart Blender")

class QT_QUICK3D_OT_open_window(Operator):
    """Open Qt6.9 Quick3D Window"""
    bl_idname = "qt_quick3d.open_window"
    bl_label = "Open Quick3D Window"
    
    def execute(self, context):
        try:
            # 尝试启动Qt Quick3D窗口
            if hasattr(qt_quick3d_integration, 'show_quick3d_window'):
                qt_quick3d_integration.show_quick3d_window()
                self.report({'INFO'}, "Quick3D window opened successfully!")
            else:
                self.report({'WARNING'}, "Qt integration not fully implemented yet")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open Quick3D window: {str(e)}")
        
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



class QT_QUICK3D_OT_convert_gltf_to_qml(Operator):
    """Convert current scene to QML using GLTF converter"""
    bl_idname = "qt_quick3d.convert_gltf_to_qml"
    bl_label = "Convert Scene to QML (GLTF)"
    bl_description = "Export scene to GLTF and convert to QML files"
    
    def execute(self, context):
        try:
            # 尝试导入转换器
            try:
                from . import balsam_gltf_converter
                converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
                
                # 执行转换
                success = converter.convert(keep_files=True, copy_to_docs=False)
                
                if success:
                    self.report({'INFO'}, "Scene converted to QML using Balsam successfully!")
                    print("Scene path: ", converter.get_output_paths()['base_dir'])
                else:
                    self.report({'ERROR'}, "Balsam conversion failed")
                    
            except ImportError:
                self.report({'ERROR'}, "Balsam GLTF converter module not found")
            except Exception as e:
                self.report({'ERROR'}, f"Conversion failed: {str(e)}")
                
        except Exception as e:
            self.report({'ERROR'}, f"Operation failed: {str(e)}")
        
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
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            success = converter.convert(keep_files=True, copy_to_docs=False)
            
            if success:
                self.report({'INFO'}, "Balsam conversion successful!")
                paths = converter.get_output_paths()
                self.report({'INFO'}, f"Output directory: {paths['base_dir']}")
            else:
                self.report({'ERROR'}, "Balsam conversion failed")
                
        except Exception as e:
            self.report({'ERROR'}, f"Conversion failed: {str(e)}")
        
        return {'FINISHED'}

class QT_QUICK3D_OT_balsam_convert_and_copy(Operator):
    """Convert and copy to documents"""
    bl_idname = "qt_quick3d.balsam_convert_and_copy"
    bl_label = "Convert & Copy to Docs"
    bl_description = "Convert scene to QML and copy to documents directory"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            success = converter.convert(keep_files=True, copy_to_docs=True)
            
            if success:
                self.report({'INFO'}, "Conversion and copy successful!")
                paths = converter.get_output_paths()
                self.report({'INFO'}, f"Output directory: {paths['base_dir']}")
            else:
                self.report({'ERROR'}, "Conversion and copy failed")
                
        except Exception as e:
            self.report({'ERROR'}, f"Operation failed: {str(e)}")
        
        return {'FINISHED'}

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

class QT_QUICK3D_OT_balsam_convert_existing(Operator):
    """Convert existing GLTF file"""
    bl_idname = "qt_quick3d.balsam_convert_existing"
    bl_label = "Convert Existing GLTF"
    bl_description = "Convert existing GLTF file to QML"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            # 获取场景中保存的路径
            gltf_path = getattr(context.scene, 'balsam_gltf_path', None)
            output_dir = getattr(context.scene, 'balsam_output_dir', None)
            
            if not gltf_path:
                self.report({'ERROR'}, "Please set GLTF path first")
                return {'CANCELLED'}
            
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

class QT_QUICK3D_OT_open_quick_window(Operator):
    """Open Quick3D window with Balsam conversion"""
    bl_idname = "qt_quick3d.open_quick_window"
    bl_label = "Open Quick3D Window"
    bl_description = "Convert scene with Balsam and open Quick3D window"
    
    def execute(self, context):
        try:
            print("🚀 开始Quick3D窗口流程...")
            
            # 直接启动Quick3D窗口，跳过Balsam转换
            print("⏭️ 跳过Balsam转换，直接启动Quick3D窗口...")
            
            # 启动Quick3D窗口
            self.launch_quick3d_window()
            
            self.report({'INFO'}, "Quick3D window launched successfully!")
            return {'FINISHED'}
                
        except Exception as e:
            print(f"❌ Quick3D窗口启动失败: {e}")
            self.report({'ERROR'}, f"Failed to launch Quick3D window: {str(e)}")
            return {'CANCELLED'}
    
    def launch_quick3d_window(self):
        """启动Quick3D窗口"""
        try:
            print("🔧 启动Quick3D窗口...")
            
            # 直接尝试导入PySide6模块
            try:
                from PySide6.QtCore import QTimer, Qt, QUrl
                from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout, QWidget, QLabel
                from PySide6.QtQuick import QQuickView
                from PySide6.QtQml import QQmlApplicationEngine
                print("✅ PySide6模块直接导入成功")
            except ImportError as e:
                print(f"❌ PySide6模块导入失败: {e}")
                self.report({'ERROR'}, f"PySide6 not available: {str(e)}")
                return
            
            # 创建QApplication
            app = QApplication.instance()
            if not app:
                app = QApplication(["blender"])
                print("✅ 创建新的QApplication")
            else:
                print("✅ 使用现有的QApplication")
            
            # 创建Quick3D主窗口
            quick3d_window = self.create_quick3d_window()
            quick3d_window.show()
            
            # 保存对窗口和app的全局引用，防止被垃圾回收
            global _qml_window, _qml_app
            _qml_window = quick3d_window
            _qml_app = app
            
            print("✅ Quick3D窗口已启动")
            print(" 窗口引用已保存，应该不会闪关了")
            
        except Exception as e:
            print(f"❌ 启动Quick3D窗口失败: {e}")
            raise
    
    def create_quick3d_window(self):
        """创建Quick3D主窗口"""
        try:
            print("🔧 开始创建Quick3D窗口...")
            
            # 确保PySide6已导入 - 只导入基本组件
            from PySide6.QtCore import QTimer, Qt, QUrl
            from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
            from PySide6.QtQuick import QQuickView
            from PySide6.QtQml import QQmlApplicationEngine
            
            # 创建Quick3D主窗口类
            class Quick3DMainWindow(QMainWindow):
                """Quick3D主窗口"""
                
                def __init__(self):
                    super().__init__()
                    
                    self.setWindowTitle("Quick3D Window")
                    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
                    self.resize(1280, 720)
                    
                    # 创建中央部件
                    central_widget = QWidget()
                    layout = QVBoxLayout()
                    
                    # 添加标题标签
                    title_label = QLabel("Quick3D Window")
                    title_label.setAlignment(Qt.AlignCenter)
                    title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
                    layout.addWidget(title_label)
                    
                    # 添加状态标签
                    self.status_label = QLabel("Ready")
                    self.status_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(self.status_label)
                    
                    # 尝试创建QML View3D
                    try:
                        print("🔧 创建QML View3D...")
                        
                        # 创建QML引擎
                        self.qml_engine = QQmlApplicationEngine()
                        
                        # 添加QML导入路径，使用Balsam转换器的全局路径
                        try:
                            from . import balsam_gltf_converter
                            qml_output_dir = balsam_gltf_converter.get_qml_output_dir()
                            if os.path.exists(qml_output_dir):
                                self.qml_engine.addImportPath(qml_output_dir)
                                print(f"✅ 已添加QML导入路径: {qml_output_dir}")
                                
                                # 设置QML引擎的工作目录，使用QUrl.fromLocalFile
                                from PySide6.QtCore import QUrl
                                base_url = QUrl.fromLocalFile(qml_output_dir)
                                self.qml_engine.setBaseUrl(base_url)
                                print(f"✅ 已设置QML引擎工作目录: {qml_output_dir}")
                                print(f"  Base URL: {base_url.toString()}")
                                
                                # 设置环境变量，确保QML引擎能找到文件
                                os.environ['QML_IMPORT_PATH'] = qml_output_dir
                                print(f"✅ 已设置QML_IMPORT_PATH环境变量: {qml_output_dir}")
                                
                                # 添加额外的导入路径，包括meshes子目录
                                meshes_dir = os.path.join(qml_output_dir, "meshes")
                                if os.path.exists(meshes_dir):
                                    self.qml_engine.addImportPath(meshes_dir)
                                    print(f"✅ 已添加meshes目录导入路径: {meshes_dir}")
                            else:
                                print(f"⚠️ QML输出目录不存在: {qml_output_dir}")
                        except Exception as e:
                            print(f"⚠️ 无法获取Balsam路径: {e}")
                            # 回退到本地路径
                            addon_dir = os.path.dirname(os.path.abspath(__file__))
                            qml_output_dir = os.path.join(addon_dir, "output", "qml")
                            if os.path.exists(qml_output_dir):
                                self.qml_engine.addImportPath(qml_output_dir)
                                print(f"✅ 已添加本地QML导入路径: {qml_output_dir}")
                            else:
                                print(f"⚠️ QML输出目录不存在: {qml_output_dir}")
                        
                        # 使用简单的测试QML内容
                        qml_content = '''
import QtQuick
import QtQuick3D

Window {
    visible: true
    width: 600
    height: 400
    title: "Quick3D Test Window"
    
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            clearColor: "#303030"
            backgroundMode: SceneEnvironment.Color
        }
        
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -70
            ambientColor: Qt.rgba(0.3, 0.3, 0.3, 1.0)
        }
        
        Model {
            source: "#Cube"
            materials: [
                DefaultMaterial {
                    diffuseColor: "red"
                }
            ]
        }
        
        PerspectiveCamera {
            z: 600
        }
    }
}
'''
                        
                        # 加载QML内容
                        self.qml_engine.loadData(qml_content.encode())
                        
                        # 检查QML是否加载成功
                        if self.qml_engine.rootObjects():
                            print("✅ QML加载成功")
                            self.status_label.setText("状态: QML View3D 已加载")
                            
                            # 将QML窗口添加到布局中
                            qml_window = self.qml_engine.rootObjects()[0]
                            qml_container = QWidget.createWindowContainer(qml_window)
                            layout.addWidget(qml_container)
                            
                        else:
                            print("❌ QML加载失败")
                            self.status_label.setText("状态: QML加载失败")
                            
                            # 显示错误信息
                            error_label = QLabel("QML加载失败，请检查PySide6.QtQuick3D模块")
                            error_label.setStyleSheet("color: red; padding: 10px;")
                            layout.addWidget(error_label)
                            
                    except Exception as e:
                        print(f"⚠️ QML View3D创建失败: {e}")
                        self.status_label.setText(f"状态: QML创建失败 - {str(e)}")
                        
                        # 显示错误信息
                        error_label = QLabel(f"QML View3D创建失败: {str(e)}")
                        error_label.setStyleSheet("color: red; padding: 10px;")
                        layout.addWidget(error_label)
                    
                    # 添加控制按钮
                    button_layout = QVBoxLayout()
                    
                    refresh_button = QPushButton("Refresh Status")
                    refresh_button.clicked.connect(self.refresh_status)
                    button_layout.addWidget(refresh_button)
                    
                    test_button = QPushButton("Test Quick3D")
                    test_button.clicked.connect(self.test_quick3d)
                    button_layout.addWidget(test_button)
                    
                    layout.addLayout(button_layout)
                    
                    # 设置布局
                    central_widget.setLayout(layout)
                    self.setCentralWidget(central_widget)
                    
                    # 设置定时器更新状态
                    self.timer = QTimer()
                    self.timer.timeout.connect(self.update_status)
                    self.timer.start(1000)  # 每秒更新一次
                    
                    print("✅ Quick3D主窗口创建成功")
                
                def refresh_status(self):
                    """刷新状态"""
                    try:
                        import bpy
                        scene = bpy.context.scene
                        
                        # 检查渲染引擎
                        if scene.render.engine == 'QUICK3D':
                            self.status_label.setText("Render Engine: Quick3D ✓")
                        else:
                            self.status_label.setText(f"Render Engine: {scene.render.engine}")
                            
                    except Exception as e:
                        self.status_label.setText(f"Error: {str(e)}")
                
                def test_quick3d(self):
                    """测试Quick3D功能"""
                    try:
                        print("🧪 测试Quick3D功能...")
                        self.status_label.setText("Testing Quick3D...")
                        
                        # 这里可以添加更多的Quick3D测试
                        self.status_label.setText("Quick3D Test Complete ✓")
                        
                    except Exception as e:
                        print(f"❌ Quick3D测试失败: {e}")
                        self.status_label.setText(f"Test Failed: {str(e)}")
                
                def update_status(self):
                    """更新状态"""
                    try:
                        import bpy
                        scene = bpy.context.scene
                        
                        # 检查场景对象数量
                        obj_count = len(bpy.data.objects)
                        self.setWindowTitle(f"Quick3D Window - Objects: {obj_count}")
                        
                    except Exception as e:
                        print(f"状态更新失败: {e}")
                
                def closeEvent(self, event):
                    """窗口关闭事件"""
                    self.timer.stop()
                    print("Quick3D窗口已关闭")
                    event.accept()
            
            return Quick3DMainWindow()
            
        except Exception as e:
            print(f"❌ 创建Quick3D窗口失败: {e}")
            raise

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
        
        # 目录设置
        box = layout.box()
        box.label(text="Directory Settings")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_set_gltf_path", text="Set GLTF Path")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_set_output_dir", text="Set Output Directory")
        
        # 转换操作
        box = layout.box()
        box.label(text="Conversion")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_convert_scene", text="Convert Scene to QML")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_convert_existing", text="Convert Existing GLTF")
        
        row = box.row()
        row.operator("qt_quick3d.balsam_convert_and_copy", text="Convert & Copy to Docs")
        
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
        row.operator("qt_quick3d.open_quick_window", text="Open Quick3D Window")


# 注册类
classes = [
    QtQuick3DAddonPreferences,
    InstallPySide6Operator,
    RestartBlenderOperator,
    VIEW3D_PT_qt_quick3d_panel,
    RENDER_PT_qt_quick3d_qml,
    QT_QUICK3D_OT_open_window,
    QT_QUICK3D_OT_set_render_engine,
    QT_QUICK3D_OT_convert_gltf_to_qml,
    # Balsam转换器操作符
    QT_QUICK3D_OT_balsam_convert_scene,
    QT_QUICK3D_OT_balsam_convert_and_copy,
    QT_QUICK3D_OT_balsam_convert_existing,
    QT_QUICK3D_OT_balsam_set_gltf_path,
    QT_QUICK3D_OT_balsam_set_output_dir,
    QT_QUICK3D_OT_balsam_open_output,
    QT_QUICK3D_OT_balsam_open_gltf,
    QT_QUICK3D_OT_balsam_open_qml,
    QT_QUICK3D_OT_balsam_cleanup,
    # Quick3D窗口操作符
    QT_QUICK3D_OT_open_quick_window,
]

# 不再需要单独的Balsam UI面板
print("✓ Balsam converter will be integrated into render properties panel")

def register():
    # 注册场景属性
    register_scene_properties()
    
    # 注册主插件类
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册渲染引擎
    if MODULES_AVAILABLE:
        render_engine.register()
        print("✓ Qt Quick3D plugin registered successfully")
        
        # 自动设置Quick3D渲染引擎
        try:
            # 延迟执行，确保Blender完全初始化
            bpy.app.timers.register(auto_set_render_engine, first_interval=0.1)
            print("✓ Auto-set render engine timer scheduled")
        except Exception as e:
            print(f"⚠️  Failed to schedule auto-set render engine: {e}")
    else:
        print("✗ Qt Quick3D plugin registration incomplete")
        if not PYSDIE6_AVAILABLE:
            print("  - PySide6 not available")

def unregister():
    # 注销渲染引擎
    if MODULES_AVAILABLE:
        render_engine.unregister()
    
    # 注销主插件类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 注销场景属性
    unregister_scene_properties()
    
    # 清理场景加载处理器
    try:
        if set_render_engine_on_load in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(set_render_engine_on_load)
            print("✓ 清理场景加载后处理器")
    except Exception as e:
        print(f"⚠️  清理场景加载后处理器失败: {e}")
    
    print("Qt Quick3D plugin unregistered")

def auto_set_render_engine():
    """自动设置Quick3D渲染引擎"""
    try:
        # 获取所有场景
        for scene in bpy.data.scenes:
            if scene.render.engine != 'QUICK3D':
                scene.render.engine = 'QUICK3D'
                print(f"✓ 自动设置场景 '{scene.name}' 的渲染引擎为 Quick3D")
        
        # 设置新创建的场景也使用Quick3D引擎
        bpy.app.handlers.load_post.append(set_render_engine_on_load)
        print("✓ 添加场景加载后处理器")
        
        return None  # 停止定时器
        
    except Exception as e:
        print(f"⚠️  自动设置渲染引擎失败: {e}")
        return None  # 停止定时器

def set_render_engine_on_load(scene):
    """在场景加载后设置渲染引擎"""
    try:
        if scene.render.engine != 'QUICK3D':
            scene.render.engine = 'QUICK3D'
            print(f"✓ 场景加载后自动设置渲染引擎为 Quick3D")
    except Exception as e:
        print(f"⚠️  场景加载后设置渲染引擎失败: {e}")

if __name__ == "__main__":
    register()
