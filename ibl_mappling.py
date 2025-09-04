#!/usr/bin/env python3
"""
IBL (Image-Based Lighting) Mapping for Blender2Quick3D
This module handles world shader nodes and extracts connected image texture file paths
"""

import bpy
import os
import shutil
from typing import List, Dict, Optional, Tuple


def get_world_surface_connected_image_paths() -> Dict[str, str]:
    """
    获取Blender world下连接着surface的图像或环境图节点的文件路径
    
    Returns:
        Dict[str, str]: 包含图像路径信息的字典
        {
            'surface_image': 'path/to/surface/image.jpg',  # surface输入连接的图像
            'environment_image': 'path/to/environment/hdr',  # 环境图路径
            'has_surface_connection': True,  # 是否有surface连接
            'has_environment_connection': True,  # 是否有环境图连接
            'world_name': 'World',  # world名称
            'surface_node_type': 'ShaderNodeBackground',  # surface节点类型
            'environment_node_type': 'ShaderNodeTexEnvironment'  # 环境图节点类型
        }
    """
    result = {
        'surface_image': '',
        'environment_image': '',
        'has_surface_connection': False,
        'has_environment_connection': False,
        'world_name': '',
        'surface_node_type': '',
        'environment_node_type': '',
        'has_ibl': False,  # 新增：是否有IBL图像
        'ibl_path': ''  # 新增：IBL图像在maps目录中的路径
    }
    
    try:
        # 获取当前场景的world
        world = bpy.context.scene.world
        if not world:
            print("❌ 当前场景没有world")
            return result
        
        result['world_name'] = world.name
        print(f"🌍 检查World: {world.name}")
        
        # 检查world是否有节点树
        if not world.use_nodes or not world.node_tree:
            print("❌ World没有启用节点或没有节点树")
            return result
        
        node_tree = world.node_tree
        print(f"🌳 World节点树: {node_tree.name}")
        
        # 查找World Output节点
        world_output = None
        for node in node_tree.nodes:
            if node.type == 'OUTPUT_WORLD':
                world_output = node
                break
        
        if not world_output:
            print("❌ 未找到World Output节点")
            return result
        
        print(f"🔌 找到World Output节点: {world_output.name}")
        
        # 检查surface输入连接
        surface_input = world_output.inputs.get('Surface')
        if surface_input and surface_input.is_linked:
            result['has_surface_connection'] = True
            print(f"✅ Surface输入已连接")
            
            # 获取连接的节点
            surface_node = surface_input.links[0].from_node
            result['surface_node_type'] = surface_node.type
            print(f"🔗 Surface连接节点: {surface_node.name} (类型: {surface_node.type})")
            
            # 根据节点类型获取图像路径
            surface_image_path = _get_image_path_from_node(surface_node)
            if surface_image_path:
                result['surface_image'] = surface_image_path
                print(f"🖼️ Surface图像路径: {surface_image_path}")
            else:
                print("⚠️ 无法从Surface节点获取图像路径")
        else:
            print("❌ Surface输入未连接")
        
        # 检查environment输入连接（如果存在）
        environment_input = world_output.inputs.get('Environment')
        if environment_input and environment_input.is_linked:
            result['has_environment_connection'] = True
            print(f"✅ Environment输入已连接")
            
            # 获取连接的节点
            environment_node = environment_input.links[0].from_node
            result['environment_node_type'] = environment_node.type
            print(f"🔗 Environment连接节点: {environment_node.name} (类型: {environment_node.type})")
            
            # 根据节点类型获取图像路径
            environment_image_path = _get_image_path_from_node(environment_node)
            if environment_image_path:
                result['environment_image'] = environment_image_path
                print(f"🌍 Environment图像路径: {environment_image_path}")
            else:
                print("⚠️ 无法从Environment节点获取图像路径")
        else:
            print("❌ Environment输入未连接")
        
        # 注意：我们不再在整个节点树中搜索环境图节点
        # 只查找与world surface有直接或间接连接的图像
        
        # 设置IBL相关标志和路径
        if result['surface_image'] or result['environment_image']:
            result['has_ibl'] = True
            
            # 确定IBL图像路径（优先使用environment，其次surface）
            if result['environment_image']:
                _, ext = os.path.splitext(result['environment_image'])
                result['ibl_path'] = f"maps/iblimage{ext}"
                print(f"🌍 设置IBL路径: {result['ibl_path']}")
            elif result['surface_image']:
                _, ext = os.path.splitext(result['surface_image'])
                result['ibl_path'] = f"maps/iblimage{ext}"
                print(f"🖼️ 设置IBL路径: {result['ibl_path']}")
        else:
            print("ℹ️ 没有IBL图像")
        
        return result
        
    except Exception as e:
        print(f"❌ 获取world surface连接图像路径失败: {e}")
        import traceback
        traceback.print_exc()
        return result


