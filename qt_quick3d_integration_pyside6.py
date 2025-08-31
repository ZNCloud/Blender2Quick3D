#!/usr/bin/env python3
"""
Qt Quick3D PySide6集成模块

这个模块直接使用addon目录中的PySide6库，实现本地依赖管理
这个文件用于显示QML View3D窗口，管理qml。启窗口。设置各种路径，启动Balsam转换器等
"""

import sys
import os
import bpy

# 导入Balsam转换器模块以获取全局路径
try:
    from . import balsam_gltf_converter
    BALSAM_AVAILABLE = True
except ImportError:
    BALSAM_AVAILABLE = False
    print("Warning: Balsam converter not available")

# 导入QML处理器模块
try:
    from . import qml_handler
    QML_HANDLER_AVAILABLE = True
    print("✅ QML处理器模块加载成功")
except ImportError:
    QML_HANDLER_AVAILABLE = False
    print("Warning: QML handler not available")

# 设置PySide6路径
def setup_pyside6_environment():
    """设置PySide6环境"""
    try:
        # 获取插件目录
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        pyside6_dir = os.path.join(plugin_dir, "lib", "PySide6")
        
        if not os.path.exists(pyside6_dir):
            print(f"Warning: PySide6目录不存在: {pyside6_dir}")
            return False
        
        print(f"PySide6目录: {pyside6_dir}")
        
        # 添加PySide6路径到Python路径
        if pyside6_dir not in sys.path:
            sys.path.insert(0, pyside6_dir)
            print(f"Added PySide6 path: {pyside6_dir}")
        
        # 设置Qt环境变量
        qt6_dir = os.path.join(pyside6_dir, "Qt6")
        if os.path.exists(qt6_dir):
            os.environ['QT_DIR'] = qt6_dir
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt6_dir, "plugins")
            os.environ['QT_PLUGIN_PATH'] = os.path.join(qt6_dir, "plugins")
            os.environ['QT_QML_IMPORT_PATH'] = os.path.join(qt6_dir, "qml")
            print(f"Set Qt environment variables: {qt6_dir}")
        
        # 设置DLL搜索路径
        if hasattr(os, 'add_dll_directory'):
            bin_dir = os.path.join(qt6_dir, "bin")
            if os.path.exists(bin_dir):
                try:
                    os.add_dll_directory(bin_dir)
                    print(f"Added DLL directory: {bin_dir}")
                except Exception as e:
                    print(f"Warning: Failed to add DLL directory: {e}")
        
        print("✓ PySide6环境设置完成")
        return True
        
    except Exception as e:
        print(f"✗ PySide6环境设置失败: {e}")
        return False

# 尝试设置PySide6环境
QT_AVAILABLE = False
QUICK3D_AVAILABLE = False

# 先尝试设置环境
if setup_pyside6_environment():
    try:
        # 尝试导入PySide6
        import PySide6
        from PySide6.QtCore import *
        from PySide6.QtGui import *
        from PySide6.QtWidgets import *
        from PySide6.QtQml import *
        from PySide6.QtQuick import *
        
        # 尝试导入Quick3D
        try:
            from PySide6.QtQuick3D import *
            QUICK3D_AVAILABLE = True
            print("✓ PySide6.QtQuick3D 加载成功")
        except ImportError as e:
            print(f"⚠️  PySide6.QtQuick3D 加载失败: {e}")
        
        QT_AVAILABLE = True
        print("✓ PySide6 加载成功")
        
    except ImportError as e:
        print(f"✗ PySide6加载失败: {e}")
        QT_AVAILABLE = False

