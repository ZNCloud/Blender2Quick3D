#!/usr/bin/env python3
"""
QML处理器测试脚本
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_qml_handler():
    """测试QML处理器"""
    try:
        print("🧪 开始测试QML处理器...")
        
        # 导入QML处理器
        import qml_handler
        print("✅ QML处理器模块导入成功")
        
        # 创建处理器实例
        handler = qml_handler.QMLHandler()
        print("✅ QML处理器实例创建成功")
        
        # 测试环境设置
        print("\n1. 测试环境设置...")
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
                    
                    # 显示内容预览
                    print(f"\n📄 QML内容预览:")
                    print("=" * 50)
                    print(assembled_qml[:500] + "..." if len(assembled_qml) > 500 else assembled_qml)
                    print("=" * 50)
                    
                    # 测试保存功能
                    print(f"\n4. 测试保存功能...")
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
        
        # 测试便捷函数
        print(f"\n5. 测试便捷函数...")
        qml_content = qml_handler.get_qml_content_for_integration()
        if qml_content:
            print("✅ 便捷函数测试成功")
            print(f"📊 获取到的QML内容长度: {len(qml_content)} 字符")
        else:
            print("❌ 便捷函数测试失败")
        
        print("\n🎉 QML处理器测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qml_handler()
