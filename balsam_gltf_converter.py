#!/usr/bin/env python3
"""
Balsam GLTF to QML Converter for Blender2Quick3D
This script exports the current Blender scene to GLTF format and then calls balsam.exe
"""

import bpy
import os
import subprocess
import shutil
from pathlib import Path
from . import path_manager

# 全局变量定义 - 确保所有模块使用相同的路径
QML_OUTPUT_DIR = None
OUTPUT_BASE_DIR = None
BASE_DIR = None

def get_qml_output_dir():
    """获取QML输出目录的全局路径"""
    global QML_OUTPUT_DIR
    # 如果Blender场景中定义了工作空间路径，则优先使用
    try:
        scene = bpy.context.scene
        work_space = getattr(scene, 'work_space_path', None)
        if work_space:
            QML_OUTPUT_DIR = work_space
            return QML_OUTPUT_DIR
    except Exception:
        pass
    if QML_OUTPUT_DIR is None:
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        QML_OUTPUT_DIR = os.path.join(addon_dir, "output")  # 直接使用output目录
    return QML_OUTPUT_DIR

def get_output_base_dir():
    """获取输出基础目录的全局路径"""
    global OUTPUT_BASE_DIR
    # 如果Blender场景中定义了工作空间路径，则优先使用
    try:
        scene = bpy.context.scene
        work_space = getattr(scene, 'work_space_path', None)
        if work_space:
            OUTPUT_BASE_DIR = work_space
            return OUTPUT_BASE_DIR
    except Exception:
        pass
    if OUTPUT_BASE_DIR is None:
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        OUTPUT_BASE_DIR = os.path.join(addon_dir, "output")
    return OUTPUT_BASE_DIR

