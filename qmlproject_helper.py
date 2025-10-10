import os
import re
from pathlib import Path
import bpy

class QMLProjectHelper:
    """
    QMLProject管理器 - 统一管理QML项目相关的所有操作
    
    设计原则：
    1. 作为QML项目操作的统一入口点
    2. 通过依赖注入接收path_manager，避免循环依赖
    3. 封装所有QML项目相关的业务逻辑
    """
    
    def __init__(self, path_manager=None):
        """
        初始化QMLProjectHelper
        
        Args:
            path_manager: 路径管理器实例（依赖注入）
        """
        self.path_manager = path_manager
        self.blender_file_name = None
        self.qmlproject_path = None #same as _qmlproject_path in path_manager.py
        self.qtquick3d_assets_dir = None
        self.qmlproject_assets_path = None #same as _qmlproject_assets_path in path_manager.py
        self.assets_folders = [] #same as _qmlproject_assets in path_manager.py
    
    def setup(self, qmlproject_path):
        """
        设置QML项目路径并初始化文件夹结构
        
        Args:
            qmlproject_path: qmlproject文件的完整路径
            
        Returns:
            bool: 设置成功返回True
        """
        self.qmlproject_path = qmlproject_path
        
        # 先设置 Blender 文件名（在生成文件夹结构之前）
        self.blender_file_name = self._set_blender_file_name(bpy.data.filepath)
        
        # 生成文件夹结构
        self.qtquick3d_assets_dir = self._generate_folder_structure(qmlproject_path)
        
        if self.qtquick3d_assets_dir:
            self.assets_folders = self._find_assets_folders()
            
            # 设置工作空间（如果需要的话）
            if self.path_manager and self.qmlproject_assets_path:
                self.path_manager.set_work_space(self.qmlproject_assets_path)
            
            return True
        return False

    def _set_qmlproject_path(self, qmlproject_path):
        """
        设置QML项目路径
        """
        self.qmlproject_path = qmlproject_path
        self.qtquick3d_assets_dir = self._generate_folder_structure(qmlproject_path)
        #todo 生成文件夹，并且设置工作空间到qmlproject_assets_path
        self.blender_file_name = self._set_blender_file_name(bpy.data.filepath)
        self.qmlproject_assets_path =  os.path.join(self.qtquick3d_assets_dir,self.blender_file_name)
        self.path_manager.set_workspace(self.qmlproject_assets_path)
        return self.qtquick3d_assets_dir

    def _set_blender_file_name(self, blender_filepath=None):
        """
        设置Blender文件名
        
        Args:
            blender_filepath: Blender文件路径，如果为None则使用 bpy.data.filepath
            
        Returns:
            str: 处理后的文件名
        """
        try:
            # 按照当前blender文件名称命名 如果包含非法字符就保存为Scene
            import re
            
            if blender_filepath is None:
                blender_filepath = bpy.data.filepath
            
            def only_legal_english_characters(text):
                # 只允许英文字母、数字、连字符和点
                return re.match(r'^[a-zA-Z0-9\-\.]+$', text) is not None
            
            # 获取不带扩展名的文件名
            if blender_filepath:
                filename = os.path.splitext(os.path.basename(blender_filepath))[0]
            else:
                filename = "Scene"
            
            # 检查是否是合法的英文字符
            if filename and only_legal_english_characters(filename):
                result = filename
            else:
                result = "Scene"
            
            # 文件第一个字母大写
            if result:
                result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
            
            return result
            
        except Exception as e:
            print(f"❌ 设置Blender文件名失败: {e}")
            return "Scene"
    
    def _generate_folder_structure(self, qmlproject_path):
        """
        创建Generated/QtQuick3D文件夹结构（私有方法）
        
        Args:
            qmlproject_path: qmlproject文件的完整路径
            
        Returns:
            qtquick3d_path: Generated/QtQuick3D文件夹的路径，失败返回None
        """
        try:
            # 检查qmlproject文件是否存在
            if not os.path.exists(qmlproject_path):
                print(f" QMLProject文件不存在: {qmlproject_path}")
                return None
            
            # 获取qmlproject文件所在的目录
            qmlproject_dir = os.path.dirname(qmlproject_path)
            print(f" QMLProject目录: {qmlproject_dir}")
            
            # 检查/创建Generated文件夹
            generated_dir = os.path.join(qmlproject_dir, "Generated")
            if not os.path.exists(generated_dir):
                os.makedirs(generated_dir, exist_ok=True)
                print(f"创建Generated文件夹: {generated_dir}")
            else:
                print(f" Generated文件夹已存在: {generated_dir}")
            
            # 检查/创建QtQuick3D文件夹
            qtquick3d_dir = os.path.join(generated_dir, "QtQuick3D")
            if not os.path.exists(qtquick3d_dir):
                os.makedirs(qtquick3d_dir, exist_ok=True)
                print(f" 创建QtQuick3D文件夹: {qtquick3d_dir}")
            else:
                print(f" QtQuick3D文件夹已存在: {qtquick3d_dir}")
            
            # 检查/创建基于blender文件名称的文件夹
            qmlproject_assets_path = os.path.join(qtquick3d_dir, self.blender_file_name)
            if not os.path.exists(qmlproject_assets_path):
                os.makedirs(qmlproject_assets_path, exist_ok=True)
                print(f" 创建基于blender文件名称的文件夹: {qmlproject_assets_path}")
            else:
                print(f" 基于blender文件名称的文件夹已存在: {qmlproject_assets_path}")
            self.qmlproject_assets_path = qmlproject_assets_path
            return qtquick3d_dir
            
        except Exception as e:
            print(f" 生成文件夹结构失败: {e}")
            return None
    
    def _find_assets_folders(self):
        """
        查找Generated/QtQuick3D下的所有资源文件夹（私有方法）
        
        Returns:
            list: 资源文件夹名称列表
        """
        if not self.qtquick3d_assets_dir or not os.path.exists(self.qtquick3d_assets_dir):
            print(f"⚠️ QtQuick3D资源路径不存在: {self.qtquick3d_assets_dir}")
            return []
        
        # 只获取文件夹，过滤掉文件
        assets = [
            item for item in os.listdir(self.qtquick3d_assets_dir)
            if os.path.isdir(os.path.join(self.qtquick3d_assets_dir, item))
        ]
        
        print(f"📦 找到 {len(assets)} 个资源文件夹: {assets}")
        return assets

    def set_workspace_to_qmlproject_assets_path(self):
        """
        设置工作空间到qmlproject_assets_path
        """
        self.path_manager.set_workspace(self.qmlproject_assets_path)
        return self.qmlproject_assets_path
    
    def get_asset_full_path(self, asset_name):
        """
        获取指定资源文件夹的完整路径
        
        Args:
            asset_name: 资源文件夹名称
            
        Returns:
            str: 完整路径，不存在返回None
        """
        if not self.qtquick3d_assets_dir:
            return None
        
        full_path = os.path.join(self.qtquick3d_assets_dir, asset_name)
        return full_path if os.path.exists(full_path) else None
    
    def refresh_assets(self):
        """刷新资源列表"""
        self.assets_folders = self._find_assets_folders()
        return self.assets_folders


