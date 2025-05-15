#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
脚本功能：

DEM图像合并脚本
将四个按经纬度顺序排列的DEM图像合并成一个完整的图像

"""

import os
import re
import numpy as np
import rasterio
from rasterio.merge import merge
import matplotlib.pyplot as plt

# DEM文件目录
DEM_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_coordinates(filename):
    """
    从文件名中提取经纬度信息
    格式示例: ASTGTM_N29E119H.img -> (29, 119)
    """
    match = re.search(r'N(\d+)E(\d+)', filename)
    if match:
        lat = int(match.group(1))
        lon = int(match.group(2))
        return lat, lon
    return None

def get_dem_files():
    """
    获取目录中的所有DEM文件并按经纬度排序
    """
    dem_files = [f for f in os.listdir(DEM_DIR) if f.endswith('.img') and 'ASTGTM' in f]
    
    # 提取坐标信息并排序
    dem_with_coords = []
    for f in dem_files:
        coords = extract_coordinates(f)
        if coords:
            dem_with_coords.append((f, coords))
    
    # 按纬度降序、经度升序排序（从北到南，从西到东）
    dem_with_coords.sort(key=lambda x: (-x[1][0], x[1][1]))
    
    return dem_with_coords

def merge_dem_files(dem_files_with_coords):
    """
    使用rasterio合并DEM文件
    """
    if len(dem_files_with_coords) != 4:
        print(f"需要4个DEM文件，但找到了{len(dem_files_with_coords)}个")
        return None
    
    # 打开所有DEM文件
    src_files_to_mosaic = []
    for file_info in dem_files_with_coords:
        file_name, coords = file_info
        file_path = os.path.join(DEM_DIR, file_name)
        try:
            src = rasterio.open(file_path)
            src_files_to_mosaic.append(src)
            print(f"成功打开文件: {file_name}")
        except Exception as e:
            print(f"无法打开文件 {file_name}: {e}")
            # 关闭已打开的文件
            for src in src_files_to_mosaic:
                src.close()
            return None
    
    try:
        # 合并栅格
        mosaic, out_trans = merge(src_files_to_mosaic)
        
        # 获取元数据（使用第一个文件的元数据作为基础）
        out_meta = src_files_to_mosaic[0].meta.copy()
        
        # 更新元数据
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
        })
        
        return {
            'data': mosaic[0],  # 获取第一个波段的数据
            'meta': out_meta
        }
    except Exception as e:
        print(f"合并DEM文件时出错: {e}")
        return None
    finally:
        # 关闭所有打开的文件
        for src in src_files_to_mosaic:
            src.close()

def save_merged_dem(merged_data, output_file):
    """
    保存合并后的DEM文件
    """
    try:
        with rasterio.open(output_file, 'w', **merged_data['meta']) as dst:
            dst.write(merged_data['data'], 1)  # 写入第一个波段
        print(f"合并后的DEM文件已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"保存合并后的DEM文件时出错: {e}")
        return False

def visualize_dem(dem_data, output_file=None):
    """
    可视化DEM数据
    """
    # 设置matplotlib支持中文显示
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    plt.figure(figsize=(12, 10))
    
    # 处理数据，避免出现蓝色层
    # 将无效值（如NaN或极小值）设置为掩码
    masked_data = np.ma.masked_where(dem_data <= 0, dem_data)
    
    # 使用更适合地形显示的颜色映射，避免蓝色层
    plt.imshow(masked_data, cmap='gist_earth')
    plt.colorbar(label='高程 (米)')
    plt.title('合并后的DEM数据')
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"可视化结果已保存到: {output_file}")
    else:
        plt.show()

def main():
    # 获取DEM文件列表
    dem_files = get_dem_files()
    print(f"找到{len(dem_files)}个DEM文件:")
    for file_info in dem_files:
        print(f"  {file_info[0]} - 坐标: N{file_info[1][0]}E{file_info[1][1]}")
    
    # 合并DEM文件
    merged_data = merge_dem_files(dem_files)
    if merged_data:
        # 保存合并后的文件
        output_file = os.path.join(DEM_DIR, 'merged_dem.tif')
        if save_merged_dem(merged_data, output_file):
            # 可视化
            vis_output = os.path.join(DEM_DIR, 'merged_dem_vis.png')
            visualize_dem(merged_data['data'], vis_output)

if __name__ == "__main__":
    main()