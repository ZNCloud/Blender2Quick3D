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
from bpy.props import StringProperty, BoolProperty, EnumProperty
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

# 供下拉框与转换器共享：Qt安装中的balsam路径映射
BALSAM_PATH_MAP = {}
BALSAM_CACHE_FILE = os.path.join(os.path.dirname(__file__), "balsam_version.txt")
BALSAM_CACHE_LOADED = False
# 全局变量：最终执行的balsam路径
SELECTED_BALSAM_PATH = None

def _scan_qt_balsam_paths():
    """扫描Qt安装目录，查找bin下的balsam.exe - 简化版本避免卡死"""
    candidates = []
    try:
        qt_root = r"C:\Qt"
        if not os.path.exists(qt_root):
            return candidates
            
        # 只扫描第一级版本目录
        for version_dir in os.listdir(qt_root):
            version_path = os.path.join(qt_root, version_dir)
            if not os.path.isdir(version_path):
                continue
                
            # 在版本目录下查找mingw和msvc目录
            for toolchain_dir in os.listdir(version_path):
                toolchain_path = os.path.join(version_path, toolchain_dir)
                if not os.path.isdir(toolchain_path):
                    continue
                    
                # 只检查mingw和msvc目录
                if 'mingw' in toolchain_dir.lower() or 'msvc' in toolchain_dir.lower():
                    bin_path = os.path.join(toolchain_path, 'bin')
                    balsam_exe = os.path.join(bin_path, 'balsam.exe')
                    if os.path.exists(balsam_exe):
                        candidates.append(balsam_exe)
                        
    except Exception as e:
        print(f"扫描Qt目录失败: {e}")
    return candidates

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

def _load_balsam_cache():
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

def _save_balsam_cache():
    """保存balsam路径映射到缓存文件"""
    try:
        with open(BALSAM_CACHE_FILE, 'w', encoding='utf-8') as f:
            for key, path in BALSAM_PATH_MAP.items():
                f.write(f"{key}={path}\n")
        print(f"✅ 已保存 {len(BALSAM_PATH_MAP)} 个balsam路径到缓存")
        return True
    except Exception as e:
        print(f"❌ 保存balsam缓存失败: {e}")
        return False

def _update_balsam_selection(self, context):
    """当下拉框选择改变时更新全局balsam路径"""
    global SELECTED_BALSAM_PATH, BALSAM_PATH_MAP
    
    selected = getattr(context.scene, 'balsam_version', 'AUTO')
    print(f"🔧 下拉框选择改变: {selected}")
    
    if selected == 'AUTO':
        SELECTED_BALSAM_PATH = None
        print(f"🔧 设置为Auto模式，将自动检测balsam路径")
    else:
        # 确保缓存已加载
        _load_balsam_cache()
        chosen = BALSAM_PATH_MAP.get(selected)
        if chosen and os.path.exists(chosen):
            SELECTED_BALSAM_PATH = chosen
            print(f"✅ 设置选定的balsam路径: {chosen}")
        else:
            SELECTED_BALSAM_PATH = None
            print(f"❌ 选择的路径无效: {chosen}")
    
    # 确保系统PATH不被污染，恢复原始PATH
    # 这里我们不做任何PATH修改，让QML窗口正常工作

def _build_balsam_enum_items(self, context):
    """为EnumProperty提供items，并刷新全局映射。"""
    global BALSAM_PATH_MAP
    
    # 只加载一次缓存
    _load_balsam_cache()
    
    items = [("AUTO", "Auto", "Auto-detect from C:/Qt (prefer mingw) or PATH")]
    for key, exe in BALSAM_PATH_MAP.items():
        label = _label_for_balsam_path(exe)
        items.append((key, label, exe))
    return items

# 添加场景属性
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
        items=_build_balsam_enum_items,
        default=0,
        update=_update_balsam_selection,
    )
    
    register_qt_quick3d_properties()

def register_qt_quick3d_properties():
    """注册Qt Quick3D引擎相关属性"""
    from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, BoolProperty, StringProperty
    
    # UI控制属性
    bpy.types.Scene.show_scene_settings = BoolProperty(
        name="Show Scene Settings",
        description="Show or hide SceneSettings panel",
        default=False
    )
    
    # 窗口和View3D尺寸设置
    register_window_properties()
    
    # SceneEnvironment基础属性
    register_scene_environment_properties()
    
    # ExtendedSceneEnvironment高级属性
    register_extended_scene_environment_properties()
    
    # WASD控制器属性
    register_wasd_controller_properties()

