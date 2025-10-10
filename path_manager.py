#!/usr/bin/env python3
"""
路径管理模块 - 统一管理所有路径相关功能
负责管理输出目录、工作空间、QML路径等
"""

import os
import bpy
from typing import Optional, Dict, Any


class PathManager:
    """路径管理器 - 统一管理所有路径"""
    
    def __init__(self):
        self._output_base_dir = None
        self._qml_output_dir = None
        self._work_space_path = None
        self._addon_dir = None
        self._qmlproject_path = None
        self._qmlproject_assets_path = None
        self._qmlproject_assets=[]

    
    @property
    def addon_dir(self) -> str:
        """获取插件目录"""
        if self._addon_dir is None:
            self._addon_dir = os.path.dirname(os.path.abspath(__file__))
        return self._addon_dir
    
    @property
    def work_space_path(self) -> Optional[str]:
        """获取工作空间路径"""
        if self._work_space_path is None:
            try:
                scene = bpy.context.scene
                self._work_space_path = getattr(scene, 'work_space_path', None)
            except Exception:
                pass
        return self._work_space_path
    
    @work_space_path.setter
    def work_space_path(self, value: str):
        """设置工作空间路径"""
        self._work_space_path = value
        # 同时更新场景属性
        try:
            scene = bpy.context.scene
            scene.work_space_path = value
        except Exception:
            pass
    
    @property
    def output_base_dir(self) -> str:
        """获取输出基础目录"""
        if self._output_base_dir is None:
            # 优先使用工作空间路径
            if self.work_space_path:
                self._output_base_dir = self.work_space_path
            else:
                # 使用默认输出目录
                self._output_base_dir = os.path.join(self.addon_dir, "output")
        
        # 确保目录存在
        os.makedirs(self._output_base_dir, exist_ok=True)
        return self._output_base_dir
    
    @output_base_dir.setter
    def output_base_dir(self, value: str):
        """设置输出基础目录"""
        self._output_base_dir = value
        os.makedirs(self._output_base_dir, exist_ok=True)
    
    @property
    def qml_output_dir(self) -> str:
        """获取QML输出目录"""
        if self._qml_output_dir is None:
            # QML输出目录与基础输出目录相同
            self._qml_output_dir = self.output_base_dir
        return self._qml_output_dir
    
    @qml_output_dir.setter
    def qml_output_dir(self, value: str):
        """设置QML输出目录"""
        self._qml_output_dir = value
        os.makedirs(self._qml_output_dir, exist_ok=True)
    
    def set_work_space(self, work_space_path: str) -> bool:
        """设置工作空间路径"""
        try:
            if os.path.exists(work_space_path) or os.path.exists(os.path.dirname(work_space_path)):
                self.work_space_path = work_space_path
                # 更新相关路径
                self._output_base_dir = work_space_path
                self._qml_output_dir = work_space_path
                print(f" 工作空间设置成功: {work_space_path}")
                return True
            else:
                print(f" 工作空间路径无效: {work_space_path}")
                return False
        except Exception as e:
            print(f" 设置工作空间失败: {e}")
            return False

    @property
    def qmlproject_path(self) -> str:
        """获取QML项目路径"""
        return self._qmlproject_path
    
    @qmlproject_path.setter
    def qmlproject_path(self, value: str):
        """设置QML项目路径"""
        self._qmlproject_path = value

    
    def get_gltf_path(self, filename: str = None) -> str:
        """获取GLTF文件路径"""
        if filename is None:
            # 根据Blender文件名生成
            blend_filepath = bpy.data.filepath
            if blend_filepath:
                blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
                # 检查是否包含中文字符
                if any('\u4e00' <= char <= '\u9fff' for char in blend_filename):
                    filename = "scene.gltf"
                else:
                    import re
                    safe_name = re.sub(r'[^\w\-\.]', '_', blend_filename)
                    filename = f"{safe_name}.gltf"
            else:
                filename = "scene.gltf"
        
        return os.path.join(self.output_base_dir, filename)
    
    def get_output_paths(self) -> Dict[str, str]:
        """获取所有输出路径信息"""
        return {
            'addon_dir': self.addon_dir,
            'work_space': self.work_space_path,
            'output_base_dir': self.output_base_dir,
            'qml_output_dir': self.qml_output_dir,
            'gltf_path': self.get_gltf_path(),
            'gltf_dir': self.output_base_dir
        }
    
    def open_output_folder(self) -> bool:
        """打开输出文件夹"""
        try:
            if os.path.exists(self.output_base_dir):
                os.startfile(self.output_base_dir)
                print(f"📁 已打开输出文件夹: {self.output_base_dir}")
                return True
            else:
                print("❌ 输出目录不存在")
                return False
        except Exception as e:
            print(f"❌ 打开文件夹失败: {e}")
            return False
    
    def open_qml_folder(self) -> bool:
        """打开QML输出文件夹"""
        try:
            if os.path.exists(self.qml_output_dir):
                os.startfile(self.qml_output_dir)
                print(f"📁 已打开QML输出文件夹: {self.qml_output_dir}")
                return True
            else:
                print("❌ QML输出目录不存在")
                return False
        except Exception as e:
            print(f"❌ 打开文件夹失败: {e}")
            return False
    
    def cleanup_output(self) -> bool:
        """清理输出目录"""
        try:
            if os.path.exists(self.output_base_dir):
                import shutil
                for item in os.listdir(self.output_base_dir):
                    item_path = os.path.join(self.output_base_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        print(f"🧹 清理文件: {item}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"🧹 清理目录: {item}")
                print(f"🧹 清理完成: {self.output_base_dir}")
                return True
            return False
        except Exception as e:
            print(f"⚠️ 清理文件失败: {e}")
            return False
    
    def setup_qml_engine_paths(self, qml_engine) -> bool:
        """为QML引擎设置导入路径"""
        try:
            if qml_engine and hasattr(qml_engine, 'addImportPath'):
                if os.path.exists(self.qml_output_dir):
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


# 全局路径管理器实例
_path_manager = None


def get_path_manager() -> PathManager:
    """获取全局路径管理器实例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager


def get_output_paths() -> Dict[str, str]:
    """获取输出路径信息（兼容性函数）"""
    return get_path_manager().get_output_paths()


def get_qml_output_dir() -> str:
    """获取QML输出目录（兼容性函数）"""
    return get_path_manager().qml_output_dir


def get_output_base_dir() -> str:
    """获取输出基础目录（兼容性函数）"""
    return get_path_manager().output_base_dir


def get_qml_output_base_dir() -> str:
    """获取QML输出基础目录（兼容性函数）"""
    return get_path_manager().qml_output_dir


def get_qmlproject_path() -> str:
    """获取QML项目路径"""
    return get_path_manager().qmlproject_path

def get_qmlproject_assets_path() -> str:
    """获取QML项目资产路径"""
    return get_path_manager().qmlproject_assets_path

def print_path_status():
    """打印路径状态"""
    pm = get_path_manager()
    paths = pm.get_output_paths()
    
    print(" 路径管理器状态 Path Manager Status:")
    print(f"  插件目录 Addon Directory: {paths['addon_dir']}")
    print(f"  工作空间 Work Space: {paths['work_space'] or '(未设置)'}")
    print(f"  输出基础目录 Output Base Directory: {paths['output_base_dir']}")
    print(f"  QML输出目录 QML Output Directory: {paths['qml_output_dir']}")
    print(f"  GLTF路径 GLTF Path: {paths['gltf_path']}")
    print(f"  基础目录存在 Base Directory Exists: {'True' if os.path.exists(paths['output_base_dir']) else 'False'}")
    print(f"  QML目录存在 QML Directory Exists: {'True' if os.path.exists(paths['qml_output_dir']) else 'False'}")


# 全局变量 - balsam缓存管理
BALSAM_PATH_MAP = {}
BALSAM_CACHE_LOADED = False
BALSAM_CACHE_FILE = os.path.join(os.path.dirname(__file__), "balsam_version.txt")

def load_balsam_cache():
    """从缓存文件加载balsam路径映射"""
    global BALSAM_PATH_MAP, BALSAM_CACHE_LOADED
    
    # 如果已经加载过，直接返回
    if BALSAM_CACHE_LOADED:
        return len(BALSAM_PATH_MAP) > 0
    
    BALSAM_PATH_MAP = {}
    
    if not os.path.exists(BALSAM_CACHE_FILE):
        print(f"❌ 缓存文件不存在: {BALSAM_CACHE_FILE}")
        BALSAM_CACHE_LOADED = True
        return False
        
    try:
        with open(BALSAM_CACHE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if '=' in line:
                key, path = line.split('=', 1)
                if os.path.exists(path):
                    BALSAM_PATH_MAP[key] = path
                    
        print(f"✅ 从缓存加载了 {len(BALSAM_PATH_MAP)} 个balsam路径")
        BALSAM_CACHE_LOADED = True
        return len(BALSAM_PATH_MAP) > 0
    except Exception as e:
        print(f"❌ 加载balsam缓存失败: {e}")
        BALSAM_CACHE_LOADED = True
        return False

def save_balsam_cache():
    """保存balsam路径映射到缓存文件"""
    try:
        with open(BALSAM_CACHE_FILE, 'w', encoding='utf-8') as f:
            for key, path in BALSAM_PATH_MAP.items():
                f.write(f"{key}={path}\n")
        print(f"✅ 保存了 {len(BALSAM_PATH_MAP)} 个balsam路径到缓存")
        return True
    except Exception as e:
        print(f"❌ 保存balsam缓存失败: {e}")
        return False

def scan_qt_balsam_paths():
    """扫描C:/Qt目录下的balsam.exe文件"""
    candidates = []
    qt_base = "C:/Qt"
    
    if not os.path.exists(qt_base):
        print(f"❌ Qt目录不存在: {qt_base}")
        return candidates
    
    try:
        for item in os.listdir(qt_base):
            item_path = os.path.join(qt_base, item)
            if os.path.isdir(item_path):
                # 检查两种格式：
                # 1. 旧格式: Qt-6.9.0/bin/balsam.exe
                # 2. 新格式: 6.9.2/compiler/bin/balsam.exe
                
                # 格式1: 直接在版本目录下查找bin
                bin_path = os.path.join(item_path, "bin")
                if os.path.exists(bin_path):
                    balsam_path = os.path.join(bin_path, "balsam.exe")
                    if os.path.exists(balsam_path):
                        candidates.append(balsam_path)
                        print(f"✅ 找到balsam (格式1): {balsam_path}")
                
                # 格式2: 在版本目录下的编译器子目录中查找
                else:
                    for compiler in os.listdir(item_path):
                        compiler_path = os.path.join(item_path, compiler)
                        if os.path.isdir(compiler_path):
                            compiler_bin_path = os.path.join(compiler_path, "bin")
                            if os.path.exists(compiler_bin_path):
                                balsam_path = os.path.join(compiler_bin_path, "balsam.exe")
                                if os.path.exists(balsam_path):
                                    candidates.append(balsam_path)
                                    print(f"✅ 找到balsam (格式2): {balsam_path}")
        
        print(f"✅ 总共找到 {len(candidates)} 个balsam版本")
        return candidates
    except Exception as e:
        print(f"❌ 扫描Qt目录失败: {e}")
        return candidates

def find_balsam_executable():
    """查找可用的balsam可执行文件"""
    # 首先尝试从缓存加载
    load_balsam_cache()
    
    # 如果缓存为空，扫描Qt目录
    if not BALSAM_PATH_MAP:
        candidates = scan_qt_balsam_paths()
        if candidates:
            # 选择最新的版本（按路径排序）
            latest_balsam = sorted(candidates)[-1]
            BALSAM_PATH_MAP["QT_AUTO"] = latest_balsam
            save_balsam_cache()
            return latest_balsam
    
    # 从缓存中选择 - 优先选择与PySide6匹配的版本
    if BALSAM_PATH_MAP:
        # 尝试找到与PySide6版本匹配的balsam
        pyside6_matched = find_balsam_matching_pyside6()
        if pyside6_matched:
            return pyside6_matched
        
        # 如果没有匹配的，优先选择QT_AUTO，如果没有则选择第一个
        if "QT_AUTO" in BALSAM_PATH_MAP:
            return BALSAM_PATH_MAP["QT_AUTO"]
        else:
            return list(BALSAM_PATH_MAP.values())[0]
    
    return None

def find_balsam_matching_pyside6():
    """查找与当前PySide6版本匹配的balsam"""
    try:
        import PySide6
        pyside6_version = getattr(PySide6, '__version__', 'Unknown')
        print(f"🔍 当前PySide6版本: {pyside6_version}")
        
        if pyside6_version == 'Unknown':
            return None
        
        # 首先检查PySide6目录下是否有balsam
        pyside6_path = os.path.dirname(PySide6.__file__)
        pyside6_balsam = os.path.join(pyside6_path, "balsam.exe")
        
        if os.path.exists(pyside6_balsam):
            print(f"✅ 找到PySide6目录下的balsam: {pyside6_balsam}")
            return pyside6_balsam
        
        print(f"⚠️ PySide6目录下未找到balsam: {pyside6_balsam}")
        
        # 如果PySide6目录下没有，则查找匹配的Qt版本
        version_parts = pyside6_version.split('.')
        if len(version_parts) >= 2:
            major_minor = f"{version_parts[0]}.{version_parts[1]}"
        else:
            major_minor = version_parts[0]
        
        print(f"🔍 查找匹配的Qt版本: {major_minor}")
        
        # 查找匹配的balsam版本
        matching_balsam = None
        for key, path in BALSAM_PATH_MAP.items():
            if key == "QT_AUTO":
                continue
                
            qt_version, compiler = _parse_balsam_path_info(path)
            if qt_version.startswith(major_minor):
                print(f"✅ 找到匹配的balsam: Qt {qt_version} - {compiler}")
                print(f"   路径: {path}")
                matching_balsam = path
                break
        
        if matching_balsam:
            print(f"🎯 选择与PySide6匹配的balsam: {matching_balsam}")
        else:
            print(f"⚠️ 未找到与PySide6 {major_minor}匹配的balsam版本")
            
        return matching_balsam
        
    except ImportError:
        print("❌ PySide6不可用，无法匹配版本")
        return None
    except Exception as e:
        print(f"❌ 匹配PySide6版本失败: {e}")
        return None

def _parse_balsam_path_info(path):
    """解析balsam路径，提取Qt版本和编译器信息"""
    path_parts = path.replace('\\', '/').split('/')
    
    # 查找Qt版本和编译器
    qt_version = "Unknown"
    compiler = "Unknown"
    
    # 处理两种路径格式：
    # 1. C:/Qt/Qt-6.9.0/bin/balsam.exe
    # 2. C:/Qt/6.9.2/msvc2022_64/bin/balsam.exe
    
    if 'Qt' in path_parts:
        qt_index = path_parts.index('Qt')
        if qt_index + 1 < len(path_parts):
            qt_version = path_parts[qt_index + 1]
            if qt_version.startswith('Qt-'):
                qt_version = qt_version[3:]  # 移除"Qt-"前缀
    else:
        # 查找版本号模式 (如 6.9.2)
        for part in path_parts:
            if '.' in part and part.replace('.', '').isdigit():
                qt_version = part
                break
    
    # 查找编译器
    for part in path_parts:
        if any(compiler_name in part.lower() for compiler_name in ['mingw', 'msvc', 'llvm']):
            compiler = part
            break
    
    # 如果没有找到编译器，尝试从bin目录的父目录推断
    if compiler == "Unknown":
        try:
            bin_index = path_parts.index('bin')
            if bin_index > 0:
                parent_dir = path_parts[bin_index - 1]
                if any(compiler_name in parent_dir.lower() for compiler_name in ['mingw', 'msvc', 'llvm']):
                    compiler = parent_dir
                elif parent_dir == qt_version:
                    # 对于Qt-6.9.0格式，编译器可能是默认的
                    compiler = "Default"
        except ValueError:
            pass
    
    return qt_version, compiler

def build_balsam_enum_items(self, context):
    """构建balsam版本枚举项"""
    # 获取当前PySide6版本信息
    pyside6_info = ""
    try:
        import PySide6
        pyside6_version = getattr(PySide6, '__version__', 'Unknown')
        if pyside6_version != 'Unknown':
            pyside6_info = f" (PySide6 {pyside6_version})"
    except ImportError:
        pass
    
    items = [("AUTO", f"Auto{pyside6_info}", "Auto-select balsam matching PySide6 version")]
    
    # 从缓存加载路径（如果还没有加载）
    if not BALSAM_CACHE_LOADED:
        load_balsam_cache()
    
    # 按Qt版本和编译器排序
    sorted_items = []
    for key, path in BALSAM_PATH_MAP.items():
        if key != "QT_AUTO":  # 跳过自动选择项
            qt_version, compiler = _parse_balsam_path_info(path)
            description = f"Qt {qt_version} - {compiler}"
            sorted_items.append((qt_version, compiler, key, description, path))
    
    # 按Qt版本号排序（降序，最新版本在前）
    def version_sort_key(item):
        version_str = item[0]
        try:
            # 将版本号转换为可比较的元组
            version_parts = [int(x) for x in version_str.split('.')]
            return tuple(version_parts)
        except:
            return (0, 0, 0)
    
    sorted_items.sort(key=version_sort_key, reverse=True)
    
    # 添加到items列表
    for _, _, key, description, path in sorted_items:
        items.append((key, description, path))
    
    return items

def update_balsam_selection(self, context):
    """更新balsam选择"""
    scene = context.scene
    selected_version = scene.balsam_version
    
    print(f"🔧 update_balsam_selection被调用，选择版本: {selected_version}")
    
    if selected_version == "AUTO":
        # 自动选择最新的版本
        print("🔍 开始AUTO选择...")
        latest = find_balsam_executable()
        print(f"🔍 AUTO选择结果: {latest}")
        if latest:
            print(f"✅ 自动选择balsam: {latest}")
            # 更新全局选择的balsam路径
            set_selected_balsam_path(latest)
        else:
            print("❌ AUTO选择失败，未找到balsam")
    else:
        # 选择指定的版本
        print(f"🔍 选择指定版本: {selected_version}")
        if selected_version in BALSAM_PATH_MAP:
            selected_path = BALSAM_PATH_MAP[selected_version]
            print(f"✅ 选择balsam版本: {selected_path}")
            # 更新全局选择的balsam路径
            set_selected_balsam_path(selected_path)
        else:
            print(f"❌ 未找到balsam版本: {selected_version}")

# 全局选择的balsam路径
_SELECTED_BALSAM_PATH = None

def set_selected_balsam_path(path):
    """设置选择的balsam路径"""
    global _SELECTED_BALSAM_PATH
    _SELECTED_BALSAM_PATH = path
    print(f"🔧 全局balsam路径已更新: {path}")

def get_selected_balsam_path():
    """获取选择的balsam路径"""
    global _SELECTED_BALSAM_PATH
    if _SELECTED_BALSAM_PATH is None:
        # 如果没有选择，使用默认的
        _SELECTED_BALSAM_PATH = find_balsam_executable()
    return _SELECTED_BALSAM_PATH

def get_pyside6_installation_info():
    """获取PySide6安装信息"""
    try:
        import PySide6
        current_path = os.path.dirname(PySide6.__file__)
        current_version = getattr(PySide6, '__version__', 'Unknown')
        
        # 查找所有可用的安装
        all_installations = find_all_pyside6_installations()
        
        # 确定当前使用的安装
        current_install = None
        for install in all_installations:
            try:
                if install['path'] == current_path:
                    current_install = install
                    break
            except Exception:
                continue
        
        if not current_install:
            # 如果找不到匹配的安装，创建一个
            current_install = {
                'version': current_version,
                'path': current_path,
                'description': f'Current installation: {current_path}',
                'type': 'unknown',
                'priority': 999,
                'valid': True
            }
        
        return {
            'available': True,
            'current': current_install,
            'all_installations': all_installations
        }
    except ImportError:
        return {
            'available': False,
            'current': None,
            'all_installations': []
        }

def get_python_executable_info():
    """获取Python可执行文件信息"""
    import sys
    return {
        'executable': sys.executable,
        'version': sys.version,
        'platform': sys.platform
    }

def find_all_pyside6_installations():
    """查找所有可用的PySide6安装位置，按优先级排序"""
    import site
    import sys
    
    installations = []
    
    # 获取所有可能的site-packages路径
    site_packages_paths = site.getsitepackages()
    user_site = site.getusersitepackages()
    
    # 添加Blender特定的site-packages路径
    blender_site_packages = []
    if hasattr(sys, 'executable') and 'blender' in sys.executable.lower():
        # Blender的site-packages通常在scripts/modules/下
        blender_base = os.path.dirname(os.path.dirname(sys.executable))
        blender_modules = os.path.join(blender_base, 'scripts', 'modules')
        if os.path.exists(blender_modules):
            blender_site_packages.append(blender_modules)
    
    # 搜索所有路径
    search_paths = site_packages_paths + [user_site] + blender_site_packages
    
    for path in search_paths:
        if os.path.exists(path):
            pyside6_path = os.path.join(path, 'PySide6')
            if os.path.exists(pyside6_path):
                try:
                    # 尝试获取版本信息
                    version_file = os.path.join(pyside6_path, '__init__.py')
                    version = 'Unknown'
                    if os.path.exists(version_file):
                        with open(version_file, 'r') as f:
                            for line in f:
                                if line.startswith('__version__'):
                                    version = line.split('=')[1].strip().strip("'\"")
                                    break
                    
                    install_type = 'system' if path in site_packages_paths else 'user'
                    priority = 1 if install_type == 'system' else 2
                    
                    installations.append({
                        'version': version,
                        'path': pyside6_path,
                        'description': f'{install_type.title()} site-packages: {path}',
                        'type': install_type,
                        'priority': priority,
                        'valid': True
                    })
                except Exception as e:
                    print(f"❌ 处理PySide6安装失败 {path}: {e}")
    
    # 按优先级排序
    installations.sort(key=lambda x: x['priority'])
    return installations

def get_qt_environment_for_path(balsam_path):
    """为指定的balsam路径获取Qt环境变量"""
    env = os.environ.copy()
    
    if balsam_path and os.path.exists(balsam_path):
        # 获取Qt安装目录
        qt_dir = os.path.dirname(os.path.dirname(balsam_path))
        qt_bin = os.path.dirname(balsam_path)
        
        # 设置Qt环境变量
        env['QT_DIR'] = qt_dir
        env['QT_BIN'] = qt_bin
        env['PATH'] = qt_bin + os.pathsep + env.get('PATH', '')
        
        # 设置Qt插件路径
        plugins_path = os.path.join(qt_bin, 'plugins')
        if os.path.exists(plugins_path):
            env['QT_PLUGIN_PATH'] = plugins_path
    
    return env

if __name__ == "__main__":
    # 测试路径管理器
    pm = get_path_manager()
    print_path_status()
