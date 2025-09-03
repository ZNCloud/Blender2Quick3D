#!/usr/bin/env python3
"""
QML处理器模块

这个模块负责：
1. 读取balsam输出的QML文件
2. 删除import语句
3. 组装完整的QML内容（包含View3D和SceneEnvironment）
4. 将组装好的QML传递给qt_quick3d_integration
"""

import os
import re
from pathlib import Path

# 尝试导入bpy，如果不在Blender环境中则跳过
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print(" Blender环境不可用 使用默认设置")

class QMLHandler:
    """QML处理器类"""
    
    def __init__(self):
        self.qml_output_dir = None
        self.qml_content = None
        self.assembled_qml = None
        self.scene_settings = {}
        
    def setup_environment(self):
        """设置环境，获取QML输出目录"""
        try:
            # 导入balsam转换器模块以获取全局路径
            from . import balsam_gltf_converter
            self.qml_output_dir = balsam_gltf_converter.get_qml_output_dir()
            print(f"✅ QML输出目录设置成功: {self.qml_output_dir}")
            return True
        except ImportError as e:
            print(f"❌ 无法导入balsam转换器: {e}")
            # 回退到本地路径
            addon_dir = os.path.dirname(os.path.abspath(__file__))
            self.qml_output_dir = os.path.join(addon_dir, "output")
            print(f"⚠️ 使用本地QML输出目录: {self.qml_output_dir}")
            return False
        except Exception as e:
            print(f"❌ 设置环境失败: {e}")
            return False
    
    def find_qml_files(self):
        """查找QML输出目录中的QML文件"""
        if not self.qml_output_dir or not os.path.exists(self.qml_output_dir):
            print(f"❌ QML输出目录不存在: {self.qml_output_dir}")
            return []
        
        qml_files = []
        try:
            for file in os.listdir(self.qml_output_dir):
                if file.endswith('.qml'):
                    qml_files.append(os.path.join(self.qml_output_dir, file))
            
            print(f"✅ 找到 {len(qml_files)} 个QML文件:")
            for qml_file in qml_files:
                print(f"  📄 {os.path.basename(qml_file)}")
            
            return qml_files
        except Exception as e:
            print(f"❌ 查找QML文件失败: {e}")
            return []
    
    def read_qml_file(self, qml_file_path):
        """读取QML文件内容"""
        try:
            if not os.path.exists(qml_file_path):
                print(f"❌ QML文件不存在: {qml_file_path}")
                return None
            
            with open(qml_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✅ 成功读取QML文件: {os.path.basename(qml_file_path)}")
            print(f"  📊 文件大小: {len(content)} 字符")
            
            self.qml_content = content
            return content
            
        except Exception as e:
            print(f"❌ 读取QML文件失败: {e}")
            return None
    
    def remove_import_statements(self, qml_content):
        """删除QML文件中的import语句"""
        if not qml_content:
            print("❌ 没有QML内容可处理")
            return None
        
        try:
            # 使用正则表达式删除import语句
            # 匹配以import开头的行，包括可能的注释
            pattern = r'^\s*import\s+.*?(?:\n|$)'
            cleaned_content = re.sub(pattern, '', qml_content, flags=re.MULTILINE)
            
            # 清理多余的空行
            cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)
            
            print(f"✅ 成功删除import语句")
            print(f"  📊 原始内容长度: {len(qml_content)} 字符")
            print(f"  📊 清理后长度: {len(cleaned_content)} 字符")
            
            return cleaned_content
            
        except Exception as e:
            print(f"❌ 删除import语句失败: {e}")
            return qml_content
    
    def read_scene_properties(self):
        """从Blender场景中读取Qt Quick3D属性设置"""
        if not BLENDER_AVAILABLE:
            print("⚠️ Blender环境不可用，使用默认设置")
            return self.get_default_scene_settings()
        
        try:
            scene = bpy.context.scene
            settings = {}
            
            # View3D尺寸设置（同时作为窗口尺寸，因为View3D覆盖全窗口）
            settings['view3d_width'] = getattr(scene, 'qtquick3d_view3d_width', 1280)
            settings['view3d_height'] = getattr(scene, 'qtquick3d_view3d_height', 720)
            
            # SceneEnvironment基础属性
            settings['antialiasing_mode'] = getattr(scene, 'qtquick3d_antialiasing_mode', 0)
            settings['antialiasing_quality'] = getattr(scene, 'qtquick3d_antialiasing_quality', 2)
            settings['ao_enabled'] = getattr(scene, 'qtquick3d_ao_enabled', False)
            settings['ao_strength'] = getattr(scene, 'qtquick3d_ao_strength', 1.0)
            settings['ao_bias'] = getattr(scene, 'qtquick3d_ao_bias', 0.0)
            settings['ao_distance'] = getattr(scene, 'qtquick3d_ao_distance', 5.0)
            settings['ao_dither'] = getattr(scene, 'qtquick3d_ao_dither', False)
            settings['ao_sample_rate'] = getattr(scene, 'qtquick3d_ao_sample_rate', 2)
            settings['ao_softness'] = getattr(scene, 'qtquick3d_ao_softness', 0.0)
            settings['background_mode'] = getattr(scene, 'qtquick3d_background_mode', 0)
            settings['clear_color'] = getattr(scene, 'qtquick3d_clear_color', (0.0, 0.0, 0.0, 1.0))
            settings['depth_test_enabled'] = getattr(scene, 'qtquick3d_depth_test_enabled', True)
            settings['depth_prepass_enabled'] = getattr(scene, 'qtquick3d_depth_prepass_enabled', False)
            settings['probe_exposure'] = getattr(scene, 'qtquick3d_probe_exposure', 0.0)
            settings['probe_horizon'] = getattr(scene, 'qtquick3d_probe_horizon', 0.0)
            settings['probe_orientation'] = getattr(scene, 'qtquick3d_probe_orientation', (0.0, 0.0, 0.0))
            settings['skybox_cubemap'] = getattr(scene, 'qtquick3d_skybox_cubemap', "")
            settings['skybox_blur_amount'] = getattr(scene, 'qtquick3d_skybox_blur_amount', 0.0)
            settings['specular_aa_enabled'] = getattr(scene, 'qtquick3d_specular_aa_enabled', False)
            settings['temporal_aa_enabled'] = getattr(scene, 'qtquick3d_temporal_aa_enabled', False)
            settings['temporal_aa_strength'] = getattr(scene, 'qtquick3d_temporal_aa_strength', 0.0)
            settings['tonemap_mode'] = getattr(scene, 'qtquick3d_tonemap_mode', 0)
            settings['oit_method'] = getattr(scene, 'qtquick3d_oit_method', 0)
            settings['light_probe'] = getattr(scene, 'qtquick3d_light_probe', "")
            settings['lightmapper'] = getattr(scene, 'qtquick3d_lightmapper', 0)
            # scissor_rect: (x, y, width, height) - x,y是左上角坐标，width,height是View3D分辨率
            default_scissor_rect = (0.0, 0.0, settings.get('view3d_width', 1280), settings.get('view3d_height', 720))
            scissor_rect = getattr(scene, 'qtquick3d_scissor_rect', default_scissor_rect)
            
            # 检查是否是归一化坐标（旧格式），如果是则转换为像素坐标
            if len(scissor_rect) >= 4 and scissor_rect[2] <= 1.0 and scissor_rect[3] <= 1.0:
                # 检测到归一化坐标，转换为像素坐标
                view3d_width = settings.get('view3d_width', 1280)
                view3d_height = settings.get('view3d_height', 720)
                settings['scissor_rect'] = (scissor_rect[0], scissor_rect[1], view3d_width, view3d_height)
                print(f"⚠️ 检测到归一化scissor_rect，已自动转换为像素坐标: {settings['scissor_rect']}")
            else:
                settings['scissor_rect'] = scissor_rect
            settings['fog'] = getattr(scene, 'qtquick3d_fog', "")
            settings['debug_settings'] = getattr(scene, 'qtquick3d_debug_settings', "")
            settings['effects'] = getattr(scene, 'qtquick3d_effects', "")
            
            # ExtendedSceneEnvironment高级属性
            settings['use_extended_environment'] = getattr(scene, 'qtquick3d_use_extended_environment', False)
            settings['color_adjustments_enabled'] = getattr(scene, 'qtquick3d_color_adjustments_enabled', False)
            settings['brightness'] = getattr(scene, 'qtquick3d_brightness', 0.0)
            settings['contrast'] = getattr(scene, 'qtquick3d_contrast', 0.0)
            settings['saturation'] = getattr(scene, 'qtquick3d_saturation', 0.0)
            settings['exposure'] = getattr(scene, 'qtquick3d_exposure', 0.0)
            settings['sharpness'] = getattr(scene, 'qtquick3d_sharpness', 0.0)
            settings['white_point'] = getattr(scene, 'qtquick3d_white_point', 1.0)
            settings['dof_enabled'] = getattr(scene, 'qtquick3d_dof_enabled', False)
            settings['dof_blur_amount'] = getattr(scene, 'qtquick3d_dof_blur_amount', 0.0)
            settings['dof_focus_distance'] = getattr(scene, 'qtquick3d_dof_focus_distance', 100.0)
            settings['dof_focus_range'] = getattr(scene, 'qtquick3d_dof_focus_range', 10.0)
            settings['dithering_enabled'] = getattr(scene, 'qtquick3d_dithering_enabled', False)
            settings['fxaa_enabled'] = getattr(scene, 'qtquick3d_fxaa_enabled', False)
            settings['glow_enabled'] = getattr(scene, 'qtquick3d_glow_enabled', False)
            settings['glow_intensity'] = getattr(scene, 'qtquick3d_glow_intensity', 0.0)
            settings['glow_blend_mode'] = getattr(scene, 'qtquick3d_glow_blend_mode', 0)
            settings['glow_bloom'] = getattr(scene, 'qtquick3d_glow_bloom', 0.0)
            settings['glow_hdr_maximum_value'] = getattr(scene, 'qtquick3d_glow_hdr_maximum_value', 1.0)
            settings['glow_hdr_minimum_value'] = getattr(scene, 'qtquick3d_glow_hdr_minimum_value', 0.0)
            settings['glow_hdr_scale'] = getattr(scene, 'qtquick3d_glow_hdr_scale', 1.0)
            settings['glow_level'] = getattr(scene, 'qtquick3d_glow_level', 0)
            settings['glow_quality_high'] = getattr(scene, 'qtquick3d_glow_quality_high', False)
            settings['glow_strength'] = getattr(scene, 'qtquick3d_glow_strength', 0.0)
            settings['glow_use_bicubic_upscale'] = getattr(scene, 'qtquick3d_glow_use_bicubic_upscale', False)
            settings['lens_flare_enabled'] = getattr(scene, 'qtquick3d_lens_flare_enabled', False)
            settings['lens_flare_apply_dirt_texture'] = getattr(scene, 'qtquick3d_lens_flare_apply_dirt_texture', False)
            settings['lens_flare_apply_starburst_texture'] = getattr(scene, 'qtquick3d_lens_flare_apply_starburst_texture', False)
            settings['lens_flare_bloom_bias'] = getattr(scene, 'qtquick3d_lens_flare_bloom_bias', 0.0)
            settings['lens_flare_bloom_scale'] = getattr(scene, 'qtquick3d_lens_flare_bloom_scale', 1.0)
            settings['lens_flare_blur_amount'] = getattr(scene, 'qtquick3d_lens_flare_blur_amount', 0.0)
            settings['lens_flare_camera_direction'] = getattr(scene, 'qtquick3d_lens_flare_camera_direction', (0.0, 0.0, 1.0))
            settings['lens_flare_distortion'] = getattr(scene, 'qtquick3d_lens_flare_distortion', 0.0)
            settings['lens_flare_ghost_count'] = getattr(scene, 'qtquick3d_lens_flare_ghost_count', 4)
            settings['lens_flare_ghost_dispersal'] = getattr(scene, 'qtquick3d_lens_flare_ghost_dispersal', 0.3)
            settings['lens_flare_halo_width'] = getattr(scene, 'qtquick3d_lens_flare_halo_width', 0.0)
            settings['lens_flare_lens_color_texture'] = getattr(scene, 'qtquick3d_lens_flare_lens_color_texture', "")
            settings['lens_flare_lens_dirt_texture'] = getattr(scene, 'qtquick3d_lens_flare_lens_dirt_texture', "")
            settings['lens_flare_lens_starburst_texture'] = getattr(scene, 'qtquick3d_lens_flare_lens_starburst_texture', "")
            settings['lens_flare_stretch_to_aspect'] = getattr(scene, 'qtquick3d_lens_flare_stretch_to_aspect', 0.0)
            settings['lut_enabled'] = getattr(scene, 'qtquick3d_lut_enabled', False)
            settings['lut_filter_alpha'] = getattr(scene, 'qtquick3d_lut_filter_alpha', 1.0)
            settings['lut_size'] = getattr(scene, 'qtquick3d_lut_size', 32.0)
            settings['lut_texture'] = getattr(scene, 'qtquick3d_lut_texture', "")
            settings['vignette_enabled'] = getattr(scene, 'qtquick3d_vignette_enabled', False)
            settings['vignette_color'] = getattr(scene, 'qtquick3d_vignette_color', (0.0, 0.0, 0.0, 1.0))
            settings['vignette_radius'] = getattr(scene, 'qtquick3d_vignette_radius', 0.5)
            settings['vignette_strength'] = getattr(scene, 'qtquick3d_vignette_strength', 0.0)
            
            self.scene_settings = settings
            print(f"✅ 成功读取场景属性，共 {len(settings)} 个设置")
            return settings
            
        except Exception as e:
            print(f"❌ 读取场景属性失败: {e}")
            return self.get_default_scene_settings()
    
    def get_default_scene_settings(self):
        """获取默认的场景设置"""
        return {
            'view3d_width': 1280,
            'view3d_height': 720,
            'scissor_rect': (0.0, 0.0, 1280, 720),  # 默认使用View3D分辨率
            'antialiasing_mode': 0,
            'antialiasing_quality': 2,
            'ao_enabled': False,
            'ao_strength': 1.0,
            'background_mode': 0,
            'clear_color': (0.0, 0.0, 0.0, 1.0),
            'depth_test_enabled': True,
            'probe_exposure': 0.0,
            'probe_horizon': 0.0,
            'tonemap_mode': 0,
            'use_extended_environment': False,
            'color_adjustments_enabled': False,
            'brightness': 0.0,
            'contrast': 0.0,
            'saturation': 0.0,
            'exposure': 0.0,
            'sharpness': 0.0,
            'white_point': 1.0,
            'dof_enabled': False,
            'dof_blur_amount': 0.0,
            'glow_enabled': False,
            'glow_intensity': 0.0,
            'lens_flare_enabled': False,
            'lut_enabled': False,
            'vignette_enabled': False,
            'vignette_strength': 0.0
        }
    
    def convert_color_to_qml(self, color_tuple):
        """将Blender颜色元组转换为QML颜色字符串"""
        if len(color_tuple) >= 3:
            r, g, b = color_tuple[:3]
            # 转换为0-255范围
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        return "#000000"
    
    def convert_vector3d_to_qml(self, vector_tuple):
        """将Blender向量元组转换为QML vector3d字符串"""
        if len(vector_tuple) >= 3:
            x, y, z = vector_tuple[:3]
            return f"Qt.vector3d({x}, {y}, {z})"
        return "Qt.vector3d(0, 0, 0)"
    
    def convert_rect_to_qml(self, rect_tuple):
        """将Blender矩形元组转换为QML rect字符串"""
        if len(rect_tuple) >= 4:
            x, y, w, h = rect_tuple[:4]
            return f"Qt.rect({x}, {y}, {w}, {h})"
        return "Qt.rect(0, 0, 1, 1)"
    
    def get_antialiasing_mode_qml(self, mode):
        """获取抗锯齿模式的QML字符串"""
        modes = {
            0: "SceneEnvironment.NoAA",
            1: "SceneEnvironment.SSAA",
            2: "SceneEnvironment.MSAA",
            3: "SceneEnvironment.ProgressiveAA"
        }
        return modes.get(mode, "SceneEnvironment.MSAA")
    
    def get_antialiasing_quality_qml(self, quality):
        """获取抗锯齿质量的QML字符串"""
        qualities = {
            0: "SceneEnvironment.Low",
            1: "SceneEnvironment.Medium", 
            2: "SceneEnvironment.High",
            3: "SceneEnvironment.VeryHigh"
        }
        return qualities.get(quality, "SceneEnvironment.High")
    
    def get_background_mode_qml(self, mode):
        """获取背景模式的QML字符串"""
        modes = {
            0: "SceneEnvironment.Color",
            1: "SceneEnvironment.SkyBox",
            2: "SceneEnvironment.Transparent",
            3: "SceneEnvironment.Unspecified"
        }
        return modes.get(mode, "SceneEnvironment.Color")
    
    def get_tonemap_mode_qml(self, mode):
        """获取色调映射模式的QML字符串"""
        modes = {
            0: "SceneEnvironment.TonemapModeNone",
            1: "SceneEnvironment.TonemapModeLinear",
            2: "SceneEnvironment.TonemapModeAces",
            3: "SceneEnvironment.TonemapModeHejlDawson",
            4: "SceneEnvironment.TonemapModeFilmic"
        }
        return modes.get(mode, "SceneEnvironment.TonemapModeNone")
    
    def get_oit_method_qml(self, method):
        """获取顺序无关透明度方法的QML字符串"""
        methods = {
            0: "SceneEnvironment.NoOIT",
            1: "SceneEnvironment.WeightedBlendedOIT",
            2: "SceneEnvironment.WeightedOIT"
        }
        return methods.get(method, "SceneEnvironment.NoOIT")
    
    def get_glow_blend_mode_qml(self, mode):
        """获取发光混合模式的QML字符串"""
        modes = {
            0: "ExtendedSceneEnvironment.Additive",
            1: "ExtendedSceneEnvironment.Screen",
            2: "ExtendedSceneEnvironment.Multiply",
            3: "ExtendedSceneEnvironment.Overlay"
        }
        return modes.get(mode, "ExtendedSceneEnvironment.Additive")
    
    def assemble_complete_qml(self, cleaned_qml_content, scene_name="DemoScene"):
        """组装完整的QML内容，包含View3D和SceneEnvironment"""
        if not cleaned_qml_content:
            print("❌ 没有清理后的QML内容可组装")
            return None
        
        try:
            # 读取场景属性
            settings = self.read_scene_properties()
            
            # 生成SceneEnvironment QML字符串
            scene_environment_qml = self.generate_scene_environment_qml(settings)
            
            # 创建完整的QML内容
            head_qml = """"""
            complete_qml = f'''import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

Window {{
    visible: true
    width: {settings['view3d_width']}
    height: {settings['view3d_height']}
    title: "Quick3D Scene - {scene_name}"
    
    View3D {{
        id: view3D
        anchors.fill: parent
        
        environment: {scene_environment_qml}
        
        // 插入清理后的QML内容
        {cleaned_qml_content}
    }}
}}'''
            
            print(f"✅ 成功组装完整QML内容")
            print(f"  📊 组装后长度: {len(complete_qml)} 字符")
            print(f"  📊 View3D尺寸: {settings['view3d_width']}x{settings['view3d_height']}")
            
            self.assembled_qml = head_qml + complete_qml
            return self.assembled_qml
            
        except Exception as e:
            print(f"❌ 组装QML内容失败: {e}")
            return None
    
    def generate_scene_environment_qml(self, settings):
        """生成SceneEnvironment的QML字符串"""
        try:
            # 基础SceneEnvironment设置
            qml_parts = []
            
            # 基本属性
            qml_parts.append(f"backgroundMode: {self.get_background_mode_qml(settings['background_mode'])}")
            qml_parts.append(f"antialiasingMode: {self.get_antialiasing_mode_qml(settings['antialiasing_mode'])}")
            qml_parts.append(f"antialiasingQuality: {self.get_antialiasing_quality_qml(settings['antialiasing_quality'])}")
            
            # 只有在Color模式下才设置clearColor
            if settings['background_mode'] == 0:  # SceneEnvironment.Color
                qml_parts.append(f"clearColor: \"{self.convert_color_to_qml(settings['clear_color'])}\"")
            
            # 环境光遮蔽
            if settings['ao_enabled']:
                qml_parts.append(f"aoEnabled: true")
                qml_parts.append(f"aoStrength: {settings['ao_strength']}")
                qml_parts.append(f"aoBias: {settings['ao_bias']}")
                qml_parts.append(f"aoDistance: {settings['ao_distance']}")
                qml_parts.append(f"aoDither: {str(settings['ao_dither']).lower()}")
                qml_parts.append(f"aoSampleRate: {settings['ao_sample_rate']}")
                qml_parts.append(f"aoSoftness: {settings['ao_softness']}")
            else:
                qml_parts.append(f"aoEnabled: false")
            
            # 深度设置
            qml_parts.append(f"depthTestEnabled: {str(settings['depth_test_enabled']).lower()}")
            if settings['depth_prepass_enabled']:
                qml_parts.append(f"depthPrePassEnabled: true")
            
            # 环境探针
            if settings['probe_exposure'] != 0.0:
                qml_parts.append(f"probeExposure: {settings['probe_exposure']}")
            if settings['probe_horizon'] != 0.0:
                qml_parts.append(f"probeHorizon: {settings['probe_horizon']}")
            if settings['probe_orientation'] != (0.0, 0.0, 0.0):
                qml_parts.append(f"probeOrientation: {self.convert_vector3d_to_qml(settings['probe_orientation'])}")
            
            # 天空盒
            if settings['skybox_cubemap']:
                qml_parts.append(f"skyBoxCubeMap: \"{settings['skybox_cubemap']}\"")
            if settings['skybox_blur_amount'] > 0.0:
                qml_parts.append(f"skyboxBlurAmount: {settings['skybox_blur_amount']}")
            
            # 抗锯齿高级设置
            if settings['specular_aa_enabled']:
                qml_parts.append(f"specularAAEnabled: true")
            if settings['temporal_aa_enabled']:
                qml_parts.append(f"temporalAAEnabled: true")
                qml_parts.append(f"temporalAAStrength: {settings['temporal_aa_strength']}")
            
            # 色调映射
            if settings['tonemap_mode'] != 0:
                qml_parts.append(f"tonemapMode: {self.get_tonemap_mode_qml(settings['tonemap_mode'])}")
            
            # 顺序无关透明度
            if settings['oit_method'] != 0:
                qml_parts.append(f"oitMethod: {self.get_oit_method_qml(settings['oit_method'])}")
            
            # 光照探针
            if settings['light_probe']:
                qml_parts.append(f"lightProbe: \"{settings['light_probe']}\"")
            
            # 光照映射器
            if settings['lightmapper'] != 0:
                qml_parts.append(f"lightmapper: {settings['lightmapper']}")
            
            # 裁剪矩形（总是设置，使用View3D的实际分辨率）
            qml_parts.append(f"scissorRect: {self.convert_rect_to_qml(settings['scissor_rect'])}")
            
            # 雾效
            if settings['fog']:
                qml_parts.append(f"fog: \"{settings['fog']}\"")
            
            # 调试设置
            if settings['debug_settings']:
                qml_parts.append(f"debugSettings: \"{settings['debug_settings']}\"")
            
            # 效果
            if settings['effects']:
                qml_parts.append(f"effects: \"{settings['effects']}\"")
            
            # 检查是否使用ExtendedSceneEnvironment
            if settings['use_extended_environment']:
                # 生成ExtendedSceneEnvironment
                extended_qml = self.generate_extended_scene_environment_qml(settings)
                return f"ExtendedSceneEnvironment {{\n    {extended_qml}\n}}"
            else:
                # 生成基础SceneEnvironment  
                qml_content = "\n    ".join(qml_parts)
                return f"SceneEnvironment {{\n    {qml_content}\n}}"
                
        except Exception as e:
            print(f"❌ 生成SceneEnvironment QML失败: {e}")
            return "SceneEnvironment {\n    clearColor: \"#303030\"\n    backgroundMode: SceneEnvironment.Color\n    antialiasingMode: SceneEnvironment.MSAA\n    antialiasingQuality: SceneEnvironment.High\n}"
    
    def generate_extended_scene_environment_qml(self, settings):
        """生成ExtendedSceneEnvironment的QML字符串"""
        try:
            qml_parts = []
            
            # 基础SceneEnvironment属性（继承）
            qml_parts.append(f"backgroundMode: {self.get_background_mode_qml(settings['background_mode'])}")
            qml_parts.append(f"antialiasingMode: {self.get_antialiasing_mode_qml(settings['antialiasing_mode'])}")
            qml_parts.append(f"antialiasingQuality: {self.get_antialiasing_quality_qml(settings['antialiasing_quality'])}")
            
            # 只有在Color模式下才设置clearColor
            if settings['background_mode'] == 0:  # SceneEnvironment.Color
                qml_parts.append(f"clearColor: \"{self.convert_color_to_qml(settings['clear_color'])}\"")
            
            # 环境光遮蔽
            if settings['ao_enabled']:
                qml_parts.append(f"aoEnabled: true")
                qml_parts.append(f"aoStrength: {settings['ao_strength']}")
            else:
                qml_parts.append(f"aoEnabled: false")
            
            # 深度设置
            qml_parts.append(f"depthTestEnabled: {str(settings['depth_test_enabled']).lower()}")
            
            # 环境探针
            if settings['probe_exposure'] != 0.0:
                qml_parts.append(f"probeExposure: {settings['probe_exposure']}")
            if settings['probe_horizon'] != 0.0:
                qml_parts.append(f"probeHorizon: {settings['probe_horizon']}")
            
            # 色调映射
            if settings['tonemap_mode'] != 0:
                qml_parts.append(f"tonemapMode: {self.get_tonemap_mode_qml(settings['tonemap_mode'])}")
            
            # ExtendedSceneEnvironment特有属性
            
            # 颜色调整
            if settings['color_adjustments_enabled']:
                qml_parts.append(f"colorAdjustmentsEnabled: true")
                if settings['brightness'] != 0.0:
                    qml_parts.append(f"adjustmentBrightness: {settings['brightness']}")
                if settings['contrast'] != 0.0:
                    qml_parts.append(f"adjustmentContrast: {settings['contrast']}")
                if settings['saturation'] != 0.0:
                    qml_parts.append(f"adjustmentSaturation: {settings['saturation']}")
            else:
                qml_parts.append(f"colorAdjustmentsEnabled: false")
            
            # 曝光和锐化
            if settings['exposure'] != 0.0:
                qml_parts.append(f"exposure: {settings['exposure']}")
            if settings['sharpness'] != 0.0:
                qml_parts.append(f"sharpnessAmount: {settings['sharpness']}")
            if settings['white_point'] != 1.0:
                qml_parts.append(f"whitePoint: {settings['white_point']}")
            
            # 景深效果
            if settings['dof_enabled']:
                qml_parts.append(f"depthOfFieldEnabled: true")
                qml_parts.append(f"depthOfFieldBlurAmount: {settings['dof_blur_amount']}")
                qml_parts.append(f"depthOfFieldFocusDistance: {settings['dof_focus_distance']}")
                qml_parts.append(f"depthOfFieldFocusRange: {settings['dof_focus_range']}")
            else:
                qml_parts.append(f"depthOfFieldEnabled: false")
            
            # 抖动
            if settings['dithering_enabled']:
                qml_parts.append(f"ditheringEnabled: true")
            
            # FXAA
            if settings['fxaa_enabled']:
                qml_parts.append(f"fxaaEnabled: true")
            
            # 发光效果
            if settings['glow_enabled']:
                qml_parts.append(f"glowEnabled: true")
                qml_parts.append(f"glowIntensity: {settings['glow_intensity']}")
                qml_parts.append(f"glowBlendMode: {self.get_glow_blend_mode_qml(settings['glow_blend_mode'])}")
                if settings['glow_bloom'] > 0.0:
                    qml_parts.append(f"glowBloom: {settings['glow_bloom']}")
                if settings['glow_hdr_maximum_value'] != 1.0:
                    qml_parts.append(f"glowHDRMaximumValue: {settings['glow_hdr_maximum_value']}")
                if settings['glow_hdr_minimum_value'] != 0.0:
                    qml_parts.append(f"glowHDRMinimumValue: {settings['glow_hdr_minimum_value']}")
                if settings['glow_hdr_scale'] != 1.0:
                    qml_parts.append(f"glowHDRScale: {settings['glow_hdr_scale']}")
                if settings['glow_level'] != 0:
                    qml_parts.append(f"glowLevel: {settings['glow_level']}")
                if settings['glow_quality_high']:
                    qml_parts.append(f"glowQualityHigh: true")
                if settings['glow_strength'] != 0.0:
                    qml_parts.append(f"glowStrength: {settings['glow_strength']}")
                if settings['glow_use_bicubic_upscale']:
                    qml_parts.append(f"glowUseBicubicUpscale: true")
            else:
                qml_parts.append(f"glowEnabled: false")
            
            # 镜头光晕
            if settings['lens_flare_enabled']:
                qml_parts.append(f"lensFlareEnabled: true")
                qml_parts.append(f"lensFlareGhostCount: {settings['lens_flare_ghost_count']}")
                qml_parts.append(f"lensFlareGhostDispersal: {settings['lens_flare_ghost_dispersal']}")
                if settings['lens_flare_blur_amount'] > 0.0:
                    qml_parts.append(f"lensFlareBlurAmount: {settings['lens_flare_blur_amount']}")
                if settings['lens_flare_camera_direction'] != (0.0, 0.0, 1.0):
                    qml_parts.append(f"lensFlareCameraDirection: {self.convert_vector3d_to_qml(settings['lens_flare_camera_direction'])}")
                if settings['lens_flare_distortion'] != 0.0:
                    qml_parts.append(f"lensFlareDistortion: {settings['lens_flare_distortion']}")
                if settings['lens_flare_halo_width'] > 0.0:
                    qml_parts.append(f"lensFlareHaloWidth: {settings['lens_flare_halo_width']}")
                if settings['lens_flare_apply_dirt_texture']:
                    qml_parts.append(f"lensFlareApplyDirtTexture: true")
                if settings['lens_flare_apply_starburst_texture']:
                    qml_parts.append(f"lensFlareApplyStarburstTexture: true")
                if settings['lens_flare_bloom_bias'] != 0.0:
                    qml_parts.append(f"lensFlareBloomBias: {settings['lens_flare_bloom_bias']}")
                if settings['lens_flare_bloom_scale'] != 1.0:
                    qml_parts.append(f"lensFlareBloomScale: {settings['lens_flare_bloom_scale']}")
                if settings['lens_flare_stretch_to_aspect'] > 0.0:
                    qml_parts.append(f"lensFlareStretchToAspect: {settings['lens_flare_stretch_to_aspect']}")
                if settings['lens_flare_lens_color_texture']:
                    qml_parts.append(f"lensFlareLensColorTexture: \"{settings['lens_flare_lens_color_texture']}\"")
                if settings['lens_flare_lens_dirt_texture']:
                    qml_parts.append(f"lensFlareLensDirtTexture: \"{settings['lens_flare_lens_dirt_texture']}\"")
                if settings['lens_flare_lens_starburst_texture']:
                    qml_parts.append(f"lensFlareLensStarburstTexture: \"{settings['lens_flare_lens_starburst_texture']}\"")
            else:
                qml_parts.append(f"lensFlareEnabled: false")
            
            # LUT设置
            if settings['lut_enabled']:
                qml_parts.append(f"lutEnabled: true")
                if settings['lut_filter_alpha'] != 1.0:
                    qml_parts.append(f"lutFilterAlpha: {settings['lut_filter_alpha']}")
                if settings['lut_size'] != 32.0:
                    qml_parts.append(f"lutSize: {settings['lut_size']}")
                if settings['lut_texture']:
                    qml_parts.append(f"lutTexture: \"{settings['lut_texture']}\"")
            else:
                qml_parts.append(f"lutEnabled: false")
            
            # 暗角效果
            if settings['vignette_enabled']:
                qml_parts.append(f"vignetteEnabled: true")
                qml_parts.append(f"vignetteStrength: {settings['vignette_strength']}")
                qml_parts.append(f"vignetteRadius: {settings['vignette_radius']}")
                qml_parts.append(f"vignetteColor: \"{self.convert_color_to_qml(settings['vignette_color'])}\"")
            else:
                qml_parts.append(f"vignetteEnabled: false")
            
            return "\n    ".join(qml_parts)
            
        except Exception as e:
            print(f"❌ 生成ExtendedSceneEnvironment QML失败: {e}")
            
            return f"clearColor: \"{self.convert_color_to_qml(settings['clear_color'])}\"\n    backgroundMode: {self.get_background_mode_qml(settings['background_mode'])}\n    antialiasingMode: {self.get_antialiasing_mode_qml(settings['antialiasing_mode'])}\n    antialiasingQuality: {self.get_antialiasing_quality_qml(settings['antialiasing_quality'])}"
    
    def get_assembled_qml(self):
        """获取组装好的QML内容"""
        return self.assembled_qml
    
    def save_assembled_qml(self, output_path=None):
        """保存组装好的QML到文件"""
        if not self.assembled_qml:
            print("❌ 没有组装好的QML内容可保存")
            return False
        
        try:
            if not output_path:
                # 使用默认路径
                scene_name = "AssembledScene"
                output_path = os.path.join(self.qml_output_dir, f"{scene_name}.qml")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.assembled_qml)
            
            print(f"✅ 成功保存组装后的QML文件: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 保存QML文件失败: {e}")
            return False
    
    def process_qml_file(self, qml_file_path=None, scene_name=None):
        """处理QML文件的完整流程"""
        try:
            print("🚀 开始处理QML文件...")
            
            # 1. 设置环境
            if not self.setup_environment():
                return False
            
            # 2. 查找QML文件
            if not qml_file_path:
                qml_files = self.find_qml_files()
                if not qml_files:
                    print("❌ 未找到QML文件")
                    return False
                qml_file_path = qml_files[0]  # 使用第一个找到的QML文件
            
            # 3. 读取QML文件
            qml_content = self.read_qml_file(qml_file_path)
            if not qml_content:
                return False
            
            # 4. 删除import语句
            cleaned_content = self.remove_import_statements(qml_content)
            if not cleaned_content:
                return False
            
            # 5. 组装完整QML
            if not scene_name:
                scene_name = os.path.splitext(os.path.basename(qml_file_path))[0]
            
            complete_qml = self.assemble_complete_qml(cleaned_content, scene_name)
            if not complete_qml:
                return False
            
            print("🎉 QML文件处理完成！")
            return True
            
        except Exception as e:
            print(f"❌ QML文件处理失败: {e}")
            return False
    
    def get_qml_for_qt_quick3d(self):
        """获取用于Qt Quick3D集成的QML内容"""
        if not self.assembled_qml:
            print("❌ 没有组装好的QML内容")
            return None
        print("self.assembled_qml as below: ",self.assembled_qml)
        return self.assembled_qml
    
    def get_qml_as_bytes(self):
        """获取QML内容作为字节数据（用于QQmlApplicationEngine.loadData）"""
        if not self.assembled_qml:
            print("❌ 没有组装好的QML内容")
            return None
        
        try:
            return self.assembled_qml.encode('utf-8')
        except Exception as e:
            print(f"❌ 转换QML内容为字节失败: {e}")
            return None