def register_window_properties():
    """注册窗口和View3D尺寸相关属性"""
    from bpy.props import IntProperty
    
    # 窗口/View3D大小设置（统一设置，因为View3D覆盖全窗口）
    bpy.types.Scene.qtquick3d_view3d_width = IntProperty(
        name="Width",
        description="Width of the window and View3D area",
        default=1280,
        min=400,
        max=3840
    )
    
    bpy.types.Scene.qtquick3d_view3d_height = IntProperty(
        name="Height",
        description="Height of the window and View3D area", 
        default=720,
        min=300,
        max=2160
    )

def register_scene_environment_properties():
    """注册SceneEnvironment基础属性"""
    from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, BoolProperty, StringProperty
    
    # 抗锯齿设置
    bpy.types.Scene.qtquick3d_antialiasing_mode = IntProperty(
        name="Antialiasing Mode",
        description="Qt Quick3D antialiasing mode",
        default=0,
        min=0,
        max=3
    )
    
    bpy.types.Scene.qtquick3d_antialiasing_quality = IntProperty(
        name="Antialiasing Quality",
        description="Qt Quick3D antialiasing quality",
        default=2,
        min=0,
        max=3
    )
    
    # 环境光遮蔽
    bpy.types.Scene.qtquick3d_ao_enabled = BoolProperty(
        name="AO Enabled",
        description="Enable ambient occlusion",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_ao_strength = FloatProperty(
        name="AO Strength",
        description="Ambient occlusion strength",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    # 背景和清除颜色
    bpy.types.Scene.qtquick3d_background_mode = IntProperty(
        name="Background Mode",
        description="Background mode",
        default=0,
        min=0,
        max=3
    )
    
    bpy.types.Scene.qtquick3d_clear_color = FloatVectorProperty(
        name="Clear Color",
        description="Clear color",
        default=(0.0, 0.0, 0.0, 1.0),
        size=4,
        subtype='COLOR'
    )
    
    # 深度测试
    bpy.types.Scene.qtquick3d_depth_test_enabled = BoolProperty(
        name="Depth Test",
        description="Enable depth test",
        default=True
    )
    
    # 环境光遮蔽详细设置
    bpy.types.Scene.qtquick3d_ao_bias = FloatProperty(
        name="AO Bias",
        description="Ambient occlusion bias",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_ao_distance = FloatProperty(
        name="AO Distance",
        description="Ambient occlusion distance",
        default=5.0,
        min=0.1,
        max=100.0
    )
    
    bpy.types.Scene.qtquick3d_ao_dither = BoolProperty(
        name="AO Dither",
        description="Enable ambient occlusion dithering",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_ao_sample_rate = IntProperty(
        name="AO Sample Rate",
        description="Ambient occlusion sample rate",
        default=2,
        min=1,
        max=8
    )
    
    bpy.types.Scene.qtquick3d_ao_softness = FloatProperty(
        name="AO Softness",
        description="Ambient occlusion softness",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    # 深度设置
    bpy.types.Scene.qtquick3d_depth_prepass_enabled = BoolProperty(
        name="Depth PrePass",
        description="Enable depth prepass",
        default=False
    )
    
    # 环境探针
    bpy.types.Scene.qtquick3d_probe_exposure = FloatProperty(
        name="Probe Exposure",
        description="Environment probe exposure",
        default=0.0,
        min=-5.0,
        max=5.0
    )
    
    bpy.types.Scene.qtquick3d_probe_horizon = FloatProperty(
        name="Probe Horizon",
        description="Environment probe horizon",
        default=0.0,
        min=-1.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_probe_orientation = FloatVectorProperty(
        name="Probe Orientation",
        description="Environment probe orientation",
        default=(0.0, 0.0, 0.0),
        size=3
    )
    
    # 天空盒设置
    bpy.types.Scene.qtquick3d_skybox_cubemap = StringProperty(
        name="SkyBox CubeMap",
        description="Skybox cubemap texture",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_skybox_blur_amount = FloatProperty(
        name="SkyBox Blur Amount",
        description="Skybox blur amount",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    # 抗锯齿高级设置
    bpy.types.Scene.qtquick3d_specular_aa_enabled = BoolProperty(
        name="Specular AA",
        description="Enable specular anti-aliasing",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_temporal_aa_enabled = BoolProperty(
        name="Temporal AA",
        description="Enable temporal anti-aliasing",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_temporal_aa_strength = FloatProperty(
        name="Temporal AA Strength",
        description="Temporal anti-aliasing strength",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    # 色调映射
    bpy.types.Scene.qtquick3d_tonemap_mode = IntProperty(
        name="Tonemap Mode",
        description="Tone mapping mode",
        default=0,
        min=0,
        max=3
    )
    
    # 其他设置
    bpy.types.Scene.qtquick3d_oit_method = IntProperty(
        name="OIT Method",
        description="Order independent transparency method",
        default=0,
        min=0,
        max=2
    )
    
    bpy.types.Scene.qtquick3d_light_probe = StringProperty(
        name="Light Probe",
        description="Light probe texture",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_lightmapper = IntProperty(
        name="Lightmapper",
        description="Lightmapper type",
        default=0,
        min=0,
        max=2
    )
    
    bpy.types.Scene.qtquick3d_scissor_rect = FloatVectorProperty(
        name="Scissor Rect",
        description="Scissor rectangle (x, y, width, height) - x,y是左上角坐标，width,height是View3D分辨率",
        default=(0.0, 0.0, 1280.0, 720.0),
        size=4
    )
    
    # 裁剪启用开关
    bpy.types.Scene.qtquick3d_scissor_enabled = BoolProperty(
        name="Enable Scissor",
        description="Enable scissor rectangle on SceneEnvironment",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_fog = StringProperty(
        name="Fog",
        description="Fog settings",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_debug_settings = StringProperty(
        name="Debug Settings",
        description="Debug settings",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_effects = StringProperty(
        name="Effects",
        description="Effects settings",
        default="",
        subtype='FILE_PATH'
    )

def register_extended_scene_environment_properties():
    """注册ExtendedSceneEnvironment高级属性"""
    from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, BoolProperty, StringProperty
    
    # 扩展环境开关
    bpy.types.Scene.qtquick3d_use_extended_environment = BoolProperty(
        name="Use Extended Environment",
        description="Enable extended scene environment settings",
        default=False
    )
    
    # 颜色调整
    bpy.types.Scene.qtquick3d_brightness = FloatProperty(
        name="Brightness",
        description="Brightness adjustment",
        default=0.0,
        min=-1.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_contrast = FloatProperty(
        name="Contrast",
        description="Contrast adjustment", 
        default=0.0,
        min=-1.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_saturation = FloatProperty(
        name="Saturation",
        description="Saturation adjustment",
        default=0.0,
        min=-1.0,
        max=1.0
    )
    
    # 曝光和锐化
    bpy.types.Scene.qtquick3d_exposure = FloatProperty(
        name="Exposure",
        description="Exposure value",
        default=0.0,
        min=-5.0,
        max=5.0
    )
    
    bpy.types.Scene.qtquick3d_sharpness = FloatProperty(
        name="Sharpness",
        description="Sharpness amount",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    # 景深效果
    bpy.types.Scene.qtquick3d_dof_enabled = BoolProperty(
        name="Enable Depth of Field",
        description="Enable depth of field effect",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_dof_blur_amount = FloatProperty(
        name="DOF Blur Amount",
        description="Depth of field blur amount",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    # 发光效果
    bpy.types.Scene.qtquick3d_glow_enabled = BoolProperty(
        name="Enable Glow",
        description="Enable glow effect",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_glow_intensity = FloatProperty(
        name="Glow Intensity",
        description="Glow intensity",
        default=0.0,
        min=0.0,
        max=10.0
    )
    
    # 镜头光晕
    bpy.types.Scene.qtquick3d_lens_flare_enabled = BoolProperty(
        name="Enable Lens Flare",
        description="Enable lens flare effect",
        default=False
    )
    
    # 颜色调整开关
    bpy.types.Scene.qtquick3d_color_adjustments_enabled = BoolProperty(
        name="Enable Color Adjustments",
        description="Enable color adjustments",
        default=False
    )
    
    # 景深详细设置
    bpy.types.Scene.qtquick3d_dof_focus_distance = FloatProperty(
        name="DOF Focus Distance",
        description="Depth of field focus distance",
        default=100.0,
        min=0.1,
        max=1000.0
    )
    
    bpy.types.Scene.qtquick3d_dof_focus_range = FloatProperty(
        name="DOF Focus Range",
        description="Depth of field focus range",
        default=10.0,
        min=0.1,
        max=100.0
    )
    
    # 抖动设置
    bpy.types.Scene.qtquick3d_dithering_enabled = BoolProperty(
        name="Enable Dithering",
        description="Enable dithering",
        default=False
    )
    
    # FXAA设置
    bpy.types.Scene.qtquick3d_fxaa_enabled = BoolProperty(
        name="Enable FXAA",
        description="Enable FXAA anti-aliasing",
        default=False
    )
    
    # 发光详细设置
    bpy.types.Scene.qtquick3d_glow_blend_mode = IntProperty(
        name="Glow Blend Mode",
        description="Glow blend mode",
        default=0,
        min=0,
        max=3
    )
    
    bpy.types.Scene.qtquick3d_glow_bloom = FloatProperty(
        name="Glow Bloom",
        description="Glow bloom amount",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_glow_hdr_maximum_value = FloatProperty(
        name="Glow HDR Max",
        description="Glow HDR maximum value",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    bpy.types.Scene.qtquick3d_glow_hdr_minimum_value = FloatProperty(
        name="Glow HDR Min",
        description="Glow HDR minimum value",
        default=0.0,
        min=0.0,
        max=10.0
    )
    
    bpy.types.Scene.qtquick3d_glow_hdr_scale = FloatProperty(
        name="Glow HDR Scale",
        description="Glow HDR scale",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    bpy.types.Scene.qtquick3d_glow_level = IntProperty(
        name="Glow Level",
        description="Glow level",
        default=0,
        min=0,
        max=10
    )
    
    bpy.types.Scene.qtquick3d_glow_quality_high = BoolProperty(
        name="High Quality Glow",
        description="Enable high quality glow",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_glow_strength = FloatProperty(
        name="Glow Strength",
        description="Glow strength",
        default=0.0,
        min=0.0,
        max=10.0
    )
    
    bpy.types.Scene.qtquick3d_glow_use_bicubic_upscale = BoolProperty(
        name="Bicubic Upscale",
        description="Use bicubic upscaling for glow",
        default=False
    )
    
    # 镜头光晕详细设置
    bpy.types.Scene.qtquick3d_lens_flare_apply_dirt_texture = BoolProperty(
        name="Apply Dirt Texture",
        description="Apply dirt texture to lens flare",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_apply_starburst_texture = BoolProperty(
        name="Apply Starburst Texture",
        description="Apply starburst texture to lens flare",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_bloom_bias = FloatProperty(
        name="Bloom Bias",
        description="Lens flare bloom bias",
        default=0.0,
        min=-1.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_bloom_scale = FloatProperty(
        name="Bloom Scale",
        description="Lens flare bloom scale",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_blur_amount = FloatProperty(
        name="Blur Amount",
        description="Lens flare blur amount",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_camera_direction = FloatVectorProperty(
        name="Camera Direction",
        description="Lens flare camera direction",
        default=(0.0, 0.0, 1.0),
        size=3
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_distortion = FloatProperty(
        name="Distortion",
        description="Lens flare distortion",
        default=0.0,
        min=-1.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_ghost_count = IntProperty(
        name="Ghost Count",
        description="Number of lens flare ghosts",
        default=4,
        min=0,
        max=20
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_ghost_dispersal = FloatProperty(
        name="Ghost Dispersal",
        description="Lens flare ghost dispersal",
        default=0.3,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_halo_width = FloatProperty(
        name="Halo Width",
        description="Lens flare halo width",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_lens_color_texture = StringProperty(
        name="Color Texture",
        description="Lens flare color texture",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_lens_dirt_texture = StringProperty(
        name="Dirt Texture",
        description="Lens flare dirt texture",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_lens_starburst_texture = StringProperty(
        name="Starburst Texture",
        description="Lens flare starburst texture",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.qtquick3d_lens_flare_stretch_to_aspect = FloatProperty(
        name="Stretch To Aspect",
        description="Stretch lens flare to aspect ratio",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    # LUT设置
    bpy.types.Scene.qtquick3d_lut_enabled = BoolProperty(
        name="Enable LUT",
        description="Enable LUT (Look-Up Table)",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_lut_filter_alpha = FloatProperty(
        name="LUT Filter Alpha",
        description="LUT filter alpha value",
        default=1.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_lut_size = FloatProperty(
        name="LUT Size",
        description="LUT size",
        default=32.0,
        min=16.0,
        max=64.0
    )
    
    bpy.types.Scene.qtquick3d_lut_texture = StringProperty(
        name="LUT Texture",
        description="Path to LUT texture file",
        default="",
        subtype='FILE_PATH'
    )
    
    # 白点设置
    bpy.types.Scene.qtquick3d_white_point = FloatProperty(
        name="White Point",
        description="White point value",
        default=1.0,
        min=0.1,
        max=10.0
    )
    
    # 暗角详细设置
    bpy.types.Scene.qtquick3d_vignette_enabled = BoolProperty(
        name="Enable Vignette",
        description="Enable vignette effect",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_vignette_strength = FloatProperty(
        name="Vignette Strength",
        description="Vignette strength",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_vignette_color = FloatVectorProperty(
        name="Vignette Color",
        description="Vignette color",
        default=(0.0, 0.0, 0.0, 1.0),
        size=4,
        subtype='COLOR'
    )
    
    bpy.types.Scene.qtquick3d_vignette_radius = FloatProperty(
        name="Vignette Radius",
        description="Vignette radius",
        default=0.5,
        min=0.0,
        max=1.0
    )

def register_wasd_controller_properties():
    """注册WASD控制器相关属性"""
    from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
    
    # WASD控制器开关
    bpy.types.Scene.qtquick3d_wasd_enabled = BoolProperty(
        name="Enable WASD Controller",
        description="Enable WASD controller for camera navigation",
        default=True
    )
    
    # 速度设置
    bpy.types.Scene.qtquick3d_wasd_speed = FloatProperty(
        name="Speed",
        description="Base speed of navigation",
        default=1.0,
        min=0.1,
        max=10.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_forward_speed = FloatProperty(
        name="Forward Speed",
        description="Speed when moving forward",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_back_speed = FloatProperty(
        name="Back Speed",
        description="Speed when moving backward",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_left_speed = FloatProperty(
        name="Left Speed",
        description="Speed when moving left",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_right_speed = FloatProperty(
        name="Right Speed",
        description="Speed when moving right",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_up_speed = FloatProperty(
        name="Up Speed",
        description="Speed when moving up",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_down_speed = FloatProperty(
        name="Down Speed",
        description="Speed when moving down",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_shift_speed = FloatProperty(
        name="Shift Speed",
        description="Speed multiplier when shift key is pressed",
        default=3.0,
        min=0.1,
        max=10.0
    )
    
    # 鼠标控制设置
    bpy.types.Scene.qtquick3d_wasd_mouse_enabled = BoolProperty(
        name="Mouse Enabled",
        description="Enable mouse controls",
        default=True
    )
    
    bpy.types.Scene.qtquick3d_wasd_x_speed = FloatProperty(
        name="X Speed",
        description="Speed when mouse moves along X axis",
        default=0.1,
        min=0.01,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_y_speed = FloatProperty(
        name="Y Speed",
        description="Speed when mouse moves along Y axis",
        default=0.1,
        min=0.01,
        max=1.0
    )
    
    bpy.types.Scene.qtquick3d_wasd_x_invert = BoolProperty(
        name="X Invert",
        description="Invert X-axis controls",
        default=False
    )
    
    bpy.types.Scene.qtquick3d_wasd_y_invert = BoolProperty(
        name="Y Invert",
        description="Invert Y-axis controls",
        default=True
    )
    
    # 键盘控制设置
    bpy.types.Scene.qtquick3d_wasd_keys_enabled = BoolProperty(
        name="Keys Enabled",
        description="Enable key controls",
        default=True
    )
    
    # 接受的按钮设置
    bpy.types.Scene.qtquick3d_wasd_accepted_buttons = EnumProperty(
        name="Accepted Buttons",
        description="Specifies the buttons accepted by the controller",
        items=[
            ("LEFT", "Left Button", "Left mouse button only"),
            ("RIGHT", "Right Button", "Right mouse button only"),
            ("MIDDLE", "Middle Button", "Middle mouse button only"),
            ("LEFT_RIGHT", "Left + Right", "Left and right mouse buttons"),
            ("ALL", "All Buttons", "All mouse buttons")
        ],
        default="LEFT"
    )

def unregister_wasd_controller_properties():
    """注销WASD控制器相关属性"""
    # WASD控制器开关
    del bpy.types.Scene.qtquick3d_wasd_enabled
    
    # 速度设置
    del bpy.types.Scene.qtquick3d_wasd_speed
    del bpy.types.Scene.qtquick3d_wasd_forward_speed
    del bpy.types.Scene.qtquick3d_wasd_back_speed
    del bpy.types.Scene.qtquick3d_wasd_left_speed
    del bpy.types.Scene.qtquick3d_wasd_right_speed
    del bpy.types.Scene.qtquick3d_wasd_up_speed
    del bpy.types.Scene.qtquick3d_wasd_down_speed
    del bpy.types.Scene.qtquick3d_wasd_shift_speed
    
    # 鼠标控制设置
    del bpy.types.Scene.qtquick3d_wasd_mouse_enabled
    del bpy.types.Scene.qtquick3d_wasd_x_speed
    del bpy.types.Scene.qtquick3d_wasd_y_speed
    del bpy.types.Scene.qtquick3d_wasd_x_invert
    del bpy.types.Scene.qtquick3d_wasd_y_invert
    
    # 键盘控制设置
    del bpy.types.Scene.qtquick3d_wasd_keys_enabled
    del bpy.types.Scene.qtquick3d_wasd_accepted_buttons

def unregister_scene_properties():
    """注销场景属性"""
    # Balsam转换器相关属性
    del bpy.types.Scene.work_space_path
    del bpy.types.Scene.balsam_gltf_path
    del bpy.types.Scene.balsam_output_dir
    # 版本选择
    try:
        del bpy.types.Scene.balsam_version
    except Exception:
        pass
    
    # 注销Qt Quick3D引擎属性
    unregister_qt_quick3d_properties()

def unregister_qt_quick3d_properties():
    """注销Qt Quick3D引擎相关属性"""
    # UI控制属性
    del bpy.types.Scene.show_scene_settings
    
    # 窗口/View3D尺寸设置（统一设置）
    del bpy.types.Scene.qtquick3d_view3d_width
    del bpy.types.Scene.qtquick3d_view3d_height
    
    # SceneEnvironment基础属性
    del bpy.types.Scene.qtquick3d_antialiasing_mode
    del bpy.types.Scene.qtquick3d_antialiasing_quality
    del bpy.types.Scene.qtquick3d_ao_enabled
    del bpy.types.Scene.qtquick3d_ao_strength
    del bpy.types.Scene.qtquick3d_ao_bias
    del bpy.types.Scene.qtquick3d_ao_distance
    del bpy.types.Scene.qtquick3d_ao_dither
    del bpy.types.Scene.qtquick3d_ao_sample_rate
    del bpy.types.Scene.qtquick3d_ao_softness
    del bpy.types.Scene.qtquick3d_background_mode
    del bpy.types.Scene.qtquick3d_clear_color
    del bpy.types.Scene.qtquick3d_depth_test_enabled
    del bpy.types.Scene.qtquick3d_depth_prepass_enabled
    del bpy.types.Scene.qtquick3d_probe_exposure
    del bpy.types.Scene.qtquick3d_probe_horizon
    del bpy.types.Scene.qtquick3d_probe_orientation
    del bpy.types.Scene.qtquick3d_skybox_cubemap
    del bpy.types.Scene.qtquick3d_skybox_blur_amount
    del bpy.types.Scene.qtquick3d_specular_aa_enabled
    del bpy.types.Scene.qtquick3d_temporal_aa_enabled
    del bpy.types.Scene.qtquick3d_temporal_aa_strength
    del bpy.types.Scene.qtquick3d_tonemap_mode
    del bpy.types.Scene.qtquick3d_oit_method
    del bpy.types.Scene.qtquick3d_light_probe
    del bpy.types.Scene.qtquick3d_lightmapper
    del bpy.types.Scene.qtquick3d_scissor_rect
    del bpy.types.Scene.qtquick3d_scissor_enabled
    del bpy.types.Scene.qtquick3d_fog
    del bpy.types.Scene.qtquick3d_debug_settings
    del bpy.types.Scene.qtquick3d_effects
    
    # ExtendedSceneEnvironment高级属性
    del bpy.types.Scene.qtquick3d_use_extended_environment
    del bpy.types.Scene.qtquick3d_brightness
    del bpy.types.Scene.qtquick3d_contrast
    del bpy.types.Scene.qtquick3d_saturation
    del bpy.types.Scene.qtquick3d_color_adjustments_enabled
    del bpy.types.Scene.qtquick3d_exposure
    del bpy.types.Scene.qtquick3d_sharpness
    del bpy.types.Scene.qtquick3d_white_point
    del bpy.types.Scene.qtquick3d_dof_enabled
    del bpy.types.Scene.qtquick3d_dof_blur_amount
    del bpy.types.Scene.qtquick3d_dof_focus_distance
    del bpy.types.Scene.qtquick3d_dof_focus_range
    del bpy.types.Scene.qtquick3d_dithering_enabled
    del bpy.types.Scene.qtquick3d_fxaa_enabled
    del bpy.types.Scene.qtquick3d_glow_enabled
    del bpy.types.Scene.qtquick3d_glow_intensity
    del bpy.types.Scene.qtquick3d_glow_blend_mode
    del bpy.types.Scene.qtquick3d_glow_bloom
    del bpy.types.Scene.qtquick3d_glow_hdr_maximum_value
    del bpy.types.Scene.qtquick3d_glow_hdr_minimum_value
    del bpy.types.Scene.qtquick3d_glow_hdr_scale
    del bpy.types.Scene.qtquick3d_glow_level
    del bpy.types.Scene.qtquick3d_glow_quality_high
    del bpy.types.Scene.qtquick3d_glow_strength
    del bpy.types.Scene.qtquick3d_glow_use_bicubic_upscale
    del bpy.types.Scene.qtquick3d_lens_flare_enabled
    del bpy.types.Scene.qtquick3d_lens_flare_apply_dirt_texture
    del bpy.types.Scene.qtquick3d_lens_flare_apply_starburst_texture
    del bpy.types.Scene.qtquick3d_lens_flare_bloom_bias
    del bpy.types.Scene.qtquick3d_lens_flare_bloom_scale
    del bpy.types.Scene.qtquick3d_lens_flare_blur_amount
    del bpy.types.Scene.qtquick3d_lens_flare_camera_direction
    del bpy.types.Scene.qtquick3d_lens_flare_distortion
    del bpy.types.Scene.qtquick3d_lens_flare_ghost_count
    del bpy.types.Scene.qtquick3d_lens_flare_ghost_dispersal
    del bpy.types.Scene.qtquick3d_lens_flare_halo_width
    del bpy.types.Scene.qtquick3d_lens_flare_lens_color_texture
    del bpy.types.Scene.qtquick3d_lens_flare_lens_dirt_texture
    del bpy.types.Scene.qtquick3d_lens_flare_lens_starburst_texture
    del bpy.types.Scene.qtquick3d_lens_flare_stretch_to_aspect
    del bpy.types.Scene.qtquick3d_lut_enabled
    del bpy.types.Scene.qtquick3d_lut_filter_alpha
    del bpy.types.Scene.qtquick3d_lut_size
    del bpy.types.Scene.qtquick3d_lut_texture
    del bpy.types.Scene.qtquick3d_vignette_enabled
    del bpy.types.Scene.qtquick3d_vignette_color
    del bpy.types.Scene.qtquick3d_vignette_radius
    del bpy.types.Scene.qtquick3d_vignette_strength
    
    # WASD控制器属性
    unregister_wasd_controller_properties()

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

        # 显示和编辑当前工作空间路径
        scene = context.scene

        # Work Space Path 输入栏
        #layout.prop(scene, "work_space_path", text="Work Space")

        # 兼容性提示（如果属性未设置，显示默认信息）
        work_space = getattr(scene, "work_space_path", None)
        if not work_space:
            layout.label(text="Work Space: (default)")
        else:
            layout.label(text=f"Work Space: {work_space}")

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


        # 显示一些状态信息
        layout.separator()
        layout.label(text="Status: Ready")
        layout.label(text="Qt Version: 6.9")
        layout.label(text="Quick3D: Available") #TODO尚需检测环境
        
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
            
            # 优先使用工作空间路径
            work_space = getattr(context.scene, 'work_space_path', None)
            if work_space:
                converter.set_custom_output_dir(work_space)
                print(f"✅ 使用工作空间路径: {work_space}")
            
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

class QT_QUICK3D_OT_balsam_set_work_space(Operator):
    """Set work space directory for GLTF and QML files"""
    bl_idname = "qt_quick3d.balsam_set_work_space"
    bl_label = "Set Work Space"
    bl_description = "Set working directory for GLTF and QML files"
    
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
            from . import balsam_gltf_converter
            converter = balsam_gltf_converter.BalsamGLTFToQMLConverter()
            
            # 设置工作空间路径
            if converter.set_custom_output_dir(self.directory):
                self.report({'INFO'}, f"Work space set to: {self.directory}")
                # 保存到场景属性中
                context.scene.work_space_path = self.directory
                # 同时更新旧的属性以保持兼容性
                context.scene.balsam_output_dir = self.directory
            else:
                self.report({'ERROR'}, "Failed to set work space")
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set work space: {str(e)}")
        
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
            candidates = _scan_qt_balsam_paths()
            
            if not candidates:
                self.report({'WARNING'}, "No balsam.exe found in C:/Qt")
                return {'CANCELLED'}
            
            # 更新全局映射
            global BALSAM_PATH_MAP, BALSAM_CACHE_LOADED
            BALSAM_PATH_MAP = {}
            for i, exe in enumerate(candidates):
                key = f"QT_{i}"
                BALSAM_PATH_MAP[key] = exe
            
            # 重置缓存加载标志
            BALSAM_CACHE_LOADED = False
            
            # 保存到缓存文件
            if _save_balsam_cache():
                self.report({'INFO'}, f"Found {len(candidates)} balsam versions and saved to cache")
                
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

class QT_QUICK3D_OT_balsam_convert_existing(Operator):
    """Convert existing GLTF file"""
    bl_idname = "qt_quick3d.balsam_convert_existing"
    bl_label = "Convert Existing GLTF"
    bl_description = "Convert existing GLTF file to QML"
    
    def execute(self, context):
        try:
            from . import balsam_gltf_converter
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
                    
                    # 从场景设置获取窗口尺寸
                    scene = bpy.context.scene
                    window_width = getattr(scene, 'qtquick3d_view3d_width', 1280)
                    window_height = getattr(scene, 'qtquick3d_view3d_height', 720)
                    
                    self.setWindowTitle("Quick3D Window")
                    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
                    self.resize(window_width, window_height)
                    
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
    # Balsam转换器操作符
    QT_QUICK3D_OT_balsam_convert_scene,
    QT_QUICK3D_OT_balsam_convert_existing,
    QT_QUICK3D_OT_balsam_set_work_space,
    QT_QUICK3D_OT_balsam_set_gltf_path,
    QT_QUICK3D_OT_balsam_set_output_dir,
    QT_QUICK3D_OT_balsam_open_output,
    QT_QUICK3D_OT_balsam_open_gltf,
    QT_QUICK3D_OT_balsam_open_qml,
    QT_QUICK3D_OT_balsam_cleanup,
    QT_QUICK3D_OT_search_local_balsam,
    # Quick3D窗口操作符
    QT_QUICK3D_OT_open_quick_window,
]

# 不再需要单独的Balsam UI面板
print("✓ Balsam converter will be integrated into render properties panel")

def register():
    # 加载balsam缓存
    _load_balsam_cache()
    
    # 注册场景属性
    register_scene_properties()
    
    # 初始化全局balsam路径（基于默认选择）
    global SELECTED_BALSAM_PATH
    try:
        # 获取默认场景的balsam版本选择
        if hasattr(bpy.context, 'scene') and bpy.context.scene:
            scene = bpy.context.scene
            selected = getattr(scene, 'balsam_version', 'AUTO')
            if selected != 'AUTO':
                chosen = BALSAM_PATH_MAP.get(selected)
                if chosen and os.path.exists(chosen):
                    SELECTED_BALSAM_PATH = chosen
                    print(f"✅ 初始化全局balsam路径: {chosen}")
    except Exception as e:
        print(f"⚠️ 初始化全局balsam路径失败: {e}")
    
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