def show_quick3d_window():
    """显示Quick3D窗口"""
    if not QT_AVAILABLE:
        print("❌ Qt库不可用")
        return False
    
    if not QUICK3D_AVAILABLE:
        print("❌ Quick3D不可用")
        return False
    
    try:
        print("🚀 开始启动QML View3D窗口...")
        
        # 直接尝试导入PySide6模块
        try:
            from PySide6.QtCore import QTimer, Qt, QUrl
            from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout, QWidget, QLabel, QSizePolicy
            from PySide6.QtQuick import QQuickView
            from PySide6.QtQml import QQmlApplicationEngine
            print("✅ PySide6模块直接导入成功")
        except ImportError as e:
            print(f"❌ PySide6模块导入失败: {e}")
            return False
        
        # 创建QApplication
        app = QApplication.instance()
        if not app:
            app = QApplication(["blender"])
            print("✅ 创建新的QApplication")
        else:
            print("✅ 使用现有的QApplication")
        
        # 创建主窗口
        class QMLView3DWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                
                # 保存对app的引用，防止被垃圾回收
                self.app = app
                
                self.setWindowTitle("QML View3D Window")
                self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
                self.resize(800, 600)
                
                # 创建中央部件
                central_widget = QWidget()
                layout = QVBoxLayout()
                
                # 设置布局边距为0，让View3D占满整个窗口
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                
                # 尝试创建QML View3D
                try:
                    print("创建QML View3D...")
                    
                    # 创建QML引擎
                    self.qml_engine = QQmlApplicationEngine()
                    
                                     # 添加QML导入路径，使用Balsam转换器的全局路径
                    if BALSAM_AVAILABLE:
                        try:
                            qml_output_dir = balsam_gltf_converter.get_qml_output_dir()
                            # 尝试使用BASE_DIR作为base URL
                            base_dir = getattr(balsam_gltf_converter, 'BASE_DIR', None)
                            
                            if os.path.exists(qml_output_dir):

                                
                                # 设置Base URL - 直接设置到meshes文件夹
                                meshes_dir = os.path.join(qml_output_dir, "meshes")
                                if os.path.exists(meshes_dir):
                                    # 直接设置Base URL到meshes目录
                                    base_url = QUrl.fromLocalFile(meshes_dir)
                                    self.qml_engine.setBaseUrl(base_url)
                                    print(f"✅ 已设置QML引擎Base URL到meshes目录: {base_url.toString()}")
                                    print(f"  meshes目录: {meshes_dir}")
                                    print(f"  Base URL path: {base_url.path()}")
                                else:
                                    # 回退到原来的方式
                                    base_url = QUrl.fromLocalFile(qml_output_dir)
                                    self.qml_engine.setBaseUrl(base_url)
                                    print(f"⚠️ meshes目录不存在，回退到output目录: {base_url.toString()}")
                                    print(f"  QML输出目录: {qml_output_dir}")
                                
                                # 验证路径设置
                                print(f"🔍 路径验证:")
                                print(f"  当前工作目录: {os.getcwd()}")
                                print(f"  QML Base URL: {base_url.toString()}")
                                print(f"  期望的mesh路径: {os.path.join(qml_output_dir, 'meshes', 'suzanne_mesh.mesh')}")
                                
                            else:
                                print(f"⚠️ QML输出目录不存在: {qml_output_dir}")
                        except Exception as e:
                            print(f"⚠️ 无法获取Balsam路径: {e}")
                            # 回退到本地路径
                            addon_dir = os.path.dirname(os.path.abspath(__file__))
                            qml_output_dir = os.path.join(addon_dir, "output", "qml")
                            if os.path.exists(qml_output_dir):
                                print(f"✅ QML输出目录存在: {qml_output_dir}")
                            else:
                                print(f"⚠️ QML输出目录不存在: {qml_output_dir}")
                    else:
                        # 如果Balsam不可用，使用本地路径
                        addon_dir = os.path.dirname(os.path.abspath(__file__))
                        qml_output_dir = os.path.join(addon_dir, "output")  # 直接使用output目录
                        if os.path.exists(qml_output_dir):
                            print(f"✅ 本地QML输出目录存在: {qml_output_dir}")
                        else:
                            print(f"⚠️ 本地QML输出目录不存在: {qml_output_dir}")
                    # 使用QML处理器获取组装好的QML内容
                    qml_content = None
                    if QML_HANDLER_AVAILABLE:
                        try:
                            print("🔧 使用QML处理器获取组装好的QML内容...")
                            qml_content = qml_handler.get_qml_content_for_integration()
                            if qml_content:
                                print("✅ 成功从QML处理器获取内容")
                            else:
                                print("⚠️ 无法从QML处理器获取内容，使用默认内容")
                        except Exception as e:
                            print(f"⚠️ QML处理器调用失败: {e}")
                    
                    # 如果QML处理器不可用或失败，使用默认内容
                    if not qml_content:
                        print("🔧 使用默认QML内容...")
                        qml_content = '''
import QtQuick
import QtQuick3D

Window {
    visible: true
    width: 1280
    height: 720
    title: "Quick3D View - Default Content"
    
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

        // 简单的立方体模型
        Model {
            source: "#Cube"
            materials: [
                DefaultMaterial {
                    baseColor: Qt.rgba(0.8, 0.8, 0.8, 1.0)
                    cullMode: DefaultMaterial.NoCulling
                    specularAmount: 0.5
                }
            ]
        }
    }
}
'''
                    
                    # 加载QML内容
                    self.qml_engine.loadData(qml_content.encode())
                    
                    print(f"currentWorkDirection:{os.getcwd()}")
                    
                    # 添加路径调试信息
                    if BALSAM_AVAILABLE:
                        try:
                            qml_output_dir = balsam_gltf_converter.get_qml_output_dir()
                            mesh_file = os.path.join(qml_output_dir, "meshes", "suzanne_mesh.mesh")
                            print(f"🔍 路径调试信息:")
                            print(f"  QML输出目录: {qml_output_dir}")
                            print(f"  Mesh文件路径: {mesh_file}")
                            print(f"  Mesh文件存在: {'✅' if os.path.exists(mesh_file) else '❌'}")
                            print(f"  QML内容中的路径: meshes/suzanne_mesh.mesh")
                            print(f"  期望的完整路径: {os.path.abspath(os.path.join(qml_output_dir, 'meshes', 'suzanne_mesh.mesh'))}")
                        except Exception as e:
                            print(f"⚠️ 路径调试失败: {e}")
                    
                    # 检查QML是否加载成功
                    if self.qml_engine.rootObjects():
                        print("✅ QML加载成功")
                        
                        # 将QML窗口添加到布局中，占满整个窗口
                        qml_window = self.qml_engine.rootObjects()[0]
                        qml_container = QWidget.createWindowContainer(qml_window)
                        qml_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                        layout.addWidget(qml_container)
                        
                    else:
                        print("❌ QML加载失败")
                        
                        # 显示错误信息
                        error_label = QLabel("QML加载失败，请检查PySide6.QtQuick3D模块")
                        error_label.setStyleSheet("color: red; padding: 10px;")
                        error_label.setAlignment(Qt.AlignCenter)
                        layout.addWidget(error_label)
                    

                    

                        
                except Exception as e:
                    print(f"⚠️ QML View3D创建失败: {e}")
                    self.status_label.setText(f"状态: QML创建失败 - {str(e)}")
                    
                    # 显示错误信息
                    error_label = QLabel(f"QML View3D创建失败: {str(e)}")
                    error_label.setStyleSheet("color: red; padding: 10px;")
                    layout.addWidget(error_label)
                
                # 设置布局
                central_widget.setLayout(layout)
                self.setCentralWidget(central_widget)
                
                print("✅ QML View3D窗口创建完成")

            
            
            def closeEvent(self, event):
                """窗口关闭事件"""
                print("✅ QML View3D窗口已关闭")
                event.accept()
        
        # 创建并显示窗口
        window = QMLView3DWindow()
        window.show()
        
        # 保存对窗口的全局引用，防止被垃圾回收
        global _qml_window
        _qml_window = window
        
        # 保存对app的全局引用
        global _qml_app
        _qml_app = app
        
        print("🎉 QML View3D窗口启动成功！")
        print("�� 窗口引用已保存，应该不会闪关了")
        return True
        
    except Exception as e:
        print(f"❌ QML View3D窗口启动失败: {e}")
        return False

