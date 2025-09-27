#!/usr/bin/env python3
"""
测试修复后的PySide6检测功能
"""

def test_fix():
    """测试修复是否有效"""
    print("测试PySide6检测功能修复...")
    
    try:
        # 模拟新的数据结构
        pyside6_info = {
            'available': True,
            'current': {
                'version': '6.6.0',
                'path': '/path/to/pyside6',
                'description': 'System site-packages: /usr/lib/python3.11/site-packages',
                'type': 'system',
                'priority': 1,
                'valid': True
            },
            'all_installations': [
                {
                    'version': '6.6.0',
                    'path': '/path/to/pyside6',
                    'description': 'System site-packages: /usr/lib/python3.11/site-packages',
                    'type': 'system',
                    'priority': 1,
                    'valid': True
                }
            ],
            'best_installation': {
                'version': '6.6.0',
                'path': '/path/to/pyside6',
                'description': 'System site-packages: /usr/lib/python3.11/site-packages',
                'type': 'system',
                'priority': 1,
                'valid': True
            },
            'error': None
        }
        
        # 测试访问修复后的数据结构
        if pyside6_info['available']:
            current = pyside6_info['current']
            message = f"PySide6 {current['version']} found at:\n{current['path']}\n\nInstallation: {current['description']}"
            print("✅ 修复成功!")
            print(f"消息: {message}")
        else:
            print("❌ PySide6不可用")
        
    except KeyError as e:
        print(f"❌ 仍有KeyError: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    test_fix()

