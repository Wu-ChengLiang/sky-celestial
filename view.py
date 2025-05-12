import os
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
from shapely.geometry import Point, MultiPolygon, Polygon

def visualize(region_geometry, poi_gdf, drone_positions, drone_radius, output_path=None, info=None):
    """
    可视化无人机覆盖情况
    
    参数:
        region_geometry: 区域几何形状
        poi_gdf: POI的GeoDataFrame
        drone_positions: 无人机库位置坐标
        drone_radius: 无人机覆盖半径
        output_path: 输出路径
        info: 额外信息
    """
    # 创建画布
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 绘制行政区域
    gpd.GeoSeries([region_geometry]).plot(ax=ax, color='lightgray', edgecolor='black', label='行政区域')
    
    # 绘制无人机点位
    drone_points = [Point(pos[0], pos[1]) for pos in drone_positions]
    points_gdf = gpd.GeoDataFrame(geometry=drone_points)
    points_gdf.plot(ax=ax, color='green', markersize=50, marker='x', label='无人机点位')
    
    # 计算无人机覆盖范围
    buffers = [point.buffer(drone_radius) for point in drone_points]
    
    # 绘制所有缓冲区
    gpd.GeoSeries(buffers).plot(ax=ax, color='red', alpha=0.3, label='无人机覆盖范围')
    
    # 合并缓冲区
    merged_buffer = None
    if buffers:
        merged_buffer = buffers[0]
        for buffer in buffers[1:]:
            merged_buffer = merged_buffer.union(buffer)
    
    # 计算有效覆盖区域（与行政区域的交集）
    if merged_buffer:
        if isinstance(merged_buffer, MultiPolygon):
            intersected_polys = [p.intersection(region_geometry) for p in merged_buffer.geoms]
            # 过滤掉空结果并确保都是Polygon
            valid_polys = [p for p in intersected_polys if not p.is_empty and (isinstance(p, Polygon) or isinstance(p, MultiPolygon))]
            if valid_polys:
                if len(valid_polys) > 1:
                    coverage_poly = MultiPolygon(valid_polys)
                else:
                    coverage_poly = valid_polys[0]
                # 绘制有效覆盖区域
                gpd.GeoSeries([coverage_poly]).plot(ax=ax, color='blue', alpha=0.5, label='有效覆盖区域')
        else:
            coverage_poly = merged_buffer.intersection(region_geometry)
            if not coverage_poly.is_empty:
                gpd.GeoSeries([coverage_poly]).plot(ax=ax, color='blue', alpha=0.5, label='有效覆盖区域')
    
    # 绘制POI点位
    poi_gdf.plot(ax=ax, color='purple', markersize=10, marker='o', label='POI点位')
    
    # 添加图例
    legend_elements = [
        Patch(facecolor='lightgray', edgecolor='black', label='行政区域'),
        Patch(facecolor='red', alpha=0.3, label='无人机覆盖范围'),
        Patch(facecolor='blue', alpha=0.5, label='有效覆盖区域'),
        plt.Line2D([], [], color='green', marker='x', linestyle='None', markersize=10, label='无人机点位'),
        plt.Line2D([], [], color='purple', marker='o', linestyle='None', markersize=6, label='POI点位')
    ]
    ax.legend(handles=legend_elements)
    
    # 添加标题
    coverage_ratio = info['poi_coverage'] * 100 if info else 0
    plt.title(f'无人机机库选址 (POI覆盖率: {coverage_ratio:.1f}%)')
    
    # 保存或显示图形
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()

def visualize_training_progress(rewards, avg_rewards, output_path=None):
    """
    可视化训练进度
    
    参数:
        rewards: 每轮的奖励
        avg_rewards: 平均奖励
        output_path: 输出路径
    """
    plt.figure(figsize=(10, 5))
    plt.plot(rewards, label='Reward')
    plt.plot(avg_rewards, label='Avg Reward (100 ep)', color='red')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.title('Training Progress')
    plt.legend()
    plt.grid(True)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()

if __name__ == "__main__":
    # 测试可视化模块
    from configs import Config
    from env import DroneEnvironment
    
    config = Config()
    env = DroneEnvironment(config)
    
    # 随机生成无人机库位置
    state, _ = env.reset()
    drone_positions = state.reshape(-1, 2)
    
    # 可视化
    visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, "test_visualization.png", None) 