def _get_image_path_from_node(node, visited_nodes=None) -> Optional[str]:
    """
    从节点获取图像文件路径（递归查找，避免循环）
    
    Args:
        node: Blender节点对象
        visited_nodes: 已访问的节点集合，用于避免循环
        
    Returns:
        Optional[str]: 图像文件路径，如果找不到则返回None
    """
    if visited_nodes is None:
        visited_nodes = set()
    
    # 避免循环访问
    if node in visited_nodes:
        print(f"⚠️ 检测到循环访问节点: {node.name}")
        return None
    
    visited_nodes.add(node)
    
    try:
        print(f"🔍 检查节点: {node.name} (类型: {node.type})")
        
        # 处理不同类型的节点
        if node.type == 'TEX_ENVIRONMENT':
            # 环境图节点
            if hasattr(node, 'image') and node.image:
                image = node.image
                if image.filepath:
                    # 转换为绝对路径
                    abs_path = bpy.path.abspath(image.filepath)
                    if os.path.exists(abs_path):
                        print(f"✅ 找到环境图: {abs_path}")
                        return abs_path
                    else:
                        print(f"⚠️ 环境图文件不存在: {abs_path}")
                        return image.filepath  # 返回原始路径
                else:
                    print("⚠️ 环境图节点没有文件路径")
            else:
                print("⚠️ 环境图节点没有图像")
        
        elif node.type == 'TEX_IMAGE':
            # 图像纹理节点
            if hasattr(node, 'image') and node.image:
                image = node.image
                if image.filepath:
                    # 转换为绝对路径
                    abs_path = bpy.path.abspath(image.filepath)
                    if os.path.exists(abs_path):
                        print(f"✅ 找到图像纹理: {abs_path}")
                        return abs_path
                    else:
                        print(f"⚠️ 图像文件不存在: {abs_path}")
                        return image.filepath  # 返回原始路径
                else:
                    print("⚠️ 图像节点没有文件路径")
            else:
                print("⚠️ 图像节点没有图像")
        
        elif node.type == 'BACKGROUND':
            # 背景着色器节点 - 检查其输入连接
            color_input = node.inputs.get('Color')
            if color_input and color_input.is_linked:
                print(f"🔗 Background节点有颜色输入连接，继续查找...")
                # 递归查找连接的图像节点
                image_path = _get_image_path_from_node(color_input.links[0].from_node, visited_nodes)
                if image_path:
                    print(f"✅ 通过Background节点找到图像: {image_path}")
                    return image_path
                else:
                    print("⚠️ 通过Background节点未找到图像")
            else:
                print("⚠️ 背景着色器节点没有颜色输入连接")
        
        elif node.type == 'EMISSION':
            # 发光着色器节点 - 检查其输入连接
            color_input = node.inputs.get('Color')
            if color_input and color_input.is_linked:
                print(f"🔗 Emission节点有颜色输入连接，继续查找...")
                # 递归查找连接的图像节点
                image_path = _get_image_path_from_node(color_input.links[0].from_node, visited_nodes)
                if image_path:
                    print(f"✅ 通过Emission节点找到图像: {image_path}")
                    return image_path
                else:
                    print("⚠️ 通过Emission节点未找到图像")
            else:
                print("⚠️ 发光着色器节点没有颜色输入连接")
        
        elif node.type == 'MIX':
            # 混合节点 - 检查其输入连接
            print(f"🔗 Mix节点，检查所有输入...")
            for input_name in ['Fac', 'Color1', 'Color2']:
                input_socket = node.inputs.get(input_name)
                if input_socket and input_socket.is_linked:
                    print(f"  检查输入: {input_name}")
                    image_path = _get_image_path_from_node(input_socket.links[0].from_node, visited_nodes)
                    if image_path:
                        print(f"✅ 通过Mix节点({input_name})找到图像: {image_path}")
                        return image_path
            print("⚠️ Mix节点未找到图像")
        
        elif node.type == 'MAPPING':
            # 映射节点 - 检查其输入连接
            vector_input = node.inputs.get('Vector')
            if vector_input and vector_input.is_linked:
                print(f"🔗 Mapping节点有Vector输入连接，继续查找...")
                image_path = _get_image_path_from_node(vector_input.links[0].from_node, visited_nodes)
                if image_path:
                    print(f"✅ 通过Mapping节点找到图像: {image_path}")
                    return image_path
                else:
                    print("⚠️ 通过Mapping节点未找到图像")
            else:
                print("⚠️ Mapping节点没有Vector输入连接")
        
        elif node.type == 'TEX_COORD':
            # 纹理坐标节点 - 通常不直接包含图像
            print("ℹ️ 纹理坐标节点，无法继续查找图像")
            return None
        
        else:
            print(f"ℹ️ 未处理的节点类型: {node.type}")
            # 尝试查找所有输入连接
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    print(f"  检查输入: {input_socket.name}")
                    image_path = _get_image_path_from_node(input_socket.links[0].from_node, visited_nodes)
                    if image_path:
                        print(f"✅ 通过{node.type}节点找到图像: {image_path}")
                        return image_path
            print(f"⚠️ {node.type}节点未找到图像")
        
        return None
        
    except Exception as e:
        print(f"❌ 从节点获取图像路径失败: {e}")
        return None
    finally:
        # 从访问集合中移除当前节点，允许其他路径访问
        visited_nodes.discard(node)




