"""
Blender Render Engine Registration for Qt Quick3D
This module registers the Qt Quick3D engine as a Blender render engine
"""

import bpy
from bpy.types import RenderEngine, Operator
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty
)

# 导入我们的Quick3D引擎
try:
    from . import qt_quick3d_integration_pyside6 as qt_quick3d_integration
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    print("Warning: Qt Quick3D integration not available")

class Quick3DRenderEngine(RenderEngine):
    """Qt Quick3D渲染引擎"""
    
    bl_idname = "QUICK3D"
    bl_label = "Qt Quick3D"
    bl_use_preview = True
    bl_use_shading_nodes = True  # 启用Blender默认材质节点系统
    bl_use_shading_nodes_custom = False  # 禁用自定义材质节点，使用Blender默认
    bl_use_material_nodes = True  # 启用材质节点
    bl_use_texture_nodes = True   # 启用纹理节点
    bl_use_light_nodes = True     # 启用灯光节点
    
    def __init__(self):
        super().__init__()
        self.engine = None
        if ENGINE_AVAILABLE:
            # 使用集成模块中的功能
            self.engine = qt_quick3d_integration
    
    def render(self, depsgraph):
        """执行渲染"""
        if not ENGINE_AVAILABLE or not self.engine:
            self.report({'ERROR'}, "Qt Quick3D engine not available")
            return
        
        try:
            # 获取场景上下文
            scene = depsgraph.scene
            context = bpy.context
            props = scene.quick3d_properties
            
            # 设置渲染参数
            # 注意：render_settings 功能已集成到 export_blender_scene_to_qml 中
            
            # 根据输出格式选择渲染方式
            if props.output_format == 'QML':
                # 导出QML场景
                output_path = bpy.path.abspath(props.qml_output_path)
                success = self.engine.export_blender_scene_to_qml(context, output_path)
                
                if success:
                    self.report({'INFO'}, f"QML scene exported to: {output_path}")
                else:
                    self.report({'ERROR'}, "Failed to export QML scene")
            else:
                # 执行图像渲染
                success = self._render_image(depsgraph)
                
                if success:
                    self.report({'INFO'}, "Render completed successfully")
                else:
                    self.report({'ERROR'}, "Render failed")
                    
        except Exception as e:
            self.report({'ERROR'}, f"Render error: {str(e)}")
    
    def _render_image(self, depsgraph):
        #目前不可用
        """渲染图像"""
        try:
            # 获取渲染设置
            scene = depsgraph.scene
            render = scene.render
            
            # 获取输出路径
            output_path = bpy.path.abspath(render.filepath)
            
            # 这里应该调用Qt Quick3D进行实际渲染
            # 由于Qt Quick3D主要用于实时渲染，这里我们生成一个预览图像
            
            # 生成QML文件路径
            qml_path = output_path.replace('.png', '.qml').replace('.jpg', '.qml')
            
            # 导出场景数据到QML
            context = bpy.context
            success = self.engine.export_blender_scene_to_qml(context, qml_path)
            
            if success:
                print(f"Scene exported to QML: {qml_path}")
                print("Note: Image rendering requires Qt Quick3D offline rendering capabilities")
                return True
            else:
                print("Failed to export scene to QML")
                return False
            
        except Exception as e:
            print(f"Error in image rendering: {e}")
            return False
            
        except Exception as e:
            print(f"Error in image rendering: {e}")
            return False
    
    def update(self, data, depsgraph):
        """更新渲染数据"""
        if not ENGINE_AVAILABLE:
            return
        
        try:
            # 更新场景数据
            scene = depsgraph.scene
            context = bpy.context
            
            # 让Blender处理默认的材质、灯光等更新
            # 我们只需要处理Qt Quick3D特有的设置
            
            # 检查是否有材质或灯光变化
            for update in depsgraph.updates:
                if update.is_updated_geometry:
                    print(f"Geometry updated: {update.id.name}")
                if update.is_updated_material:
                    print(f"Material updated: {update.id.name}")
                if update.is_updated_light:
                    print(f"Light updated: {update.id.name}")
            
        except Exception as e:
            print(f"Error updating render data: {e}")
    
    def view_update(self, context, depsgraph):
        """视图更新"""
        if not ENGINE_AVAILABLE:
            return
        
        try:
            # 更新视图数据
            # 让Blender处理默认的视图更新
            # 我们只需要处理Qt Quick3D特有的视图设置
            
            # 检查相机变化
            for update in depsgraph.updates:
                if update.is_updated_camera:
                    print(f"Camera updated: {update.id.name}")
            
        except Exception as e:
            print(f"Error updating view: {e}")
    
    def view_draw(self, context, depsgraph):
        """视图绘制"""
        if not ENGINE_AVAILABLE:
            return
        
        try:
            # 这里可以添加实时预览绘制逻辑
            pass
            
        except Exception as e:
            print(f"Error in view drawing: {e}")

