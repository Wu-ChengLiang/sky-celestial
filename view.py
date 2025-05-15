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
    # 创建画布，使用更大的尺寸以提高清晰度
    fig, ax = plt.subplots(figsize=(14, 12), dpi=100)
    
    # 设置中文字体
    import os
    import matplotlib
    
    # 确保字体编码正确
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    
    # 设置中文字体，优先使用系统字体
    if os.name == 'nt':  # Windows系统
        font_list = ['SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong', 'KaiTi']
    else:  # Linux/Mac系统
        font_list = ['WenQuanYi Zen Hei', 'Hiragino Sans GB', 'Heiti SC', 'STHeiti', 'Source Han Sans CN']
    
    plt.rcParams['font.sans-serif'] = font_list
    plt.rcParams['axes.unicode_minus'] = False
    
    # 中文显示问题  若非win，请自行配置
    try:
        from matplotlib.font_manager import fontManager
        # 根据操作系统选择合适的字体路径
        if os.name == 'nt':  # Windows系统
            font_paths = ['C:\\Windows\\Fonts\\simhei.ttf', 'C:\\Windows\\Fonts\\msyh.ttc']
            for path in font_paths:
                if os.path.exists(path):
                    fontManager.addfont(path)
                    break
    except Exception as e:
        print(f"加载字体时出错: {e}")
        # 回退方案：使用matplotlib内置的字体
        plt.rcParams['font.family'] = 'sans-serif'
    
    # 设置更现代的风格
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # 转换无人机覆盖半径(米)为经纬度
    drone_radius_degree = drone_radius / 111000  # 转为度
    
    # 先绘制行政区域作为底图，使用更淡的颜色
    gpd.GeoSeries([region_geometry]).plot(ax=ax, color='#E6F3FF', edgecolor='#6BAED6', alpha=0.2, linewidth=0.8)
    
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
                scale_factor = 8  # 减少8倍数据点，提高精度
                # 设置zorder为1，确保DEM在底层显示
                dem_plot = ax.pcolormesh(
                    xs[::scale_factor], 
                    ys[::scale_factor], 
                    dem_data[::scale_factor, ::scale_factor],
                    cmap=cmap, 
                    vmin=vmin, 
                    vmax=vmax, 
                    alpha=0.5,
                    zorder=1  # 设置较低的zorder确保在底层
                )
                
                # 添加色条，使用更现代的样式，调整位置和大小避免与经度标签重叠
                cbar = plt.colorbar(dem_plot, ax=ax, label='海拔 (米)', shrink=0.35, pad=0.08, 
                                   location='bottom', orientation='horizontal')
                
                # 调整色条标签字体大小，确保中文显示正常
                cbar.ax.set_xlabel('海拔 (米)', fontsize=10, fontproperties='SimHei')
                cbar.ax.tick_params(labelsize=9)
                
                # 设置绘图区域范围与行政区域一致
                ax.set_xlim(bounds[0], bounds[2])
                ax.set_ylim(bounds[1], bounds[3])
                
                dem_shown = True
                print(f"DEM显示成功，数据范围: {vmin}-{vmax}米")
        except Exception as e:
            print(f"绘制DEM数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 如果DEM绘制成功，增强行政区域边界的可见性，使用更精致的样式
    if dem_shown:
        # 使用更细腻的线条和更现代的颜色
        gpd.GeoSeries([region_geometry]).plot(ax=ax, color='none', edgecolor='#3182bd', 
                                           alpha=0.9, linewidth=1.2, zorder=6)
    
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
    
    # 绘制每个无人机覆盖范围，使用更精致的样式和适当的zorder
    for i, buffer in enumerate(buffers):
        # 使用半透明红色，细线条边框
        gpd.GeoSeries([buffer]).plot(ax=ax, color='#ff9999', edgecolor='#e74c3c', 
                                    alpha=0.25, linewidth=0.6, zorder=2)
    
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
                        # 绘制有效覆盖区域，使用更精致的样式
                        gpd.GeoSeries([coverage_poly]).plot(ax=ax, color='#6BAED6', 
                                                          edgecolor='#3182bd', alpha=0.4, 
                                                          linewidth=0.8, zorder=3)
                    except Exception as e:
                        print(f"绘制有效覆盖区域时出错: {e}")
            else:
                try:
                    coverage_poly = merged_buffer.intersection(region_geometry)
                    if not coverage_poly.is_empty:
                        gpd.GeoSeries([coverage_poly]).plot(ax=ax, color='#6BAED6', 
                                                          edgecolor='#3182bd', alpha=0.4, 
                                                          linewidth=0.8, zorder=3)
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
    
    # 绘制低海拔和高海拔的点，使用更专业的样式
    if not low_elevation_points.empty:
        low_elevation_points.plot(ax=ax, color='#2ca02c', markersize=120, marker='o', linewidth=1.5, 
                                 edgecolor='white', zorder=5)
    if not high_elevation_points.empty:
        high_elevation_points.plot(ax=ax, color='#d62728', markersize=120, marker='o', linewidth=1.5, 
                                  edgecolor='white', zorder=5)
    
    # 绘制POI点位，使用更精致的样式
    poi_gdf.plot(ax=ax, color='#9467bd', markersize=25, marker='o', edgecolor='white', linewidth=0.8, 
                alpha=0.8, zorder=4)
    
    # 添加图例，使用更现代的样式
    from matplotlib.font_manager import FontProperties
    font_prop = FontProperties(family='SimHei')
    
    legend_elements = [
        Patch(facecolor='#E6F3FF', edgecolor='#6BAED6', alpha=0.5, label='行政区域'),
        Patch(facecolor='red', alpha=0.3, label='无人机覆盖范围'),
        Patch(facecolor='#6BAED6', alpha=0.5, label='有效覆盖区域'),
        plt.Line2D([], [], color='#2ca02c', marker='o', markeredgecolor='white', linestyle='None', 
                  markersize=8, label=f'无人机点位 (≤{elevation_threshold}米)'),
        plt.Line2D([], [], color='#d62728', marker='o', markeredgecolor='white', linestyle='None', 
                  markersize=8, label=f'无人机点位 (>{elevation_threshold}米)'),
        plt.Line2D([], [], color='#9467bd', marker='o', markeredgecolor='white', linestyle='None', 
                  markersize=6, label='POI点位')
    ]
    # 调整图例位置，避免与其他元素重叠，并设置中文字体
    ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9, edgecolor='#cccccc', 
             bbox_to_anchor=(0.98, 0.98), prop=font_prop)
    
    # 添加标题和信息
    coverage_ratio = info['poi_coverage'] * 100 if info and 'poi_coverage' in info else 0
    area_coverage = info['area_coverage'] * 100 if info and 'area_coverage' in info else 0
    overlap_ratio = info['overlap_ratio'] * 100 if info and 'overlap_ratio' in info else 0
    elevation_penalty = info['elevation_penalty'] if info and 'elevation_penalty' in info else 0
    
    # 设置标题，确保中文正确显示
    plt.title(f'无人机机库选址 (POI覆盖率: {coverage_ratio:.1f}%)', fontsize=14, pad=10, fontproperties='SimHei')
    
    # 添加坐标轴标签，确保中文正确显示
    plt.xlabel('经度', fontsize=12, fontproperties='SimHei')
    plt.ylabel('纬度', fontsize=12, fontproperties='SimHei')
    
    # 调整坐标轴标签位置，避免与图例重叠
    ax.xaxis.set_label_coords(0.5, -0.08)
    
    # 将点的坐标添加为标签，显示海拔信息，使用更精致的样式
    for i, (point, elev) in enumerate(zip(drone_points, drone_elevations)):
        plt.annotate(f"D{i+1}\n{elev:.0f}m", xy=(point.x, point.y), xytext=(7, 7), 
                     textcoords='offset points', fontsize=9, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc", alpha=0.85),
                     zorder=10)
    
    # 添加覆盖信息文本，移到右下角并使用半透明背景，确保不遮挡DEM
    info_text = (
        f'POI覆盖率: {coverage_ratio:.1f}%\n'
        f'区域覆盖率: {area_coverage:.1f}%\n'
        f'重叠率: {overlap_ratio:.1f}%\n'
        f'覆盖POI点数: {info["poi_covered"] if info and "poi_covered" in info else 0}\n'
        f'无人机数量: {len(drone_points)}\n'
        f'海拔惩罚: {elevation_penalty:.4f}'
    )
    plt.annotate(info_text, xy=(0.98, 0.02), xycoords='axes fraction', 
                 xytext=(-10, 10), textcoords='offset points',
                 bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#cccccc", alpha=0.85),
                 ha='right', va='bottom', zorder=20, fontproperties=font_prop)
    
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
    import os
    
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
        
        # 创建输出目录
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "test_visualization.png")
        
        # 可视化
        print("生成测试可视化...")
        visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, output_path, info)
        
        # 再次显示输出路径
        print(f"可视化结果已保存到: {output_path}")
        
    except Exception as e:
        import traceback
        print(f"测试过程中出错: {e}")
        traceback.print_exc()
    
    print("可视化测试完成!")