def get_all_world_image_paths() -> List[Dict[str, str]]:
    """
    获取所有world中的图像路径信息
    
    Returns:
        List[Dict[str, str]]: 包含所有world图像路径信息的列表
    """
    results = []
    
    try:
        # 遍历所有world
        for world in bpy.data.worlds:
            print(f"\n🌍 检查World: {world.name}")
            
            # 临时设置当前world为场景的world
            original_world = bpy.context.scene.world
            bpy.context.scene.world = world
            
            # 获取图像路径信息
            world_info = get_world_surface_connected_image_paths()
            world_info['world_name'] = world.name
            results.append(world_info)
            
            # 恢复原始world
            bpy.context.scene.world = original_world
        
        return results
        
    except Exception as e:
        print(f"❌ 获取所有world图像路径失败: {e}")
        return results


def print_world_image_info():
    """打印当前world的图像信息"""
    print("=" * 60)
    print("🌍 Blender World Surface 图像路径信息")
    print("=" * 60)
    
    info = get_world_surface_connected_image_paths()
    
    print(f"World名称: {info['world_name']}")
    print(f"Surface连接: {'✅' if info['has_surface_connection'] else '❌'}")
    print(f"Environment连接: {'✅' if info['has_environment_connection'] else '❌'}")
    print(f"有IBL图像: {'✅' if info['has_ibl'] else '❌'}")
    
    if info['surface_image']:
        print(f"Surface图像: {info['surface_image']}")
        print(f"Surface节点类型: {info['surface_node_type']}")
    else:
        print("Surface图像: 无")
    
    if info['environment_image']:
        print(f"Environment图像: {info['environment_image']}")
        print(f"Environment节点类型: {info['environment_node_type']}")
    else:
        print("Environment图像: 无")
    
    if info['has_ibl']:
        print(f"IBL路径: {info['ibl_path']}")
    else:
        print("IBL路径: 无")
    
    print("=" * 60)




def get_balsam_output_base_dir() -> Optional[str]:
    """
    从balsam转换器获取当前输出基础目录
    
    Returns:
        Optional[str]: 输出基础目录路径，如果获取失败则返回None
    """
    try:
        # 尝试导入balsam转换器模块
        from . import balsam_gltf_converter
        
        # 获取输出基础目录
        output_base_dir = balsam_gltf_converter.get_output_base_dir()
        
        if output_base_dir and os.path.exists(output_base_dir):
            print(f"✅ 获取到Balsam输出基础目录: {output_base_dir}")
            return output_base_dir
        else:
            print(f"⚠️ Balsam输出基础目录不存在: {output_base_dir}")
            return None
            
    except ImportError as e:
        print(f"❌ 无法导入balsam_gltf_converter模块: {e}")
        return None
    except Exception as e:
        print(f"❌ 获取Balsam输出基础目录失败: {e}")
        return None


