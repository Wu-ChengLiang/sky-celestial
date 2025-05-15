import os
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
from shapely.geometry import Point, MultiPolygon, Polygon
import rasterio
from matplotlib.colors import LinearSegmentedColormap

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
    
    # 先绘制行政区域作为底图
    gpd.GeoSeries([region_geometry]).plot(ax=ax, color='lightblue', edgecolor='blue', alpha=0.3)
    
    # 尝试获取配置和DEM数据以可视化海拔
    dem_file = None
    try:
        from configs import Config
        config = Config()
        if os.path.exists(config.DEM_FILE):
            dem_file = config.DEM_FILE
    except Exception as e:
        print(f"加载配置失败: {e}")
    
    # 绘制DEM数据
    dem_shown = False
    if dem_file:
        try:
            # 获取区域边界用于设置绘图范围
            bounds = region_geometry.bounds  # (minx, miny, maxx, maxy)
            
            with rasterio.open(dem_file) as src:
                # 读取DEM数据
                dem_data = src.read(1)
                
                # 创建地形图配色方案 (低海拔为绿色，高海拔为棕色)
                terrain_colors = {'green': '#267300', 'yellow': '#FFFF00', 'brown': '#A87000', 'white': '#FFFFFF'}
                cmap = LinearSegmentedColormap.from_list('terrain', 
                                                        [(0.0, terrain_colors['green']), 
                                                         (0.3, terrain_colors['green']),
                                                         (0.5, terrain_colors['yellow']),
                                                         (0.7, terrain_colors['brown']),
                                                         (1.0, terrain_colors['white'])])
                
                # 设置最小、最大值以增强对比度
                vmin = max(0, np.nanmin(dem_data))
                vmax = min(500, np.nanmax(dem_data))
                
                # 创建DEM数据的网格
                rows, cols = dem_data.shape
                
                # 获取地理变换信息，用于将行列索引转换为地理坐标
                transform = src.transform
                xs = np.array([transform[0] + (col + 0.5) * transform[1] for col in range(cols)])
                ys = np.array([transform[3] + (row + 0.5) * transform[5] for row in range(rows)])
                
                # 使用pcolormesh进行显示（比imshow更适合地理数据）
                # 由于xs和ys可能很大，我们使用一个缩放系数来减少数据量
                scale_factor = 10  # 减少10倍数据点
                dem_plot = ax.pcolormesh(
                    xs[::scale_factor], 
                    ys[::scale_factor], 
                    dem_data[::scale_factor, ::scale_factor],
                    cmap=cmap, 
                    vmin=vmin, 
                    vmax=vmax, 
                    alpha=0.4
                )
                
                # 添加色条
                cbar = plt.colorbar(dem_plot, ax=ax, label='海拔 (米)', shrink=0.5, pad=0.01)
                
                # 设置绘图区域范围与行政区域一致
                ax.set_xlim(bounds[0], bounds[2])
                ax.set_ylim(bounds[1], bounds[3])
                
                dem_shown = True
                print(f"DEM显示成功，数据范围: {vmin}-{vmax}米")
        except Exception as e:
            print(f"绘制DEM数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 如果DEM绘制成功，增强行政区域边界的可见性
    if dem_shown:
        gpd.GeoSeries([region_geometry]).plot(ax=ax, color='none', edgecolor='blue', alpha=1.0, linewidth=2)
    
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
    
    # 获取海拔信息
    drone_elevations = info.get('drone_elevations', [0] * len(drone_points)) if info else [0] * len(drone_points)
    elevation_threshold = 50  # 默认阈值，如果有配置可以替换
    try:
        from configs import Config
        elevation_threshold = Config.ELEVATION_THRESHOLD
    except:
        pass
    
    # 创建无人机点的GeoDataFrame并绘制，根据海拔使用不同颜色
    drone_gdf = gpd.GeoDataFrame(geometry=drone_points)
    # 添加海拔数据作为属性
    drone_gdf['elevation'] = drone_elevations
    
    # 根据海拔分类绘制点: 低于阈值为绿色，高于阈值为红色
    low_elevation_points = drone_gdf[drone_gdf['elevation'] <= elevation_threshold]
    high_elevation_points = drone_gdf[drone_gdf['elevation'] > elevation_threshold]
    
    # 绘制低海拔和高海拔的点，增大点的大小和可见性
    if not low_elevation_points.empty:
        low_elevation_points.plot(ax=ax, color='green', markersize=150, marker='x', linewidth=3)
    if not high_elevation_points.empty:
        high_elevation_points.plot(ax=ax, color='red', markersize=150, marker='x', linewidth=3)
    
    # 绘制POI点位，调整大小以提高可见性
    poi_gdf.plot(ax=ax, color='purple', markersize=30, marker='o')
    
    # 添加图例
    legend_elements = [
        Patch(facecolor='lightblue', edgecolor='blue', alpha=0.5, label='行政区域'),
        Patch(facecolor='red', alpha=0.3, label='无人机覆盖范围'),
        Patch(facecolor='blue', alpha=0.5, label='有效覆盖区域'),
        plt.Line2D([], [], color='green', marker='x', linestyle='None', markersize=10, label=f'无人机点位 (≤{elevation_threshold}米)'),
        plt.Line2D([], [], color='red', marker='x', linestyle='None', markersize=10, label=f'无人机点位 (>{elevation_threshold}米)'),
        plt.Line2D([], [], color='purple', marker='o', linestyle='None', markersize=6, label='POI点位')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # 添加标题和信息
    coverage_ratio = info['poi_coverage'] * 100 if info and 'poi_coverage' in info else 0
    area_coverage = info['area_coverage'] * 100 if info and 'area_coverage' in info else 0
    overlap_ratio = info['overlap_ratio'] * 100 if info and 'overlap_ratio' in info else 0
    elevation_penalty = info['elevation_penalty'] if info and 'elevation_penalty' in info else 0
    
    plt.title(f'无人机机库选址 (POI覆盖率: {coverage_ratio:.1f}%)')
    
    # 添加坐标轴标签
    plt.xlabel('经度')
    plt.ylabel('纬度')
    
    # 将点的坐标添加为标签，显示海拔信息
    for i, (point, elev) in enumerate(zip(drone_points, drone_elevations)):
        plt.annotate(f"D{i+1}\n{elev:.0f}m", xy=(point.x, point.y), xytext=(5, 5), 
                     textcoords='offset points', fontsize=10, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7))
    
    # 添加覆盖信息文本
    info_text = (
        f'POI覆盖率: {coverage_ratio:.1f}%\n'
        f'区域覆盖率: {area_coverage:.1f}%\n'
        f'重叠率: {overlap_ratio:.1f}%\n'
        f'覆盖POI点数: {info["poi_covered"] if info and "poi_covered" in info else 0}\n'
        f'无人机数量: {len(drone_points)}\n'
        f'海拔惩罚: {elevation_penalty:.4f}'
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
    from env.drone_env import DroneEnvironment
    import matplotlib.pyplot as plt
    
    print("开始可视化测试...")
    
    try:
        # 创建配置和环境
        config = Config()
        print(f"DEM文件路径: {config.DEM_FILE}")
        env = DroneEnvironment(config)
        
        # 随机生成无人机库位置
        state, _ = env.reset()
        drone_positions = state.reshape(-1, 2)
        
        # 计算奖励和信息
        reward, info = env._compute_reward()
        
        print(f"生成的无人机位置数量: {len(drone_positions)}")
        print(f"POI覆盖率: {info['poi_coverage']*100:.2f}%")
        print(f"区域覆盖率: {info['area_coverage']*100:.2f}%")
        print(f"海拔惩罚: {info['elevation_penalty']:.4f}")
        
        # 可视化
        print("生成测试可视化...")
        visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, "test_visualization.png", info)
        
        # 再次显示输出路径
        print("可视化结果已保存到: test_visualization.png")
        
    except Exception as e:
        import traceback
        print(f"测试过程中出错: {e}")
        traceback.print_exc()
    
    print("可视化测试完成!") 