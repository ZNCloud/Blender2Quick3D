#!/usr/bin/env python3
"""
测试路径设置的调试脚本
"""

import os
import sys

# 添加插件路径到sys.path
addon_dir = os.path.dirname(os.path.abspath(__file__))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

def test_paths():
    """测试路径设置"""
    print("🔍 测试路径设置...")
    
    try:
        # 导入Balsam转换器
        from balsam_gltf_converter import get_qml_output_dir, get_output_base_dir, get_current_output_status
        
        print("\n📁 路径信息:")
        print(f"  QML输出目录: {get_qml_output_dir()}")
        print(f"  输出基础目录: {get_output_base_dir()}")
        
        print("\n📊 状态信息:")
        status = get_current_output_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # 检查mesh文件
        qml_dir = get_qml_output_dir()
        mesh_file = os.path.join(qml_dir, "meshes", "suzanne_mesh.mesh")
        print(f"\n🔍 Mesh文件检查:")
        print(f"  Mesh文件路径: {mesh_file}")
        print(f"  Mesh文件存在: {'✅' if os.path.exists(mesh_file) else '❌'}")
        
        # 检查目录内容
        if os.path.exists(qml_dir):
            print(f"\n📁 QML目录内容:")
            for item in os.listdir(qml_dir):
                item_path = os.path.join(qml_dir, item)
                if os.path.isdir(item_path):
                    print(f"  📁 {item}/")
                    try:
                        sub_items = os.listdir(item_path)
                        for sub_item in sub_items[:5]:  # 只显示前5个
                            print(f"    - {sub_item}")
                        if len(sub_items) > 5:
                            print(f"    ... 还有 {len(sub_items) - 5} 个文件")
                    except Exception as e:
                        print(f"    ❌ 无法读取子目录: {e}")
                else:
                    print(f"  📄 {item}")
        
        print("\n✅ 路径测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_paths()