def copy_world_image_to_balsam_output(image_path: str, output_base_dir: str = None) -> Optional[str]:
    """
    将world图像复制到balsam输出目录，并重命名为iblimage+后缀名
    
    Args:
        image_path: 源图像文件路径
        output_base_dir: 输出基础目录，如果为None则自动获取
        
    Returns:
        Optional[str]: 复制后的文件路径，如果失败则返回None
    """
    try:
        # 检查源文件是否存在
        if not os.path.exists(image_path):
            print(f"❌ 源图像文件不存在: {image_path}")
            return None
        
        # 获取输出基础目录
        if output_base_dir is None:
            base = get_balsam_output_base_dir()
            if not base:
                print("❌ 无法获取Balsam输出基础目录")
                return None
            output_base_dir = os.path.join(base, "maps")
        
        # 确保输出目录存在
        os.makedirs(output_base_dir, exist_ok=True)
        
        # 获取文件扩展名
        _, ext = os.path.splitext(image_path)
        if not ext:
            # 如果没有扩展名，尝试从文件内容判断
            ext = _detect_image_extension(image_path)
        
        # 生成新的文件名
        new_filename = f"iblimage{ext}"
        dest_path = os.path.join(output_base_dir, new_filename)
        
        # 复制文件
        shutil.copy2(image_path, dest_path)
        
        print(f"✅ 图像复制成功:")
        print(f"  源文件: {image_path}")
        print(f"  目标文件: {dest_path}")
        
        return dest_path
        
    except Exception as e:
        print(f"❌ 复制图像文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def copy_all_world_images_to_balsam_output(output_base_dir: str = None) -> Dict[str, str]:
    """
    复制所有world图像到balsam输出目录
    
    Args:
        output_base_dir: 输出基础目录，如果为None则自动获取
        
    Returns:
        Dict[str, str]: 包含复制结果的字典
        {
            'surface_image_dest': 'path/to/iblimage.jpg',  # surface图像复制后的路径
            'environment_image_dest': 'path/to/iblimage.hdr',  # environment图像复制后的路径
            'surface_copied': True,  # surface图像是否复制成功
            'environment_copied': True,  # environment图像是否复制成功
            'output_base_dir': 'path/to/output'  # 输出基础目录
        }
    """
    result = {
        'surface_image_dest': '',
        'environment_image_dest': '',
        'surface_copied': False,
        'environment_copied': False,
        'output_base_dir': ''
    }
    
    try:
        # 获取world图像信息
        world_info = get_world_surface_connected_image_paths()
        
        # 获取输出基础目录
        if output_base_dir is None:
            base = get_balsam_output_base_dir()
            if not base:
                print("❌ 无法获取Balsam输出基础目录")
                return result
            output_base_dir = os.path.join(base, "maps")
        
        result['output_base_dir'] = output_base_dir
        
        # 复制surface图像
        if world_info['surface_image']:
            print(f"\n🖼️ 复制Surface图像...")
            surface_dest = copy_world_image_to_balsam_output(
                world_info['surface_image'], 
                output_base_dir
            )
            if surface_dest:
                result['surface_image_dest'] = surface_dest
                result['surface_copied'] = True
                print(f"✅ Surface图像复制成功: {surface_dest}")
            else:
                print("❌ Surface图像复制失败")
        else:
            print("ℹ️ 没有Surface图像需要复制")
        
        # 复制environment图像
        if world_info['environment_image']:
            print(f"\n🌍 复制Environment图像...")
            environment_dest = copy_world_image_to_balsam_output(
                world_info['environment_image'], 
                output_base_dir
            )
            if environment_dest:
                result['environment_image_dest'] = environment_dest
                result['environment_copied'] = True
                print(f"✅ Environment图像复制成功: {environment_dest}")
            else:
                print("❌ Environment图像复制失败")
        else:
            print("ℹ️ 没有Environment图像需要复制")
        
        return result
        
    except Exception as e:
        print(f"❌ 复制world图像失败: {e}")
        import traceback
        traceback.print_exc()
        return result


def _detect_image_extension(file_path: str) -> str:
    """
    检测图像文件的扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 检测到的扩展名，如果无法检测则返回'.unknown'
    """
    try:
        # 读取文件头来判断图像类型
        with open(file_path, 'rb') as f:
            header = f.read(16)
        
        # 检查常见图像格式的文件头
        if header.startswith(b'\xff\xd8\xff'):
            return '.jpg'
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):
            return '.png'
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return '.gif'
        elif header.startswith(b'BM'):
            return '.bmp'
        elif header.startswith(b'RIFF') and b'WEBP' in header:
            return '.webp'
        elif header.startswith(b'\x00\x00\x01\x00'):
            return '.ico'
        elif header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
            return '.tiff'
        elif header.startswith(b'#?RADIANCE'):
            return '.hdr'
        elif header.startswith(b'#?RGBE'):
            return '.hdr'
        else:
            print(f"⚠️ 无法识别图像格式: {file_path}")
            return '.unknown'
            
    except Exception as e:
        print(f"⚠️ 检测图像扩展名失败: {e}")
        return '.unknown'


