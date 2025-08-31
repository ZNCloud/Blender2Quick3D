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

class QMLHandler:
    """QML处理器类"""
    
    def __init__(self):
        self.qml_output_dir = None
        self.qml_content = None
        self.assembled_qml = None
        
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
    
    def assemble_complete_qml(self, cleaned_qml_content, scene_name="DemoScene"):
        """组装完整的QML内容，包含View3D和SceneEnvironment"""
        if not cleaned_qml_content:
            print("❌ 没有清理后的QML内容可组装")
            return None
        
        try:
            # 创建完整的QML内容
            complete_qml = f'''import QtQuick
import QtQuick3D

Window {{
    visible: true
    width: 1280
    height: 720
    title: "Quick3D Scene - {scene_name}"
    
    View3D {{
        id: view3D
        anchors.fill: parent
        
        environment: SceneEnvironment {{
            clearColor: "#303030"
            backgroundMode: SceneEnvironment.Color
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }}
        
        
        // 插入清理后的QML内容
        {cleaned_qml_content}
    }}
}}'''
            
            print(f"✅ 成功组装完整QML内容")
            print(f"  📊 组装后长度: {len(complete_qml)} 字符")
            
            self.assembled_qml = complete_qml
            return complete_qml
            
        except Exception as e:
            print(f"❌ 组装QML内容失败: {e}")
            return None
    
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

if __name__ == "__main__":
    test_qml_handler()