def create_qml_handler():
    """创建QML处理器实例"""
    return QMLHandler()

def process_qml_for_qt_quick3d(qml_file_path=None, scene_name=None):
    """便捷函数：处理QML文件并返回用于Qt Quick3D的内容"""
    handler = QMLHandler()
    
    if handler.process_qml_file(qml_file_path, scene_name):
        return handler.get_qml_for_qt_quick3d()
    else:
        return None

def get_qml_content_for_integration():
    """获取用于集成的QML内容（主要接口函数）"""
    try:
        # 创建处理器并处理QML文件
        handler = QMLHandler()
        
        # 自动处理QML文件
        if handler.process_qml_file():
            qml_content = handler.get_qml_for_qt_quick3d()
            if qml_content:
                print("✅ 成功获取用于集成的QML内容")
                return qml_content
            else:
                print("❌ 无法获取QML内容")
                return None
        else:
            print("❌ QML文件处理失败")
            return None
            
    except Exception as e:
        print(f"❌ 获取QML内容失败: {e}")
        return None

# 测试函数
def test_qml_handler():
    """测试QML处理器"""
    print("=" * 50)
    print("QML处理器测试")
    print("=" * 50)
    
    handler = QMLHandler()
    
    # 测试环境设置
    print("1. 测试环境设置...")
    if handler.setup_environment():
        print("✅ 环境设置成功")
    else:
        print("❌ 环境设置失败")
        return
    
    # 测试查找QML文件
    print("\n2. 测试查找QML文件...")
    qml_files = handler.find_qml_files()
    if qml_files:
        print(f"✅ 找到 {len(qml_files)} 个QML文件")
        
        # 测试处理第一个QML文件
        test_file = qml_files[0]
        print(f"\n3. 测试处理QML文件: {os.path.basename(test_file)}")
        
        if handler.process_qml_file(test_file):
            print("✅ QML文件处理成功")
            
            # 获取组装后的内容
            assembled_qml = handler.get_assembled_qml()
            if assembled_qml:
                print(f"✅ 获取到组装后的QML内容，长度: {len(assembled_qml)} 字符")
                
                # 保存到文件
                if handler.save_assembled_qml():
                    print("✅ 保存组装后的QML文件成功")
                else:
                    print("❌ 保存QML文件失败")
            else:
                print("❌ 无法获取组装后的QML内容")
        else:
            print("❌ QML文件处理失败")
    else:
        print("❌ 未找到QML文件")
    
    print("=" * 50)