def get_ibl_image_paths_in_output(output_base_dir: str = None) -> Dict[str, str]:
    """
    获取输出目录中的IBL图像路径
    
    Args:
        output_base_dir: 输出基础目录，如果为None则自动获取
        
    Returns:
        Dict[str, str]: 包含IBL图像路径的字典
        {
            'iblimage_files': ['path1', 'path2', ...],  # 所有iblimage文件
            'surface_iblimage': 'path/to/iblimage.jpg',  # surface对应的iblimage
            'environment_iblimage': 'path/to/iblimage.hdr',  # environment对应的iblimage
            'output_base_dir': 'path/to/output'  # 输出基础目录
        }
    """
    result = {
        'iblimage_files': [],
        'surface_iblimage': '',
        'environment_iblimage': '',
        'output_base_dir': ''
    }
    
    try:
        # 获取输出基础目录
        if output_base_dir is None:
            output_base_dir = get_balsam_output_base_dir()
            if not output_base_dir:
                print("❌ 无法获取Balsam输出基础目录")
                return result
        
        result['output_base_dir'] = output_base_dir
        
        # 查找所有iblimage文件
        if os.path.exists(output_base_dir):
            for filename in os.listdir(output_base_dir):
                if filename.startswith('iblimage'):
                    file_path = os.path.join(output_base_dir, filename)
                    result['iblimage_files'].append(file_path)
                    print(f"✅ 找到IBL图像文件: {filename}")
        
        # 尝试匹配surface和environment图像
        world_info = get_world_surface_connected_image_paths()
        
        if world_info['surface_image']:
            # 查找对应的iblimage文件
            surface_ext = os.path.splitext(world_info['surface_image'])[1]
            surface_iblimage = os.path.join(output_base_dir, f"iblimage{surface_ext}")
            if os.path.exists(surface_iblimage):
                result['surface_iblimage'] = surface_iblimage
                print(f"✅ 找到Surface IBL图像: {surface_iblimage}")
        
        if world_info['environment_image']:
            # 查找对应的iblimage文件
            environment_ext = os.path.splitext(world_info['environment_image'])[1]
            environment_iblimage = os.path.join(output_base_dir, f"iblimage{environment_ext}")
            if os.path.exists(environment_iblimage):
                result['environment_iblimage'] = environment_iblimage
                print(f"✅ 找到Environment IBL图像: {environment_iblimage}")
        
        return result
        
    except Exception as e:
        print(f"❌ 获取IBL图像路径失败: {e}")
        import traceback
        traceback.print_exc()
        return result


def main():
    """主函数，用于测试"""
    print_world_image_info()
    
    # 测试复制功能
    print("\n" + "=" * 60)
    print("🔄 测试复制World图像到Balsam输出目录...")
    print("=" * 60)
    
    copy_result = copy_all_world_images_to_balsam_output()
    
    print(f"\n📊 复制结果:")
    print(f"输出目录: {copy_result['output_base_dir']}")
    print(f"Surface图像复制: {'✅' if copy_result['surface_copied'] else '❌'}")
    print(f"Environment图像复制: {'✅' if copy_result['environment_copied'] else '❌'}")
    
    if copy_result['surface_image_dest']:
        print(f"Surface IBL图像: {copy_result['surface_image_dest']}")
    if copy_result['environment_image_dest']:
        print(f"Environment IBL图像: {copy_result['environment_image_dest']}")


if __name__ == "__main__":
    main()