# 渲染引擎属性面板
class Quick3DRenderEngineProperties(bpy.types.PropertyGroup):

    """Qt Quick3D渲染引擎属性"""
    
    # 质量设置
    samples: IntProperty(
        name="Samples",
        description="Number of samples for rendering",
        default=128,
        min=1,
        max=4096
    )
    
    max_bounces: IntProperty(
        name="Max Bounces",
        description="Maximum number of light bounces",
        default=8,
        min=0,
        max=32
    )
    
    use_denoising: BoolProperty(
        name="Use Denoising",
        description="Enable denoising for final render",
        default=True
    )
    
    render_quality: EnumProperty(
        name="Render Quality",
        description="Quality preset for rendering",
        items=[
            ('DRAFT', "Draft", "Fast preview quality"),
            ('MEDIUM', "Medium", "Balanced quality and speed"),
            ('HIGH', "High", "High quality render"),
            ('PRODUCTION', "Production", "Production quality render")
        ],
        default='MEDIUM'
    )
    
    use_adaptive_sampling: BoolProperty(
        name="Adaptive Sampling",
        description="Use adaptive sampling for better quality",
        default=True
    )
    
    # 输出设置
    output_format: EnumProperty(
        name="Output Format",
        description="Output image format",
        items=[
            ('PNG', "PNG", "PNG format with transparency support"),
            ('JPEG', "JPEG", "JPEG format for web use"),
            ('EXR', "OpenEXR", "High dynamic range format"),
            ('QML', "QML Scene", "Export as QML scene file")
        ],
        default='PNG'
    )
    
    qml_output_path: StringProperty(
        name="QML Output Path",
        description="Path to save QML scene file",
        default="//quick3d_scene.qml",
        subtype='FILE_PATH'
    )

class QT_READ_QML_FILE_FOR_QUICK3D(Operator):
    """读取qml文件，并应用到quick3d中"""
    bl_idname = "qt_quick3d.read_qml_file"
    bl_label = "Read QML File"
    bl_description = "读取qml文件，并应用到quick3d中"
    
    def execute(self, context):
        # TODO: 实现读取qml文件功能
        self.report({'INFO'}, "Read QML file functionality not implemented yet")
        return {'FINISHED'}

class QT_SET_VIEW3D_SETTINGS(Operator):
    """设置view3d和sceneEnvironment的设置，并写在qml中，包住场景导出的qml文件"""
    bl_idname = "qt_quick3d.set_view3d_settings"
    bl_label = "Set View3D Settings"
    bl_description = "设置view3d和sceneEnvironment的设置，并写在qml中，包住场景导出的qml文件"
    
    def execute(self, context):
        # TODO: 实现设置view3d功能
        self.report({'INFO'}, "Set View3D settings functionality not implemented yet")
        return {'FINISHED'}

# 渲染设置面板
class RENDER_PT_quick3d_settings(bpy.types.Panel):
    """Qt Quick3D渲染设置面板"""
    
    bl_label = "Qt Quick3D Settings"
    bl_idname = "RENDER_PT_quick3d_settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'QUICK3D'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.quick3d_properties
        
        # 质量设置
        box = layout.box()
        box.label(text="Quality Settings")
        
        col = box.column(align=True)
        col.prop(props, "samples")
        col.prop(props, "max_bounces")
        col.prop(props, "use_denoising")
        col.prop(props, "render_quality")
        col.prop(props, "use_adaptive_sampling")
        
        # 输出设置
        box = layout.box()
        box.label(text="Output Settings")
        
        col = box.column(align=True)
        col.prop(props, "output_format")
        
        if props.output_format == 'QML':
            col.prop(props, "qml_output_path")

# 注册函数
def register():
    if ENGINE_AVAILABLE:
        bpy.utils.register_class(Quick3DRenderEngine)
        bpy.utils.register_class(Quick3DRenderEngineProperties)
        bpy.utils.register_class(RENDER_PT_quick3d_settings)
        bpy.utils.register_class(QT_READ_QML_FILE_FOR_QUICK3D)
        bpy.utils.register_class(QT_SET_VIEW3D_SETTINGS)
        
        # 注册渲染引擎属性
        bpy.types.Scene.quick3d_properties = PointerProperty(type=Quick3DRenderEngineProperties)
        
        print("✓ Qt Quick3D render engine registered successfully")
    else:
        print("✗ Qt Quick3D render engine not available")

def unregister():
    if ENGINE_AVAILABLE:
        bpy.utils.unregister_class(RENDER_PT_quick3d_settings)
        bpy.utils.unregister_class(QT_SET_VIEW3D_SETTINGS)
        bpy.utils.unregister_class(QT_READ_QML_FILE_FOR_QUICK3D)
        bpy.utils.unregister_class(Quick3DRenderEngineProperties)
        bpy.utils.unregister_class(Quick3DRenderEngine)
        
        # 清理属性
        del bpy.types.Scene.quick3d_properties
        
        print("Qt Quick3D render engine unregistered")

if __name__ == "__main__":
    register()