class BalsamGLTFToQMLConverter:
    """使用Balsam的GLTF到QML转换器"""
    
    def __init__(self):
        self.output_base_dir = None
        self.gltf_path = None
        self.qml_output_dir = None
        self.balsam_path = None
        
    def setup_environment(self):
        """设置环境"""
        # 使用全局变量确保路径一致
        self.output_base_dir = get_output_base_dir()
        self.qml_output_dir = path_manager.get_qml_output_base_dir()

        # 设置当前Qt可读的资源目录
        # 这里可以设置Qt相关的环境变量，确保QML引擎能找到输出目录
        
        # 确保输出目录存在
        os.makedirs(self.output_base_dir, exist_ok=True)
        # 不再创建额外的qml目录，直接在output目录中生成文件
        
        # 查找balsam可执行文件
        print("🔍 开始查找balsam可执行文件...")
        old_path = self.balsam_path
        # 优先使用用户选择的balsam路径
        self.balsam_path = path_manager.get_selected_balsam_path()
        print(f"🔍 最终选择的balsam路径: {self.balsam_path}")
        if old_path != self.balsam_path:
            print(f"🔍 路径已更改: {old_path} -> {self.balsam_path}")
        else:
            print(f"🔍 路径未更改: {self.balsam_path}")
        
        # 可选：简单检查balsam可执行文件是否可用
        self._check_dependencies()
        
        print(f"📁 输出基础目录: {self.output_base_dir}")
        print(f"📁 QML输出目录: {self.qml_output_dir}")
        print(f"🔧 Balsam路径: {self.balsam_path}")
        
        # 更新全局变量
        global QML_OUTPUT_DIR, OUTPUT_BASE_DIR
        QML_OUTPUT_DIR = self.qml_output_dir
        OUTPUT_BASE_DIR = self.output_base_dir
    
    def get_output_paths(self):
        """获取输出路径信息，用于UI按钮"""
        return {
            'base_dir': self.output_base_dir,
            'qml_dir': self.qml_output_dir,
            'gltf_file': self.gltf_path,
            'gltf_dir': os.path.dirname(self.gltf_path) if self.gltf_path else None
        }
    
    def setup_qml_engine_import_path(self, qml_engine):
        """为QML引擎设置导入路径  指向qmloutput目录"""
        try:
            if qml_engine and hasattr(qml_engine, 'addImportPath'):
                if self.qml_output_dir and os.path.exists(self.qml_output_dir):
                    qml_engine.addImportPath(self.qml_output_dir)
                    print(f"✅ 已为QML引擎添加导入路径: {self.qml_output_dir}")
                    return True
                else:
                    print(f"⚠️ QML输出目录不存在: {self.qml_output_dir}")
                    return False
            else:
                print("❌ QML引擎无效或没有addImportPath方法")
                return False
        except Exception as e:
            print(f"❌ 设置QML引擎导入路径失败: {e}")
            return False
    
    def open_output_folder(self):
        """打开输出文件夹"""
        try:
            if self.output_base_dir and os.path.exists(self.output_base_dir):
                os.startfile(self.output_base_dir)
                print(f"📁 已打开输出文件夹: {self.output_base_dir}")
                return True
            else:
                print("❌ 输出目录不存在")
                return False
        except Exception as e:
            print(f"❌ 打开文件夹失败: {e}")
            return False
    
    def open_gltf_folder(self):
        """打开GLTF文件所在文件夹"""
        try:
            if self.gltf_path and os.path.exists(os.path.dirname(self.gltf_path)):
                os.startfile(os.path.dirname(self.gltf_path))
                print(f"📁 已打开GLTF文件夹: {os.path.dirname(self.gltf_path)}")
                return True
            else:
                print("❌ GLTF文件目录不存在")
                return False
        except Exception as e:
            print(f"❌ 打开文件夹失败: {e}")
            return False
    
    def open_qml_folder(self):
        """打开QML输出文件夹"""
        try:
            if self.qml_output_dir and os.path.exists(self.qml_output_dir):
                os.startfile(self.qml_output_dir)
                print(f"📁 已打开QML输出文件夹: {self.qml_output_dir}")
                return True
            else:
                print("❌ QML输出目录不存在")
                return False
        except Exception as e:
            print(f"❌ 打开文件夹失败: {e}")
            return False

    def _find_balsam_executable(self):
        """查找balsam可执行文件，优先使用系统已安装的版本"""
        # 1. 优先使用全局选定的balsam路径（用户手动选择的）
        try:
            # 直接导入模块并获取全局变量
            import sys
            addon_name = 'Blender2Quick3D'
            
            if addon_name in sys.modules:
                addon_main = sys.modules[addon_name]
                selected_path = getattr(addon_main, 'SELECTED_BALSAM_PATH', None)
                print(f"🔍 全局选定的balsam路径: {selected_path}")
                
                if selected_path and os.path.exists(selected_path):
                    print(f"✅ 使用全局选定的balsam版本: {selected_path}")
                    # 存储选定的路径，环境变量将在调用时设置
                    return selected_path
                else:
                    print(f"❌ 全局选定的路径无效或为空: {selected_path}")
            else:
                print(f"❌ 无法找到插件模块: {addon_name}")
        except Exception as e:
            print(f"❌ 获取全局选定路径失败: {e}")
            import traceback
            traceback.print_exc()

        # 2. 检查系统PATH中的balsam（系统安装的版本）
        try:
            result = subprocess.run(['where', 'balsam.exe'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                print(f"✅ 在系统PATH中找到balsam: {path}")
                return path
        except:
            pass

        # 3. 扫描 C:/Qt 目录（系统Qt安装）
        try:
            from . import __init__ as addon_main
            if hasattr(addon_main, '_scan_qt_balsam_paths'):
                candidates = addon_main._scan_qt_balsam_paths()
                if candidates:
                    # mingw优先
                    mingw = [p for p in candidates if 'mingw' in p.lower()]
                    if mingw:
                        print(f"✅ 扫描C:/Qt找到mingw balsam: {mingw[0]}")
                        return mingw[0]
                    # 回退msvc
                    print(f"✅ 扫描C:/Qt找到balsam: {candidates[0]}")
                    return candidates[0]
        except Exception as e:
            print(f"扫描C:/Qt失败: {e}")

        # 4. 不再检查插件目录，只使用系统安装的balsam
        
        print("❌ 未找到balsam可执行文件")
        return None
    
    def _get_qt_environment_for_path(self, balsam_path):
        """为选定的balsam路径获取正确的Qt环境变量（不修改系统环境）"""
        try:
            # 创建环境变量字典（不修改系统环境）
            env = os.environ.copy()
            
            # 检查balsam是否在系统PySide6目录中
            if "site-packages" in balsam_path or "dist-packages" in balsam_path:
                # 系统PySide6安装，使用系统环境变量
                print(f"🔧 检测到系统PySide6安装，使用系统环境变量")
                print(f"  Balsam路径: {balsam_path}")
                
                # 对于系统PySide6，通常不需要设置特殊的Qt环境变量
                # 只需要确保PATH中包含PySide6目录
                pyside6_dir = os.path.dirname(balsam_path)
                current_path = env.get('PATH', '')
                if pyside6_dir not in current_path:
                    env['PATH'] = f"{pyside6_dir};{current_path}"
                    print(f"  ✅ 已设置PATH，PySide6目录优先")
                
                print(f"  ✅ 系统PySide6环境变量准备完成")
                return env
            else:
                # C:\Qt安装，使用传统Qt环境变量设置
                qt_install_dir = os.path.dirname(os.path.dirname(balsam_path))
                qt_bin_dir = os.path.dirname(balsam_path)
                
                print(f"🔧 检测到C:/Qt安装，设置Qt环境变量:")
                print(f"  Qt安装目录: {qt_install_dir}")
                print(f"  Qt bin目录: {qt_bin_dir}")
                
                env['QT_DIR'] = qt_install_dir
                env['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_install_dir, "plugins", "platforms")
                env['QT_PLUGIN_PATH'] = os.path.join(qt_install_dir, "plugins")
                env['QT_QML_IMPORT_PATH'] = os.path.join(qt_install_dir, "qml")
                
                # 更新PATH，将Qt bin目录放在最前面
                current_path = env.get('PATH', '')
                if qt_bin_dir not in current_path:
                    env['PATH'] = f"{qt_bin_dir};{current_path}"
                    print(f"  ✅ 已设置临时PATH，Qt bin目录优先")
                
                print(f"  ✅ Qt环境变量准备完成")
                return env
            
        except Exception as e:
            print(f"❌ 准备Qt环境变量失败: {e}")
            return os.environ.copy()
    
    def _check_dependencies(self):
        """检查balsam是否可执行（简化版，不再依赖插件lib目录）"""
        print("🔍 检查balsam可执行文件...")
        if self.balsam_path:
            print(f"  ✅ 路径: {self.balsam_path}")
            
            # 检查文件大小和权限
            try:
                stat = os.stat(self.balsam_path)
                print(f"  📊 文件大小: {stat.st_size:,} 字节")
                print(f"  📊 修改时间: {stat.st_mtime}")
                
                # 测试balsam帮助信息
                print(f"  🔧 测试balsam帮助信息...")
                self._test_balsam_help()
                
            except Exception as e:
                print(f"  ⚠️  无法获取文件信息: {e}")
        else:
            print(f"  ❌ 未找到balsam可执行文件")
    
    def _test_balsam_help(self):
        """测试balsam帮助信息"""
        try:
            # 尝试获取帮助信息
            result = subprocess.run(
                [self.balsam_path, "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"  ✅ 帮助信息获取成功")
                print(f"  📋 帮助内容: {result.stdout[:200]}...")
            else:
                print(f"  ⚠️  帮助信息获取失败，返回码: {result.returncode}")
                
        except Exception as e:
            print(f"  ⚠️  帮助信息测试失败: {e}")
        
    def export_scene_to_gltf(self):
        """导出场景为GLTF格式"""
        try:
            # 按照当前blender文件名称命名 .gltf；如果包含中文字符就保存为scene.gltf
            import re

            def contains_chinese(text):
                return any('\u4e00' <= char <= '\u9fff' for char in text)

            # 获取当前blender文件名（不含扩展名）
            blend_filepath = bpy.data.filepath
            if blend_filepath:
                blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
                if contains_chinese(blend_filename):
                    gltf_filename = "scene.gltf"
                else:
                    # 只允许合法文件名字符
                    safe_name = re.sub(r'[^\w\-\.]', '_', blend_filename)
                    gltf_filename = f"{safe_name}.gltf"
            else:
                gltf_filename = "scene.gltf"

            self.gltf_path = os.path.join(self.output_base_dir, gltf_filename)

            # 导出的.qml路径保存下来作为一个全局变量
            global BASE_DIR, QML_OUTPUT_DIR, OUTPUT_BASE_DIR
            # 直接在GLTF同级目录生成QML文件
            BASE_DIR = self.output_base_dir
            self.qml_output_dir = self.output_base_dir
            QML_OUTPUT_DIR = self.qml_output_dir
            OUTPUT_BASE_DIR = self.output_base_dir
            
            print(f"📁 设置BASE_DIR为GLTF同级目录: {BASE_DIR}")
            print(f"📁 QML输出目录: {self.qml_output_dir}")

            #todo 导出场景到gltf的时候，可以读取blender的设置并应用于当前导出
            #todo 可以手动设置场景名称，亦或者直接调用blender的导出设置
            
            # 默认GLTF导出设置
            bpy.ops.export_scene.gltf(
                filepath=self.gltf_path,
                export_format='GLTF_EMBEDDED',  # 使用embedded模式
                export_copyright='Blender2Quick3DMadeByZhiningJiao',
                export_texcoords=True,
                export_normals=True,
                export_tangents=True,
                export_materials='EXPORT',
                # Blender 4.4: export_colors 参数已移除/更名，删除以避免错误
                export_attributes=True,
                export_animations=True,
                export_skins=True,
                export_all_influences=False,
                export_morph=True,
                export_lights=True,
                export_cameras=True,
                export_extras=True,
                export_yup=True,
                export_apply=True,
                export_import_convert_lighting_mode='COMPAT'
               
            )
            
            print(f"✅ 场景导出成功: {self.gltf_path}")
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def set_custom_gltf_path(self, gltf_path):
        """设置自定义GLTF文件路径"""
        if os.path.exists(gltf_path):
            self.gltf_path = gltf_path
            print(f"✅ 设置自定义GLTF路径: {self.gltf_path}")
            return True
        else:
            print(f"❌ GLTF文件不存在: {gltf_path}")
            return False
    
    def set_custom_output_dir(self, output_dir):
        """设置自定义输出目录"""
        if output_dir:
            # 如果用户指定了输出目录，GLTF与QML均使用该目录
            self.qml_output_dir = output_dir
            self.output_base_dir = output_dir
            os.makedirs(self.qml_output_dir, exist_ok=True)
            # 同步更新全局变量，便于其他模块读取
            global QML_OUTPUT_DIR, OUTPUT_BASE_DIR
            QML_OUTPUT_DIR = self.qml_output_dir
            OUTPUT_BASE_DIR = self.output_base_dir
            print(f"📁 设置自定义输出目录: {self.qml_output_dir}")
            return True
        else:
            # 如果没有指定，使用默认的output目录
            self.output_base_dir = get_output_base_dir()
            self.qml_output_dir = self.output_base_dir
            print(f"📁 使用默认输出目录: {self.qml_output_dir}")
            return True
    
    def convert_existing_gltf(self, gltf_path, output_dir=None):
        """转换已存在的GLTF文件"""
        try:
            print(f"🚀 开始转换已存在的GLTF文件...")
            
            # 设置GLTF路径
            if not self.set_custom_gltf_path(gltf_path):
                return False
            
            # 设置环境（这会设置默认的output_base_dir）
            self.setup_environment()
            
            # 设置输出目录（这会覆盖默认设置或使用默认设置）
            if output_dir:
                self.set_custom_output_dir(output_dir)
            else:
                # 确保使用默认的output目录
                self.qml_output_dir = self.output_base_dir
                print(f"📁 使用默认输出目录: {self.qml_output_dir}")
            
            # 调用balsam转换器
            if not self.call_balsam_converter():
                return False
            
            print(" Converted Successfully! 转换完成!")
            return True
            
        except Exception as e:
            print(f" 转换失败: {e}")
            return False
    
    def call_balsam_converter(self):
        """调用balsam转换器"""
        # 优先使用全局选定的balsam路径
        try:
            selected_path = path_manager.get_selected_balsam_path()
            if selected_path and os.path.exists(selected_path):
                print(f"🎯 使用全局选定的balsam版本: {selected_path}")
                self.balsam_path = selected_path
            else:
                print(f"⚠️ 全局选定路径无效，使用默认: {self.balsam_path}")
        except Exception as e:
            print(f"⚠️ 获取全局选定路径失败，使用默认: {e}")
        
        if not self.balsam_path:
            print("❌ 未找到balsam可执行文件")
            return False
            
        if not os.path.exists(self.gltf_path):
            print("❌ GLTF文件不存在")
            return False
            
        try:
            print(f"🔧 调用balsam转换器: {self.balsam_path}")
            print(f"🎯 最终执行的balsam版本: {os.path.basename(self.balsam_path)}")
            print(f"🎯 完整路径: {self.balsam_path}")
            
            # 使用系统环境变量（不再使用lib目录）
            env = path_manager.get_qt_environment_for_path(self.balsam_path)
            
            print(f"🔧 环境变量设置:")
            if 'PYTHONPATH' in env:
                print(f"  PYTHONPATH: {env['PYTHONPATH']}")
            else:
                print(f"  PYTHONPATH: (未设置)")
            print(f"  PATH: {env['PATH'][:200]}...")
            if 'QT_DIR' in env:
                print(f"  QT_DIR: {env['QT_DIR']}")
            if 'QT_PLUGIN_PATH' in env:
                print(f"  QT_PLUGIN_PATH: {env['QT_PLUGIN_PATH']}")
            
            # 调用balsam转换器 - 使用成功的逻辑
            print(f"开始调用balsam转换器...")
            
            # 尝试多种参数格式，直到成功
            success = False
            
            # 格式1：标准格式 --outputPath
            cmd1 = [
                self.balsam_path,
                "--outputPath", self.qml_output_dir,
                self.gltf_path
            ]
            
            print(f"尝试格式1: {' '.join(cmd1)}")
            result1 = subprocess.run(
                cmd1,
                env=env,
                cwd=self.output_base_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            
            if result1.returncode == 0:
                print("✅ 格式1转换成功！")
                print(f"📋 输出: {result1.stdout}")
                success = True
            else:
                print(f"格式1失败，返回码: {result1.returncode}")
                if result1.stderr:
                    print(f"错误: {result1.stderr}")
                
                # 格式2：简化参数，可能不需要--outputPath
                cmd2 = [self.balsam_path, self.gltf_path]
                print(f"尝试格式2: {' '.join(cmd2)}")
                
                result2 = subprocess.run(
                    cmd2,
                    env=env,
                    cwd=self.qml_output_dir,  # 直接在工作目录执行
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result2.returncode == 0:
                    print("✅ 格式2转换成功！")
                    print(f"📋 输出: {result2.stdout}")
                    success = True
                else:
                    print(f"格式2失败，返回码: {result2.returncode}")
                    if result2.stderr:
                        print(f"错误: {result2.stderr}")
                    
                    # 格式3：使用-o参数
                    cmd3 = [self.balsam_path, "-o", self.qml_output_dir, self.gltf_path]
                    print(f"尝试格式3: {' '.join(cmd3)}")
                    
                    result3 = subprocess.run(
                        cmd3,
                        env=env,
                        cwd=self.output_base_dir,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result3.returncode == 0:
                        print("✅ 格式3转换成功！")
                        print(f"📋 输出: {result3.stdout}")
                        success = True
                    else:
                        print(f"格式3失败，返回码: {result3.returncode}")
                        if result3.stderr:
                            print(f"错误: {result3.stderr}")
            
            if success:
                print("🎉 Balsam转换成功！")
                print(f"✅ 使用的balsam版本: {os.path.basename(self.balsam_path)}")
                print(f"✅ 完整路径: {self.balsam_path}")
                return True
            else:
                print("❌ 所有参数格式都失败了")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Balsam转换超时")
            return False
        except Exception as e:
            print(f"❌ 调用balsam失败: {e}")
            return False
    
    def copy_to_documents(self):
        """复制结果到文档目录（可选）"""
        try:
            # 获取用户文档目录
            docs_dir = os.path.expanduser("~/Documents/Blender2Quick3D_Output")
            os.makedirs(docs_dir, exist_ok=True)
            
            # 复制输出文件
            if os.path.exists(self.output_base_dir):
                for item in os.listdir(self.output_base_dir):
                    src = os.path.join(self.output_base_dir, item)
                    dst = os.path.join(docs_dir, item)
                    
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                        print(f"📁 复制文件: {item}")
                    elif os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                        print(f"📁 复制目录: {item}")
            
            print(f"✅ 文件已保存到: {docs_dir}")
            return True
            
        except Exception as e:
            print(f"❌ 复制到文档目录失败: {e}")
            return False
    
    def cleanup(self):
        """清理输出目录中的旧文件（可选）"""
        try:
            if self.output_base_dir and os.path.exists(self.output_base_dir):
                # 只清理GLTF文件，保留QML输出
                gltf_file = os.path.join(self.output_base_dir, "scene.gltf")
                if os.path.exists(gltf_file):
                    os.remove(gltf_file)
                    print(f"🧹 清理GLTF文件: {gltf_file}")
                
                # 清理QML输出目录中的旧文件
                if os.path.exists(self.qml_output_dir):
                    for item in os.listdir(self.qml_output_dir):
                        item_path = os.path.join(self.qml_output_dir, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            print(f"🧹 清理QML文件: {item}")
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            print(f"🧹 清理QML目录: {item}")
                
                print(f"🧹 清理完成: {self.output_base_dir}")
        except Exception as e:
            print(f"⚠️ 清理文件失败: {e}")
    
    def convert(self, keep_files=True, copy_to_docs=False):
        """执行完整的转换流程"""
        try:
            print("🚀 开始Balsam GLTF到QML转换...")
            
            # 1. 设置环境
            self.setup_environment()
            
            # 2. 导出GLTF
            if not self.export_scene_to_gltf():
                return False
            
            # 3. 调用balsam转换器
            if not self.call_balsam_converter():
                return False
            
            # 4. 可选：复制到文档目录
            if copy_to_docs:
                self.copy_to_documents()
            
            print("🎉 转换完成！")
            print(f"📁 GLTF文件: {self.gltf_path}")
            print(f"📁 QML输出: {self.qml_output_dir}")
            
            # 5. 可选：清理文件
            if not keep_files:
                self.cleanup()
            
            return True
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            return False

def get_current_output_status():
    """获取当前输出路径状态"""
    return {
        'qml_output_dir': path_manager.get_qml_output_base_dir(),
        'output_base_dir': get_output_base_dir(),
        'qml_output_exists': os.path.exists(path_manager.get_qml_output_base_dir()),
        'output_base_exists': os.path.exists(get_output_base_dir())
    }

def print_output_status():
    """打印当前输出路径状态"""
    status = get_current_output_status()
    print("📊 当前输出路径状态:")
    print(f"  QML输出目录: {status['qml_output_dir']}")
    print(f"  输出基础目录: {status['output_base_dir']}")
    print(f"  QML目录存在: {'✅' if status['qml_output_exists'] else '❌'}")
    print(f"  基础目录存在: {'✅' if status['output_base_exists'] else '❌'}")

def main():
    """主函数，用于测试"""
    converter = BalsamGLTFToQMLConverter()
    success = converter.convert(keep_files=True, copy_to_docs=False)  # 保留文件，不复制到文档
    
    if success:
        print("✅ 转换成功！")
        # 显示输出路径
        paths = converter.get_output_paths()
        print(f"📁 输出基础目录: {paths['base_dir']}")
        print(f"📁 QML输出目录: {paths['qml_dir']}")
        print(f"📁 GLTF文件: {paths['gltf_file']}")
    else:
        print("❌ 转换失败！")

if __name__ == "__main__":
    main()