# =============================================================================
# 兼容性函数 - 保持向后兼容，逐步迁移到类方法
# =============================================================================


def generate_qmlproject_file(qmlproject_path):
    """
    读取qmlproject路径，创建Generated/QtQuick3D文件夹结构
    Args:
        qmlproject_path: qmlproject文件的完整路径
    Returns:
        qtquick3d_path: Generated/QtQuick3D文件夹的路径，如果创建失败返回None
    """
    try:
        # 检查qmlproject文件是否存在 check if qmlproject file exists
        if not os.path.exists(qmlproject_path):
            print(f" QMLProject文件不存在: {qmlproject_path}")
            return None
        
        # 获取qmlproject文件所在的目录 get the directory of qmlproject file
        qmlproject_dir = os.path.dirname(qmlproject_path)
        print(f" QMLProject目录: {qmlproject_dir}")
        
        # 检查/创建Generated文件夹 check if Generated folder exists
        generated_dir = os.path.join(qmlproject_dir, "Generated")
        if not os.path.exists(generated_dir):
            os.makedirs(generated_dir, exist_ok=True)
            print(f" 创建Generated文件夹: {generated_dir}")
        else:
            print(f" Generated文件夹已存在: {generated_dir}")
        
        # 检查/创建QtQuick3D文件夹
        qtquick3d_dir = os.path.join(generated_dir, "QtQuick3D")
        if not os.path.exists(qtquick3d_dir):
            os.makedirs(qtquick3d_dir, exist_ok=True)
            print(f" 创建QtQuick3D文件夹: {qtquick3d_dir}")
        else:
            print(f" QtQuick3D文件夹已存在: {qtquick3d_dir}")
        
        return qtquick3d_dir
        
    except Exception as e:
        print(f" 生成文件夹结构失败: {e}")
        return None
    
def generate_qmlproject_related_assets_path(qmlproject_path):
    """生成qmlproject相关的资源路径"""
    if not qmlproject_path:
        print(" qmlproject_path is not set")
        return None
    
    # 这里可以添加更多逻辑
    return None

