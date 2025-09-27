#!/usr/bin/env python3
"""
SceneEnvironment设置模块 - 管理Qt Quick3D的SceneEnvironment和ExtendedSceneEnvironment设置
负责注册、管理和转换场景环境相关的属性
"""

import bpy
from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, BoolProperty, StringProperty
from typing import Dict, Any


class SceneEnvironmentManager:
    """SceneEnvironment设置管理器"""
    
    def __init__(self):
        self.registered_properties = set()
    
    def register_all_properties(self):
        """注册所有SceneEnvironment相关属性"""
        self.register_ui_properties()
        self.register_basic_properties()
        self.register_extended_properties()
        self.register_wasd_controller_properties()
    
    def register_ui_properties(self):
        """注册UI相关属性"""
        bpy.types.Scene.show_scene_settings = BoolProperty(
            name="Show Scene Settings",
            description="Show/hide scene settings panel",
            default=False
        )
        self.registered_properties.add('show_scene_settings')
        
        bpy.types.Scene.show_debug_options = BoolProperty(
            name="Show Debug Options",
            description="Show/hide debug options panel",
            default=False
        )
        self.registered_properties.add('show_debug_options')
        
        # View3D尺寸设置
        bpy.types.Scene.qtquick3d_view3d_width = IntProperty(
            name="View3D Width",
            description="View3D window width",
            default=800,
            min=100,
            max=4096
        )
        self.registered_properties.add('qtquick3d_view3d_width')
        
        bpy.types.Scene.qtquick3d_view3d_height = IntProperty(
            name="View3D Height",
            description="View3D window height",
            default=600,
            min=100,
            max=4096
        )
        self.registered_properties.add('qtquick3d_view3d_height')
        
        # 缺失的基础属性
        bpy.types.Scene.qtquick3d_antialiasing_mode = IntProperty(
            name="AA Mode",
            description="Anti-aliasing mode",
            default=0,
            min=0,
            max=2
        )
        self.registered_properties.add('qtquick3d_antialiasing_mode')
        
        bpy.types.Scene.qtquick3d_antialiasing_quality = IntProperty(
            name="AA Quality",
            description="Anti-aliasing quality",
            default=1,
            min=0,
            max=3
        )
        self.registered_properties.add('qtquick3d_antialiasing_quality')
        
        bpy.types.Scene.qtquick3d_ao_strength = FloatProperty(
            name="AO Strength",
            description="Ambient occlusion strength",
            default=1.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_ao_strength')
        
        bpy.types.Scene.qtquick3d_background_mode = IntProperty(
            name="Background Mode",
            description="Background rendering mode",
            default=0,
            min=0,
            max=2
        )
        self.registered_properties.add('qtquick3d_background_mode')
        
        bpy.types.Scene.qtquick3d_clear_color = FloatVectorProperty(
            name="Clear Color",
            description="Background clear color",
            default=(0.0, 0.0, 0.0, 1.0),
            size=4,
            subtype='COLOR'
        )
        self.registered_properties.add('qtquick3d_clear_color')
        
        bpy.types.Scene.qtquick3d_scissor_enabled = BoolProperty(
            name="Scissor Enabled",
            description="Enable scissor testing",
            default=False
        )
        self.registered_properties.add('qtquick3d_scissor_enabled')
        
        bpy.types.Scene.qtquick3d_scissor_rect = FloatVectorProperty(
            name="Scissor Rect",
            description="Scissor rectangle",
            default=(0.0, 0.0, 1.0, 1.0),
            size=4
        )
        self.registered_properties.add('qtquick3d_scissor_rect')
        
        bpy.types.Scene.qtquick3d_probe_exposure = FloatProperty(
            name="Probe Exposure",
            description="Light probe exposure",
            default=0.0,
            min=-10.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_probe_exposure')
        
        bpy.types.Scene.qtquick3d_probe_horizon = FloatProperty(
            name="Probe Horizon",
            description="Light probe horizon cutoff",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_probe_horizon')
        
        bpy.types.Scene.qtquick3d_probe_orientation = FloatVectorProperty(
            name="Probe Orientation",
            description="Light probe orientation",
            default=(0.0, 0.0, 0.0),
            size=3,
            subtype='EULER'
        )
        self.registered_properties.add('qtquick3d_probe_orientation')
        
        # Skybox设置
        bpy.types.Scene.qtquick3d_skybox_cubemap = StringProperty(
            name="Skybox Cubemap",
            description="Skybox cubemap texture path",
            default=""
        )
        self.registered_properties.add('qtquick3d_skybox_cubemap')
        
        bpy.types.Scene.qtquick3d_skybox_blur_amount = FloatProperty(
            name="Skybox Blur Amount",
            description="Skybox blur amount",
            default=0.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_skybox_blur_amount')
        
        # Light probe和lightmapper
        bpy.types.Scene.qtquick3d_light_probe = StringProperty(
            name="Light Probe",
            description="Light probe texture path",
            default=""
        )
        self.registered_properties.add('qtquick3d_light_probe')
        
        bpy.types.Scene.qtquick3d_lightmapper = IntProperty(
            name="Lightmapper",
            description="Lightmapper type",
            default=0,
            min=0,
            max=2
        )
        self.registered_properties.add('qtquick3d_lightmapper')
        
        # Fog设置
        bpy.types.Scene.qtquick3d_fog = StringProperty(
            name="Fog",
            description="Fog settings",
            default=""
        )
        self.registered_properties.add('qtquick3d_fog')
        
        # Debug和Effects设置
        bpy.types.Scene.qtquick3d_debug_settings = StringProperty(
            name="Debug Settings",
            description="Debug settings",
            default=""
        )
        self.registered_properties.add('qtquick3d_debug_settings')
        
        bpy.types.Scene.qtquick3d_effects = StringProperty(
            name="Effects",
            description="Effects settings",
            default=""
        )
        self.registered_properties.add('qtquick3d_effects')
        
        bpy.types.Scene.qtquick3d_oit_method = IntProperty(
            name="OIT Method",
            description="Order independent transparency method",
            default=0,
            min=0,
            max=2
        )
        self.registered_properties.add('qtquick3d_oit_method')
        
        bpy.types.Scene.qtquick3d_use_extended_environment = BoolProperty(
            name="Use Extended Environment",
            description="Use ExtendedSceneEnvironment",
            default=False
        )
        self.registered_properties.add('qtquick3d_use_extended_environment')
    
    def register_basic_properties(self):
        """注册基础SceneEnvironment属性"""
        
        # 环境光遮蔽
        bpy.types.Scene.qtquick3d_ao_enabled = BoolProperty(
            name="AO Enabled",
            description="Enable ambient occlusion",
            default=False
        )
        self.registered_properties.add('qtquick3d_ao_enabled')
        
        bpy.types.Scene.qtquick3d_ao_bias = FloatProperty(
            name="AO Bias",
            description="Ambient occlusion bias",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_ao_bias')
        
        bpy.types.Scene.qtquick3d_ao_distance = FloatProperty(
            name="AO Distance",
            description="Ambient occlusion distance",
            default=5.0,
            min=0.1,
            max=100.0
        )
        self.registered_properties.add('qtquick3d_ao_distance')
        
        bpy.types.Scene.qtquick3d_ao_dither = BoolProperty(
            name="AO Dither",
            description="Ambient occlusion dithering",
            default=False
        )
        self.registered_properties.add('qtquick3d_ao_dither')
        
        bpy.types.Scene.qtquick3d_ao_sample_rate = IntProperty(
            name="AO Sample Rate",
            description="Ambient occlusion sample rate",
            default=2,
            min=1,
            max=8
        )
        self.registered_properties.add('qtquick3d_ao_sample_rate')
        
        bpy.types.Scene.qtquick3d_ao_softness = FloatProperty(
            name="AO Softness",
            description="Ambient occlusion softness",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_ao_softness')
        
        # 深度设置
        bpy.types.Scene.qtquick3d_depth_prepass_enabled = BoolProperty(
            name="Depth PrePass",
            description="Enable depth prepass",
            default=False
        )
        self.registered_properties.add('qtquick3d_depth_prepass_enabled')
        
        bpy.types.Scene.qtquick3d_depth_test_enabled = BoolProperty(
            name="Depth Test",
            description="Enable depth testing",
            default=True
        )
        self.registered_properties.add('qtquick3d_depth_test_enabled')
        
        # 抗锯齿设置
        bpy.types.Scene.qtquick3d_aa_mode = IntProperty(
            name="AA Mode",
            description="Anti-aliasing mode",
            default=0,
            min=0,
            max=2
        )
        self.registered_properties.add('qtquick3d_aa_mode')
        
        bpy.types.Scene.qtquick3d_aa_quality = IntProperty(
            name="AA Quality",
            description="Anti-aliasing quality",
            default=1,
            min=0,
            max=3
        )
        self.registered_properties.add('qtquick3d_aa_quality')
        
        bpy.types.Scene.qtquick3d_aa_sample_count = IntProperty(
            name="AA Sample Count",
            description="Anti-aliasing sample count",
            default=4,
            min=1,
            max=16
        )
        self.registered_properties.add('qtquick3d_aa_sample_count')
        
        bpy.types.Scene.qtquick3d_aa_transparent_enabled = BoolProperty(
            name="AA Transparent",
            description="Enable transparent anti-aliasing",
            default=False
        )
        self.registered_properties.add('qtquick3d_aa_transparent_enabled')
        
        bpy.types.Scene.qtquick3d_specular_aa_enabled = BoolProperty(
            name="Specular AA",
            description="Enable specular anti-aliasing",
            default=False
        )
        self.registered_properties.add('qtquick3d_specular_aa_enabled')
        
        bpy.types.Scene.qtquick3d_temporal_aa_enabled = BoolProperty(
            name="Temporal AA",
            description="Enable temporal anti-aliasing",
            default=False
        )
        self.registered_properties.add('qtquick3d_temporal_aa_enabled')
        
        bpy.types.Scene.qtquick3d_temporal_aa_strength = FloatProperty(
            name="Temporal AA Strength",
            description="Temporal anti-aliasing strength",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_temporal_aa_strength')
        
        bpy.types.Scene.qtquick3d_temporal_aa_velocity_scale = FloatProperty(
            name="Temporal AA Velocity Scale",
            description="Temporal anti-aliasing velocity scale",
            default=1.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_temporal_aa_velocity_scale')
        
        # 色调映射
        bpy.types.Scene.qtquick3d_tonemap_mode = IntProperty(
            name="Tonemap Mode",
            description="Tone mapping mode",
            default=0,
            min=0,
            max=2
        )
        self.registered_properties.add('qtquick3d_tonemap_mode')
        
        bpy.types.Scene.qtquick3d_exposure = FloatProperty(
            name="Exposure",
            description="Scene exposure",
            default=0.0,
            min=-5.0,
            max=5.0
        )
        self.registered_properties.add('qtquick3d_exposure')
        
        bpy.types.Scene.qtquick3d_sharpness = FloatProperty(
            name="Sharpness",
            description="Image sharpness",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_sharpness')
        
        bpy.types.Scene.qtquick3d_white_point = FloatProperty(
            name="White Point",
            description="White point value",
            default=1.0,
            min=0.1,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_white_point')
    
    def register_extended_properties(self):
        """注册ExtendedSceneEnvironment属性"""
        
        # 景深效果
        bpy.types.Scene.qtquick3d_dof_enabled = BoolProperty(
            name="Enable Depth of Field",
            description="Enable depth of field effect",
            default=False
        )
        self.registered_properties.add('qtquick3d_dof_enabled')
        
        bpy.types.Scene.qtquick3d_dof_blur_amount = FloatProperty(
            name="DOF Blur Amount",
            description="Depth of field blur amount",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_dof_blur_amount')
        
        bpy.types.Scene.qtquick3d_dof_focus_distance = FloatProperty(
            name="DOF Focus Distance",
            description="Depth of field focus distance",
            default=100.0,
            min=0.1,
            max=1000.0
        )
        self.registered_properties.add('qtquick3d_dof_focus_distance')
        
        bpy.types.Scene.qtquick3d_dof_focus_range = FloatProperty(
            name="DOF Focus Range",
            description="Depth of field focus range",
            default=10.0,
            min=0.1,
            max=100.0
        )
        self.registered_properties.add('qtquick3d_dof_focus_range')
        
        # 发光效果
        bpy.types.Scene.qtquick3d_glow_enabled = BoolProperty(
            name="Enable Glow",
            description="Enable glow effect",
            default=False
        )
        self.registered_properties.add('qtquick3d_glow_enabled')
        
        bpy.types.Scene.qtquick3d_glow_intensity = FloatProperty(
            name="Glow Intensity",
            description="Glow effect intensity",
            default=0.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_glow_intensity')
        
        bpy.types.Scene.qtquick3d_glow_bloom = FloatProperty(
            name="Glow Bloom",
            description="Glow bloom amount",
            default=0.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_glow_bloom')
        
        bpy.types.Scene.qtquick3d_glow_blend_factor = FloatProperty(
            name="Glow Blend Factor",
            description="Glow blend factor",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_glow_blend_factor')
        
        bpy.types.Scene.qtquick3d_glow_blend_mode = IntProperty(
            name="Glow Blend Mode",
            description="Glow blend mode",
            default=0,
            min=0,
            max=3
        )
        self.registered_properties.add('qtquick3d_glow_blend_mode')
        
        bpy.types.Scene.qtquick3d_glow_level = IntProperty(
            name="Glow Level",
            description="Glow level",
            default=0,
            min=0,
            max=10
        )
        self.registered_properties.add('qtquick3d_glow_level')
        
        bpy.types.Scene.qtquick3d_glow_hdr_maximum_value = FloatProperty(
            name="Glow HDR Max",
            description="Glow HDR maximum value",
            default=1.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_glow_hdr_maximum_value')
        
        bpy.types.Scene.qtquick3d_glow_hdr_minimum_value = FloatProperty(
            name="Glow HDR Min",
            description="Glow HDR minimum value",
            default=0.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_glow_hdr_minimum_value')
        
        bpy.types.Scene.qtquick3d_glow_hdr_scale = FloatProperty(
            name="Glow HDR Scale",
            description="Glow HDR scale",
            default=1.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_glow_hdr_scale')
        
        # 镜头光晕
        bpy.types.Scene.qtquick3d_lens_flare_enabled = BoolProperty(
            name="Enable Lens Flare",
            description="Enable lens flare effect",
            default=False
        )
        self.registered_properties.add('qtquick3d_lens_flare_enabled')
        
        bpy.types.Scene.qtquick3d_lens_flare_apply_dirt_texture = BoolProperty(
            name="Apply Dirt Texture",
            description="Apply dirt texture to lens flare",
            default=False
        )
        self.registered_properties.add('qtquick3d_lens_flare_apply_dirt_texture')
        
        bpy.types.Scene.qtquick3d_lens_flare_apply_starburst_texture = BoolProperty(
            name="Apply Starburst Texture",
            description="Apply starburst texture to lens flare",
            default=False
        )
        self.registered_properties.add('qtquick3d_lens_flare_apply_starburst_texture')
        
        bpy.types.Scene.qtquick3d_lens_flare_bloom_scale = FloatProperty(
            name="Bloom Scale",
            description="Lens flare bloom scale",
            default=0.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_bloom_scale')
        
        bpy.types.Scene.qtquick3d_lens_flare_brightness = FloatProperty(
            name="Brightness",
            description="Lens flare brightness",
            default=1.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_brightness')
        
        bpy.types.Scene.qtquick3d_lens_flare_lens_color_texture = StringProperty(
            name="Color Texture",
            description="Lens flare color texture",
            default="",
            subtype='FILE_PATH'
        )
        self.registered_properties.add('qtquick3d_lens_flare_lens_color_texture')
        
        bpy.types.Scene.qtquick3d_lens_flare_lens_dirt_texture = StringProperty(
            name="Dirt Texture",
            description="Lens flare dirt texture",
            default="",
            subtype='FILE_PATH'
        )
        self.registered_properties.add('qtquick3d_lens_flare_lens_dirt_texture')
        
        bpy.types.Scene.qtquick3d_lens_flare_lens_starburst_texture = StringProperty(
            name="Starburst Texture",
            description="Lens flare starburst texture",
            default="",
            subtype='FILE_PATH'
        )
        self.registered_properties.add('qtquick3d_lens_flare_lens_starburst_texture')
        
        bpy.types.Scene.qtquick3d_lens_flare_stretch_to_aspect = FloatProperty(
            name="Stretch To Aspect",
            description="Lens flare stretch to aspect ratio",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_stretch_to_aspect')
        
        bpy.types.Scene.qtquick3d_lens_flare_bloom_bias = FloatProperty(
            name="Lens Flare Bloom Bias",
            description="Lens flare bloom bias",
            default=0.0,
            min=-1.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_bloom_bias')
        
        bpy.types.Scene.qtquick3d_lens_flare_camera_direction = FloatVectorProperty(
            name="Lens Flare Camera Direction",
            description="Lens flare camera direction",
            default=(0.0, 0.0, 1.0),
            size=3,
            subtype='DIRECTION'
        )
        self.registered_properties.add('qtquick3d_lens_flare_camera_direction')
        
        bpy.types.Scene.qtquick3d_lens_flare_distortion = FloatProperty(
            name="Lens Flare Distortion",
            description="Lens flare distortion",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_distortion')
        
        bpy.types.Scene.qtquick3d_lens_flare_halo_width = FloatProperty(
            name="Lens Flare Halo Width",
            description="Lens flare halo width",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_halo_width')
        
        # LUT设置
        bpy.types.Scene.qtquick3d_lut_enabled = BoolProperty(
            name="Enable LUT",
            description="Enable lookup table",
            default=False
        )
        self.registered_properties.add('qtquick3d_lut_enabled')
        
        bpy.types.Scene.qtquick3d_lut_filter_alpha = FloatProperty(
            name="LUT Filter Alpha",
            description="LUT filter alpha value",
            default=1.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_lut_filter_alpha')
        
        bpy.types.Scene.qtquick3d_lut_size = FloatProperty(
            name="LUT Size",
            description="LUT size",
            default=32.0,
            min=16.0,
            max=64.0
        )
        self.registered_properties.add('qtquick3d_lut_size')
        
        bpy.types.Scene.qtquick3d_lut_texture = StringProperty(
            name="LUT Texture",
            description="LUT texture file",
            default="",
            subtype='FILE_PATH'
        )
        self.registered_properties.add('qtquick3d_lut_texture')
        
        # 暗角设置
        bpy.types.Scene.qtquick3d_vignette_enabled = BoolProperty(
            name="Enable Vignette",
            description="Enable vignette effect",
            default=False
        )
        self.registered_properties.add('qtquick3d_vignette_enabled')
        
        bpy.types.Scene.qtquick3d_vignette_strength = FloatProperty(
            name="Vignette Strength",
            description="Vignette effect strength",
            default=0.0,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_vignette_strength')
        
        bpy.types.Scene.qtquick3d_vignette_radius = FloatProperty(
            name="Vignette Radius",
            description="Vignette effect radius",
            default=0.5,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_vignette_radius')
        
        bpy.types.Scene.qtquick3d_vignette_color = FloatVectorProperty(
            name="Vignette Color",
            description="Vignette effect color",
            default=(0.0, 0.0, 0.0, 1.0),
            size=4,
            subtype='COLOR'
        )
        self.registered_properties.add('qtquick3d_vignette_color')
        
        # 其他效果
        bpy.types.Scene.qtquick3d_color_adjustments_enabled = BoolProperty(
            name="Enable Color Adjustments",
            description="Enable color adjustments",
            default=False
        )
        self.registered_properties.add('qtquick3d_color_adjustments_enabled')
        
        bpy.types.Scene.qtquick3d_dithering_enabled = BoolProperty(
            name="Enable Dithering",
            description="Enable dithering",
            default=False
        )
        self.registered_properties.add('qtquick3d_dithering_enabled')
        
        bpy.types.Scene.qtquick3d_fxaa_enabled = BoolProperty(
            name="Enable FXAA",
            description="Enable FXAA anti-aliasing",
            default=False
        )
        self.registered_properties.add('qtquick3d_fxaa_enabled')
        
        # 颜色调整属性
        bpy.types.Scene.qtquick3d_brightness = FloatProperty(
            name="Brightness",
            description="Image brightness adjustment",
            default=0.0,
            min=-1.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_brightness')
        
        bpy.types.Scene.qtquick3d_contrast = FloatProperty(
            name="Contrast",
            description="Image contrast adjustment",
            default=1.0,
            min=0.0,
            max=3.0
        )
        self.registered_properties.add('qtquick3d_contrast')
        
        bpy.types.Scene.qtquick3d_saturation = FloatProperty(
            name="Saturation",
            description="Image saturation adjustment",
            default=1.0,
            min=0.0,
            max=3.0
        )
        self.registered_properties.add('qtquick3d_saturation')
        
        # 发光效果缺失属性
        bpy.types.Scene.qtquick3d_glow_strength = FloatProperty(
            name="Glow Strength",
            description="Glow effect strength",
            default=1.0,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_glow_strength')
        
        bpy.types.Scene.qtquick3d_glow_quality_high = BoolProperty(
            name="Glow High Quality",
            description="Enable high quality glow",
            default=False
        )
        self.registered_properties.add('qtquick3d_glow_quality_high')
        
        bpy.types.Scene.qtquick3d_glow_use_bicubic_upscale = BoolProperty(
            name="Glow Bicubic Upscale",
            description="Use bicubic upscaling for glow",
            default=False
        )
        self.registered_properties.add('qtquick3d_glow_use_bicubic_upscale')
        
        # 镜头光晕缺失属性
        bpy.types.Scene.qtquick3d_lens_flare_ghost_count = IntProperty(
            name="Ghost Count",
            description="Lens flare ghost count",
            default=4,
            min=0,
            max=20
        )
        self.registered_properties.add('qtquick3d_lens_flare_ghost_count')
        
        bpy.types.Scene.qtquick3d_lens_flare_ghost_dispersal = FloatProperty(
            name="Ghost Dispersal",
            description="Lens flare ghost dispersal",
            default=0.2,
            min=0.0,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_ghost_dispersal')
        
        bpy.types.Scene.qtquick3d_lens_flare_blur_amount = FloatProperty(
            name="Blur Amount",
            description="Lens flare blur amount",
            default=0.5,
            min=0.0,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_lens_flare_blur_amount')
    
    def register_wasd_controller_properties(self):
        """注册WASD控制器相关属性"""
        
        # WASD控制器开关
        bpy.types.Scene.qtquick3d_wasd_enabled = BoolProperty(
            name="WASD Enabled",
            description="Enable WASD controller",
            default=False
        )
        self.registered_properties.add('qtquick3d_wasd_enabled')
        
        # 移动速度设置
        bpy.types.Scene.qtquick3d_wasd_forward_speed = FloatProperty(
            name="Forward Speed",
            description="Forward movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_forward_speed')
        
        # 添加缺失的官方属性
        bpy.types.Scene.qtquick3d_wasd_controlled_object = StringProperty(
            name="Controlled Object",
            description="Object to be controlled by WASD",
            default=""
        )
        self.registered_properties.add('qtquick3d_wasd_controlled_object')
        
        bpy.types.Scene.qtquick3d_wasd_inputs_need_processing = BoolProperty(
            name="Inputs Need Processing",
            description="Whether inputs need processing",
            default=True
        )
        self.registered_properties.add('qtquick3d_wasd_inputs_need_processing')
        
        bpy.types.Scene.qtquick3d_wasd_left_speed = FloatProperty(
            name="Left Speed",
            description="Left movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_left_speed')
        
        bpy.types.Scene.qtquick3d_wasd_right_speed = FloatProperty(
            name="Right Speed",
            description="Right movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_right_speed')
        
        bpy.types.Scene.qtquick3d_wasd_up_speed = FloatProperty(
            name="Up Speed",
            description="Up movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_up_speed')
        
        bpy.types.Scene.qtquick3d_wasd_down_speed = FloatProperty(
            name="Down Speed",
            description="Down movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_down_speed')
        
        bpy.types.Scene.qtquick3d_wasd_shift_speed = FloatProperty(
            name="Shift Speed",
            description="Shift movement speed",
            default=3.0,
            min=0.1,
            max=10.0
        )
        self.registered_properties.add('qtquick3d_wasd_shift_speed')
        
        # 鼠标控制设置
        bpy.types.Scene.qtquick3d_wasd_mouse_enabled = BoolProperty(
            name="Mouse Enabled",
            description="Enable mouse controls",
            default=True
        )
        self.registered_properties.add('qtquick3d_wasd_mouse_enabled')
        
        bpy.types.Scene.qtquick3d_wasd_x_speed = FloatProperty(
            name="X Speed",
            description="Mouse X axis speed",
            default=0.1,
            min=0.01,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_wasd_x_speed')
        
        bpy.types.Scene.qtquick3d_wasd_y_speed = FloatProperty(
            name="Y Speed",
            description="Mouse Y axis speed",
            default=0.1,
            min=0.01,
            max=1.0
        )
        self.registered_properties.add('qtquick3d_wasd_y_speed')
        
        bpy.types.Scene.qtquick3d_wasd_x_invert = BoolProperty(
            name="X Invert",
            description="Invert X axis",
            default=False
        )
        self.registered_properties.add('qtquick3d_wasd_x_invert')
        
        bpy.types.Scene.qtquick3d_wasd_y_invert = BoolProperty(
            name="Y Invert",
            description="Invert Y axis",
            default=True
        )
        self.registered_properties.add('qtquick3d_wasd_y_invert')
        
        # 键盘控制设置
        bpy.types.Scene.qtquick3d_wasd_keys_enabled = BoolProperty(
            name="Keys Enabled",
            description="Enable key controls",
            default=True
        )
        self.registered_properties.add('qtquick3d_wasd_keys_enabled')
        
        # WASD控制器缺失属性
        bpy.types.Scene.qtquick3d_wasd_speed = FloatProperty(
            name="Base Speed",
            description="Base movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_speed')
        
        bpy.types.Scene.qtquick3d_wasd_back_speed = FloatProperty(
            name="Back Speed",
            description="Backward movement speed",
            default=5.0,
            min=0.1,
            max=50.0
        )
        self.registered_properties.add('qtquick3d_wasd_back_speed')
        
        bpy.types.Scene.qtquick3d_wasd_accepted_buttons = IntProperty(
            name="Accepted Buttons",
            description="Accepted mouse buttons",
            default=1,
            min=0,
            max=7
        )
        self.registered_properties.add('qtquick3d_wasd_accepted_buttons')
    
    def unregister_all_properties(self):
        """注销所有已注册的属性"""
        for prop_name in self.registered_properties:
            if hasattr(bpy.types.Scene, prop_name):
                delattr(bpy.types.Scene, prop_name)
        self.registered_properties.clear()
    
    def get_scene_environment_settings(self) -> Dict[str, Any]:
        """获取当前场景的环境设置"""
        scene = bpy.context.scene
        settings = {}
        
        # 属性名映射：从Blender属性名到QML处理器期望的属性名
        property_mapping = {
            # View3D基础设置
            'qtquick3d_view3d_width': 'view3d_width',
            'qtquick3d_view3d_height': 'view3d_height',
            'qtquick3d_scissor_rect': 'scissor_rect',
            'qtquick3d_scissor_enabled': 'scissor_enabled',
            
            # 抗锯齿设置
            'qtquick3d_antialiasing_mode': 'antialiasing_mode',
            'qtquick3d_antialiasing_quality': 'antialiasing_quality',
            'qtquick3d_specular_aa_enabled': 'specular_aa_enabled',
            'qtquick3d_temporal_aa_enabled': 'temporal_aa_enabled',
            'qtquick3d_temporal_aa_strength': 'temporal_aa_strength',
            'qtquick3d_temporal_aa_velocity_scale': 'temporal_aa_velocity_scale',
            'qtquick3d_fxaa_enabled': 'fxaa_enabled',
            
            # AO设置
            'qtquick3d_ao_enabled': 'ao_enabled',
            'qtquick3d_ao_strength': 'ao_strength',
            'qtquick3d_ao_bias': 'ao_bias',
            'qtquick3d_ao_distance': 'ao_distance',
            'qtquick3d_ao_dither': 'ao_dither',
            'qtquick3d_ao_sample_rate': 'ao_sample_rate',
            'qtquick3d_ao_softness': 'ao_softness',
            
            # 背景和环境设置
            'qtquick3d_background_mode': 'background_mode',
            'qtquick3d_clear_color': 'clear_color',
            'qtquick3d_probe_exposure': 'probe_exposure',
            'qtquick3d_probe_horizon': 'probe_horizon',
            'qtquick3d_probe_orientation': 'probe_orientation',
            'qtquick3d_skybox_cubemap': 'skybox_cubemap',
            'qtquick3d_skybox_blur_amount': 'skybox_blur_amount',
            'qtquick3d_light_probe': 'light_probe',
            'qtquick3d_lightmapper': 'lightmapper',
            
            # 深度和渲染设置
            'qtquick3d_depth_test_enabled': 'depth_test_enabled',
            'qtquick3d_depth_prepass_enabled': 'depth_prepass_enabled',
            'qtquick3d_oit_method': 'oit_method',
            'qtquick3d_dithering_enabled': 'dithering_enabled',
            
            # 色调映射
            'qtquick3d_tonemap_mode': 'tonemap_mode',
            
            # 扩展环境设置
            'qtquick3d_use_extended_environment': 'use_extended_environment',
            'qtquick3d_color_adjustments_enabled': 'color_adjustments_enabled',
            'qtquick3d_brightness': 'brightness',
            'qtquick3d_contrast': 'contrast',
            'qtquick3d_saturation': 'saturation',
            'qtquick3d_exposure': 'exposure',
            'qtquick3d_sharpness': 'sharpness',
            'qtquick3d_white_point': 'white_point',
            
            # DOF设置
            'qtquick3d_dof_enabled': 'dof_enabled',
            'qtquick3d_dof_blur_amount': 'dof_blur_amount',
            'qtquick3d_dof_focus_distance': 'dof_focus_distance',
            'qtquick3d_dof_focus_range': 'dof_focus_range',
            
            # 发光设置
            'qtquick3d_glow_enabled': 'glow_enabled',
            'qtquick3d_glow_strength': 'glow_strength',
            'qtquick3d_glow_bloom': 'glow_bloom',
            'qtquick3d_glow_intensity': 'glow_intensity',
            'qtquick3d_glow_blend_mode': 'glow_blend_mode',
            'qtquick3d_glow_hdr_maximum_value': 'glow_hdr_maximum_value',
            'qtquick3d_glow_hdr_minimum_value': 'glow_hdr_minimum_value',
            'qtquick3d_glow_hdr_scale': 'glow_hdr_scale',
            'qtquick3d_glow_level': 'glow_level',
            'qtquick3d_glow_quality_high': 'glow_quality_high',
            'qtquick3d_glow_use_bicubic_upscale': 'glow_use_bicubic_upscale',
            
            # 镜头光晕设置
            'qtquick3d_lens_flare_enabled': 'lens_flare_enabled',
            'qtquick3d_lens_flare_apply_dirt_texture': 'lens_flare_apply_dirt_texture',
            'qtquick3d_lens_flare_apply_starburst_texture': 'lens_flare_apply_starburst_texture',
            'qtquick3d_lens_flare_bloom_bias': 'lens_flare_bloom_bias',
            'qtquick3d_lens_flare_bloom_scale': 'lens_flare_bloom_scale',
            'qtquick3d_lens_flare_blur_amount': 'lens_flare_blur_amount',
            'qtquick3d_lens_flare_camera_direction': 'lens_flare_camera_direction',
            'qtquick3d_lens_flare_distortion': 'lens_flare_distortion',
            'qtquick3d_lens_flare_ghost_count': 'lens_flare_ghost_count',
            'qtquick3d_lens_flare_ghost_dispersal': 'lens_flare_ghost_dispersal',
            'qtquick3d_lens_flare_halo_width': 'lens_flare_halo_width',
            'qtquick3d_lens_flare_lens_color_texture': 'lens_flare_lens_color_texture',
            'qtquick3d_lens_flare_lens_dirt_texture': 'lens_flare_lens_dirt_texture',
            'qtquick3d_lens_flare_lens_starburst_texture': 'lens_flare_lens_starburst_texture',
            'qtquick3d_lens_flare_stretch_to_aspect': 'lens_flare_stretch_to_aspect',
            
            # LUT设置
            'qtquick3d_lut_enabled': 'lut_enabled',
            'qtquick3d_lut_filter_alpha': 'lut_filter_alpha',
            'qtquick3d_lut_size': 'lut_size',
            'qtquick3d_lut_texture': 'lut_texture',
            
            # 暗角设置
            'qtquick3d_vignette_enabled': 'vignette_enabled',
            'qtquick3d_vignette_color': 'vignette_color',
            'qtquick3d_vignette_radius': 'vignette_radius',
            'qtquick3d_vignette_strength': 'vignette_strength',
            
            # WASD控制器设置（官方属性，映射到下划线命名法以匹配qml_handler.py）
            'qtquick3d_wasd_accepted_buttons': 'wasd_accepted_buttons',
            'qtquick3d_wasd_back_speed': 'wasd_back_speed',
            'qtquick3d_wasd_controlled_object': 'wasd_controlled_object',
            'qtquick3d_wasd_down_speed': 'wasd_down_speed',
            'qtquick3d_wasd_forward_speed': 'wasd_forward_speed',
            'qtquick3d_wasd_inputs_need_processing': 'wasd_inputs_need_processing',
            'qtquick3d_wasd_keys_enabled': 'wasd_keys_enabled',
            'qtquick3d_wasd_left_speed': 'wasd_left_speed',
            'qtquick3d_wasd_mouse_enabled': 'wasd_mouse_enabled',
            'qtquick3d_wasd_right_speed': 'wasd_right_speed',
            'qtquick3d_wasd_shift_speed': 'wasd_shift_speed',
            'qtquick3d_wasd_speed': 'wasd_speed',
            'qtquick3d_wasd_up_speed': 'wasd_up_speed',
            'qtquick3d_wasd_x_invert': 'wasd_x_invert',
            'qtquick3d_wasd_x_speed': 'wasd_x_speed',
            'qtquick3d_wasd_y_invert': 'wasd_y_invert',
            'qtquick3d_wasd_y_speed': 'wasd_y_speed',
            
            # 自定义WASD设置（非官方）
            'qtquick3d_wasd_enabled': 'wasd_enabled',
            
            # 其他设置
            'qtquick3d_fog': 'fog',
            'qtquick3d_debug_settings': 'debug_settings',
            'qtquick3d_effects': 'effects',
        }
        
        for prop_name in self.registered_properties:
            if hasattr(scene, prop_name):
                value = getattr(scene, prop_name)
                # 处理向量属性
                if isinstance(value, (tuple, list)):
                    settings[property_mapping.get(prop_name, prop_name)] = list(value)
                else:
                    settings[property_mapping.get(prop_name, prop_name)] = value
        
        return settings


# 全局管理器实例
_scene_environment_manager = None


def get_scene_environment_manager() -> SceneEnvironmentManager:
    """获取场景环境管理器单例"""
    global _scene_environment_manager
    if _scene_environment_manager is None:
        _scene_environment_manager = SceneEnvironmentManager()
    return _scene_environment_manager


def register_scene_environment_properties():
    """注册SceneEnvironment相关属性"""
    get_scene_environment_manager().register_all_properties()


def unregister_scene_environment_properties():
    """注销SceneEnvironment相关属性"""
    global _scene_environment_manager
    if _scene_environment_manager is not None:
        _scene_environment_manager.unregister_all_properties()
        _scene_environment_manager = None


def get_scene_environment_settings() -> Dict[str, Any]:
    """获取当前场景的环境设置（模块级别函数）"""
    try:
        # 使用SceneEnvironmentManager获取设置
        manager = get_scene_environment_manager()
        return manager.get_scene_environment_settings()
    except Exception as e:
        print(f"❌ 获取场景环境设置失败: {e}")
        return {}