# 全局变量，用于保持引用
_qml_window = None
_qml_app = None

def create_quick3d_scene():
    """创建Quick3D场景"""
    if not QUICK3D_AVAILABLE:
        print("❌ Quick3D不可用")
        return None
    
    try:
        # 创建场景
        scene = QQuick3D()
        
        # 创建相机
        camera = QQuick3DCamera()
        camera.setPosition(QVector3D(0, 0, 600))
        scene.addChild(camera)
        
        # 创建光源
        light = QQuick3DDirectionalLight()
        light.setPosition(QVector3D(0, 0, 0))
        light.setEulerRotation(QVector3D(0, 0, 0))
        scene.addChild(light)
        
        # 创建立方体
        cube = QQuick3DModel()
        cube.setSource(QUrl.fromLocalFile(""))
        cube.setPosition(QVector3D(0, 0, 0))
        scene.addChild(cube)
        
        print("✓ Quick3D场景创建成功")
        return scene
        
    except Exception as e:
        print(f"✗ 创建Quick3D场景失败: {e}")
        return None

def export_blender_scene_to_qml(context, output_path):
    """将Blender场景导出为QML格式"""
    if not QUICK3D_AVAILABLE:
        print("❌ Quick3D不可用")
        return False
    
    try:
        # 获取Blender场景
        scene = context.scene
        
        # 创建QML内容
        qml_content = '''import QtQuick
import QtQuick3D

Window3D {
    id: window3D
    width: 800
    height: 800
    visible: true
    title: "Blender Scene Export"
    
    View3D {
        id: view3D
        anchors.fill: parent
        
        environment: SceneEnvironment {
            clearColor: "#000000"
            backgroundMode: SceneEnvironment.Color
        }
        
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 600)
            eulerRotation: Qt.vector3d(0, 0, 0)
        }
        
        DirectionalLight {
            id: light
            position: Qt.vector3d(0, 0, 0)
            eulerRotation: Qt.vector3d(0, 0, 0)
            ambientColor: Qt.rgba(0.1, 0.1, 0.1, 1.0)
        }
        
        // 这里将添加从Blender导出的对象
        // 示例立方体
        Model {
            id: cube
            source: "#Cube"
            position: Qt.vector3d(0, 0, 0)
            eulerRotation: Qt.vector3d(0, 0, 0)
            
            DefaultMaterial {
                id: material
                baseColor: Qt.rgba(0.8, 0.8, 0.8, 1.0)
                Texture {
                        id: baseColorMap
                        source: "qt_logo_rect.png"
                    }
                    cullMode: DefaultMaterial.NoCulling
                    diffuseMap: cbTexture.checked ? baseColorMap : null
                    specularAmount: 0.5
            }
        }
    }
}
'''
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(qml_content)
        
        print(f"✓ 场景导出到QML成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ 场景导出失败: {e}")
        return False