def test_scene_properties_integration():
    """测试场景属性集成功能"""
    print("=" * 60)
    print("测试场景属性集成功能")
    print("=" * 60)
    
    handler = QMLHandler()
    
    # 测试读取场景属性
    print("1. 测试读取场景属性...")
    settings = handler.read_scene_properties()
    if settings:
        print(f"✅ 成功读取场景属性，共 {len(settings)} 个设置")
        print(f"  📊 View3D尺寸: {settings['view3d_width']}x{settings['view3d_height']}")
        print(f"  📊 抗锯齿模式: {settings['antialiasing_mode']}")
        print(f"  📊 使用扩展环境: {settings['use_extended_environment']}")
    else:
        print("❌ 读取场景属性失败")
        return
    
    # 测试生成SceneEnvironment QML
    print("\n2. 测试生成SceneEnvironment QML...")
    scene_env_qml = handler.generate_scene_environment_qml(settings)
    if scene_env_qml:
        print("✅ 成功生成SceneEnvironment QML")
        print(f"  📊 QML长度: {len(scene_env_qml)} 字符")
        print("  📄 生成的QML片段:")
        print("  " + scene_env_qml[:200] + "..." if len(scene_env_qml) > 200 else "  " + scene_env_qml)
    else:
        print("❌ 生成SceneEnvironment QML失败")
        return
    
    # 测试组装完整QML
    print("\n3. 测试组装完整QML...")
    test_content = "Model { source: \"#Cube\" }"
    complete_qml = handler.assemble_complete_qml(test_content, "TestScene")
    if complete_qml:
        print("✅ 成功组装完整QML")
        print(f"  📊 完整QML长度: {len(complete_qml)} 字符")
        print("  📄 生成的完整QML片段:")
        print("  " + complete_qml[:300] + "..." if len(complete_qml) > 300 else "  " + complete_qml)
        
        # 保存测试QML文件
        print("\n4. 保存测试QML文件...")
        test_output_path = os.path.join(os.path.dirname(__file__), "test_output.qml")
        try:
            with open(test_output_path, 'w', encoding='utf-8') as f:
                f.write(complete_qml)
            print(f"✅ 测试QML文件已保存到: {test_output_path}")
        except Exception as e:
            print(f"❌ 保存测试QML文件失败: {e}")
    else:
        print("❌ 组装完整QML失败")
        return
    
    print("\n🎉 场景属性集成测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_qml_handler()
    print("\n")
    test_scene_properties_integration()