def find_assets_path(qmlproject_path, qmlproject_assets):
    """
    定义资源路径，获取Generated/QtQuick3D下的所有文件夹
    
    Args:
        qmlproject_path: qmlproject文件的完整路径
        qmlproject_assets: 用于存储资源文件夹的列表
        
    Returns:
        qmlproject_assets: 包含所有资源文件夹路径的列表
    """
    if not qmlproject_path:
        print(" qmlproject_path is not set")
        return None
    
    # 获取qmlproject目录
    qmlproject_dir = os.path.dirname(qmlproject_path)
    quick3d_assets_path = os.path.join(qmlproject_dir, "Generated", "QtQuick3D")
    
    # 检查路径是否存在
    if not os.path.exists(quick3d_assets_path):
        print(f" QtQuick3D资源路径不存在，尝试生成")
        generate_qmlproject_file(qmlproject_path)
        return []
    
    # 将quick3d_assets_path下所有文件夹加入到列表中（过滤掉文件）
    qmlproject_assets = [
        item for item in os.listdir(quick3d_assets_path)
        if os.path.isdir(os.path.join(quick3d_assets_path, item))
    ]
    
    print(f" find {len(qmlproject_assets)} folders in Generated/QtQuick3D: {qmlproject_assets}")
    
    return qmlproject_assets


# =============================================================================
# 全局实例管理 - 单例模式
# =============================================================================

_qmlproject_helper = None
_last_scanned_path = None  # 缓存上次扫描的路径
_cached_assets = []  # 缓存的资源文件夹列表

def get_qmlproject_helper():
    """
    获取全局QMLProjectHelper实例（单例模式）
    
    Returns:
        QMLProjectHelper: 全局实例
    """
    global _qmlproject_helper
    if _qmlproject_helper is None:
        # 延迟导入避免循环依赖
        from . import path_manager
        pm = path_manager.get_path_manager()
        _qmlproject_helper = QMLProjectHelper(path_manager=pm)
    return _qmlproject_helper

def clear_assets_cache():
    """清除资源文件夹缓存"""
    global _last_scanned_path, _cached_assets
    _last_scanned_path = None
    _cached_assets = []


def build_assets_folder_enum_items(self, context):
    """
    构建资源文件夹枚举项（用于下拉框）- 使用缓存减少扫描
    
    Args:
        self: Blender场景对象
        context: Blender上下文
        
    Returns:
        list: 枚举项列表 [(identifier, name, description), ...]
    """
    global _last_scanned_path, _cached_assets
    
    items = [("NONE", "Select Asset Folder", "No asset folder selected")]
    
    try:
        qmlproject_path = getattr(context.scene, "qmlproject_path", None)
        
        # 如果路径相同且已有缓存，直接使用缓存
        if qmlproject_path == _last_scanned_path and _cached_assets:
            for folder in _cached_assets:
                items.append((folder, folder, f"Asset folder: {folder}"))
            return items
        
        # 路径变化或没有缓存，重新扫描
        helper = get_qmlproject_helper()
        
        if qmlproject_path and os.path.exists(qmlproject_path):
            # 确保已经初始化
            if not helper.qmlproject_path or helper.qmlproject_path != qmlproject_path:
                print(f"🔍 初始化 QMLProject: {qmlproject_path}")
                helper.setup(qmlproject_path)
            else:
                helper.refresh_assets()
            
            # 更新缓存
            _last_scanned_path = qmlproject_path
            _cached_assets = helper.assets_folders.copy()
            
            # 添加找到的资源文件夹
            for folder in helper.assets_folders:
                items.append((folder, folder, f"Asset folder: {folder}"))
        else:
            # 清除缓存
            _last_scanned_path = None
            _cached_assets = []
        
        if len(items) == 1:
            items.append(("EMPTY", "No Assets Found", "No asset folders found in Generated/QtQuick3D"))
    
    except Exception as e:
        print(f"❌ 构建资源文件夹列表失败: {e}")
        items.append(("ERROR", "Error", f"Failed to load assets: {str(e)}"))
    
    return items


# =============================================================================
# 使用示例
# =============================================================================
"""
推荐的使用方式（在__init__.py的Operator中）：

class SomeOperator(bpy.types.Operator):
    def execute(self, context):
        from . import qmlproject_helper
        
        # 获取全局实例
        helper = qmlproject_helper.get_qmlproject_helper()
        
        # 设置QML项目路径
        qmlproject_path = "C:/Projects/MyApp/MyApp.qmlproject"
        if helper.setup(qmlproject_path):
            # 获取资源文件夹列表
            print(f"资源文件夹: {helper.assets_folders}")
            
            # 刷新资源列表
            helper.refresh_assets()
            
            # 获取特定资源的完整路径
            asset_path = helper.get_asset_full_path("my_model")
            
        return {'FINISHED'}
"""