def get_qt_version():
    """获取Qt版本信息"""
    if not QT_AVAILABLE:
        return "不可用"
    
    try:
        if 'PySide6' in sys.modules:
            return f"PySide6 {PySide6.__version__}"
        else:
            return "未知"
    except:
        return "未知"

def get_quick3d_status():
    """获取Quick3D状态"""
    if not QT_AVAILABLE:
        return "Qt库不可用"
    
    if not QUICK3D_AVAILABLE:
        return "Quick3D不可用"
    
    return "可用"

def get_pyside6_info():
    """获取PySide6目录信息"""
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        pyside6_dir = os.path.join(plugin_dir, "lib", "PySide6")
        
        if not os.path.exists(pyside6_dir):
            return "PySide6目录不存在"
        
        # 统计文件数量
        total_files = 0
        qt6_files = 0
        
        # 统计PySide6目录
        for root, dirs, files in os.walk(pyside6_dir):
            total_files += len(files)
            if "Qt6" in root:
                qt6_files += len(files)
        
        return f"PySide6目录: {total_files} 个文件 (Qt6: {qt6_files})"
        
    except Exception as e:
        return f"获取PySide6信息失败: {e}"

def test_qml_processor_integration():
    """测试QML处理器集成"""
    print("=" * 50)
    print("QML处理器集成测试")
    print("=" * 50)
    
    if not QML_HANDLER_AVAILABLE:
        print("❌ QML处理器不可用")
        return False
    
    try:
        print("🧪 测试QML处理器集成...")
        
        # 测试获取QML内容
        qml_content = qml_handler.get_qml_content_for_integration()
        if qml_content:
            print("✅ QML处理器集成测试成功")
            print(f"📊 获取到的QML内容长度: {len(qml_content)} 字符")
            print(f"📄 QML内容预览:")
            print(qml_content[:500] + "..." if len(qml_content) > 500 else qml_content)
            return True
        else:
            print("❌ QML处理器集成测试失败")
            return False
            
    except Exception as e:
        print(f"❌ QML处理器集成测试异常: {e}")
        return False

# 测试函数
def test_pyside6_integration():
    """测试PySide6集成"""
    print("=" * 50)
    print("PySide6集成测试")
    print("=" * 50)
    
    print(f"PySide6环境: {'✓ 可用' if QT_AVAILABLE else '✗ 不可用'}")
    print(f"Qt库: {'✓ 可用' if QT_AVAILABLE else '✗ 不可用'}")
    print(f"Quick3D: {'✓ 可用' if QUICK3D_AVAILABLE else '✗ 不可用'}")
    print(f"QML处理器: {'✓ 可用' if QML_HANDLER_AVAILABLE else '✗ 不可用'}")
    
    if QT_AVAILABLE:
        print(f"Qt版本: {get_qt_version()}")
    
    print(f"PySide6信息: {get_pyside6_info()}")
    
    if QUICK3D_AVAILABLE:
        print("Quick3D状态: 可用")
        # 尝试创建简单场景
        scene = create_quick3d_scene()
        if scene:
            print("✓ Quick3D场景创建测试通过")
        else:
            print("✗ Quick3D场景创建测试失败")
    
    # 测试QML处理器集成
    if QML_HANDLER_AVAILABLE:
        print("\n🧪 测试QML处理器集成...")
        test_qml_processor_integration()
    
    print("=" * 50)

if __name__ == "__main__":
    test_pyside6_integration()
