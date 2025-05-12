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
        drone_radius: 无人机覆盖半径(米)
        output_path: 输出路径
        info: 额外信息
    """
    # 创建画布
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 转换无人机覆盖半径(米)为经纬度
    drone_radius_degree = drone_radius / 111000  # 转为度
    
    # 绘制行政区域
    gpd.GeoSeries([region_geometry]).plot(ax=ax, color='lightblue', edgecolor='blue', alpha=0.5)
    
    # 检查drone_positions是否有效
    if drone_positions is None or len(drone_positions) == 0:
        print("警告: 无人机位置数据为空")
        plt.title('无人机机库选址 (数据错误)')
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
        return
    
    # 确保drone_positions的形状正确
    if isinstance(drone_positions, np.ndarray) and drone_positions.ndim == 2:
        drone_points = [Point(pos[0], pos[1]) for pos in drone_positions]
    else:
        try:
            # 尝试重塑数组
            reshaped_positions = np.array(drone_positions).reshape(-1, 2)
            drone_points = [Point(pos[0], pos[1]) for pos in reshaped_positions]
            print(f"重塑无人机位置数据: {len(drone_points)}个点")
        except Exception as e:
            print(f"无法处理无人机位置数据: {e}")
            drone_points = []
    
    # 使用传入的drone_buffers或计算新的
    if info and 'drone_buffers' in info and info['drone_buffers']:
        buffers = info['drone_buffers']
        print(f"使用预计算的buffers: {len(buffers)}个")
    else:
        print(f"计算新的buffer，点数: {len(drone_points)}")
        buffers = [point.buffer(drone_radius_degree) for point in drone_points]
    
    # 绘制每个无人机覆盖范围，使用不同的透明度
    for i, buffer in enumerate(buffers):
        # 使用不同颜色或不同透明度
        alpha = 0.3
        gpd.GeoSeries([buffer]).plot(ax=ax, color='red', alpha=alpha)
    
    # 绘制有效覆盖区域（与行政区域的交集）
    merged_buffer = None
    if info and 'merged_buffer' in info:
        merged_buffer = info['merged_buffer']
    else:
        # 合并缓冲区
        if buffers:
            try:
                merged_buffer = buffers[0]
                for buffer in buffers[1:]:
                    merged_buffer = merged_buffer.union(buffer)
            except Exception as e:
                print(f"合并缓冲区时出错: {e}")
    
    if merged_buffer:
        try:
            if isinstance(merged_buffer, MultiPolygon):
                # 计算每个polygon与区域的交集
                valid_polys = []
                for p in merged_buffer.geoms:
                    try:
                        intersection = p.intersection(region_geometry)
                        if not intersection.is_empty and (isinstance(intersection, Polygon) or isinstance(intersection, MultiPolygon)):
                            valid_polys.append(intersection)
                    except Exception as e:
                        print(f"计算多边形交集时出错: {e}")
                
                if valid_polys:
                    try:
                        if len(valid_polys) > 1:
                            coverage_poly = MultiPolygon(valid_polys)
                        else:
                            coverage_poly = valid_polys[0]
                        # 绘制有效覆盖区域
                        gpd.GeoSeries([coverage_poly]).plot(ax=ax, color='blue', alpha=0.5)
                    except Exception as e:
                        print(f"绘制有效覆盖区域时出错: {e}")
            else:
                try:
                    coverage_poly = merged_buffer.intersection(region_geometry)
                    if not coverage_poly.is_empty:
                        gpd.GeoSeries([coverage_poly]).plot(ax=ax, color='blue', alpha=0.5)
                except Exception as e:
                    print(f"计算单一buffer交集时出错: {e}")
        except Exception as e:
            print(f"处理merged_buffer时出错: {e}")
            
    # 创建无人机点的GeoDataFrame并绘制
    drone_gdf = gpd.GeoDataFrame(geometry=drone_points)
    drone_gdf.plot(ax=ax, color='green', markersize=100, marker='x')
    
    # 绘制POI点位
    poi_gdf.plot(ax=ax, color='purple', markersize=20, marker='o')
    
    # 添加图例
    legend_elements = [
        Patch(facecolor='lightblue', edgecolor='blue', alpha=0.5, label='行政区域'),
        Patch(facecolor='red', alpha=0.3, label='无人机覆盖范围'),
        Patch(facecolor='blue', alpha=0.5, label='有效覆盖区域'),
        plt.Line2D([], [], color='green', marker='x', linestyle='None', markersize=10, label='无人机点位'),
        plt.Line2D([], [], color='purple', marker='o', linestyle='None', markersize=6, label='POI点位')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # 添加标题和信息
    coverage_ratio = info['poi_coverage'] * 100 if info and 'poi_coverage' in info else 0
    area_coverage = info['area_coverage'] * 100 if info and 'area_coverage' in info else 0
    overlap_ratio = info['overlap_ratio'] * 100 if info and 'overlap_ratio' in info else 0
    
    plt.title(f'无人机机库选址 (POI覆盖率: {coverage_ratio:.1f}%)')
    
    # 添加坐标轴标签
    plt.xlabel('经度')
    plt.ylabel('纬度')
    
    # 将点的坐标添加为标签
    for i, point in enumerate(drone_points):
        plt.annotate(f"D{i+1}", xy=(point.x, point.y), xytext=(5, 5), 
                     textcoords='offset points', fontsize=8)
    
    # 添加覆盖信息文本
    info_text = (
        f'POI覆盖率: {coverage_ratio:.1f}%\n'
        f'区域覆盖率: {area_coverage:.1f}%\n'
        f'重叠率: {overlap_ratio:.1f}%\n'
        f'覆盖POI点数: {info["poi_covered"] if info and "poi_covered" in info else 0}\n'
        f'无人机数量: {len(drone_points)}'
    )
    plt.annotate(info_text, xy=(0.02, 0.02), xycoords='axes fraction', 
                 bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8))
    
    # 保存或显示图形
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"已保存可视化结果到: {output_path}")
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
        print(f"已保存训练进度图到: {output_path}")
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
    
    # 计算奖励和信息
    _, info = env._compute_reward()
    
    # 可视化
    print("生成测试可视化...")
    visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, "test_visualization.png", info)
    print("可视化测试完成!") 