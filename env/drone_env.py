import os
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
import gymnasium as gym
from gymnasium import spaces
import rasterio
from rasterio.warp import transform
from rasterio.transform import Affine
from pyproj import Transformer

class DroneEnvironment(gym.Env):
    """
    无人机库选址环境
    """
    
    def __init__(self, config):
        """
        初始化环境
        
        参数:
            config: 配置类实例
        """
        super(DroneEnvironment, self).__init__()
        
        self.config = config
        self.drone_num = config.DRONE_NUM
        self.drone_radius = config.DRONE_RADIUS
        self.elevation_threshold = config.ELEVATION_THRESHOLD
        self.elevation_penalty_weight = config.ELEVATION_PENALTY_WEIGHT
        
        # 加载区域边界数据 (GCJ-02坐标系)
        print(f"加载区域数据: {config.REGION_FILE}")
        self.region_gdf = gpd.read_file(config.REGION_FILE)
        self.region_geometry = self.region_gdf.geometry.iloc[0]
        
        # 获取区域边界的坐标范围
        self.bounds = self.region_geometry.bounds  # (min_x, min_y, max_x, max_y)
        print(f"区域边界: {self.bounds}")
        
        # 加载POI数据 (GCJ-02坐标系)
        print(f"加载POI数据: {config.POI_FILE}")
        self.poi_df = pd.read_csv(config.POI_FILE)
        self.poi_gdf = gpd.GeoDataFrame(
            self.poi_df, 
            geometry=gpd.points_from_xy(self.poi_df.longitude, self.poi_df.latitude),
            crs="EPSG:4326"  # 假设为WGS84，但实际数据为GCJ-02
        )
        print(f"加载POI点数量: {len(self.poi_gdf)}")
        
        # 加载DEM数据
        print(f"加载DEM数据: {config.DEM_FILE}")
        try:
            self.dem_data = rasterio.open(config.DEM_FILE)
            print(f"DEM数据加载成功，形状: {self.dem_data.shape}, CRS: {self.dem_data.crs}")
            
            # 创建坐标转换器 (GCJ-02 -> EPSG:4326，因为DEM通常是WGS84)
            self.transformer = Transformer.from_crs("EPSG:4326", self.dem_data.crs.to_string(), always_xy=True)
        except Exception as e:
            print(f"加载DEM数据失败: {e}")
            self.dem_data = None
            self.transformer = None
        
        # 初始化动作空间和观察空间
        # 动作空间: 8个无人机库的坐标 (每个库2个坐标值)
        self.action_space = spaces.Box(
            low=np.array([self.bounds[0], self.bounds[1]] * self.drone_num),
            high=np.array([self.bounds[2], self.bounds[3]] * self.drone_num),
            shape=(self.drone_num * 2,),
            dtype=np.float32
        )
        
        # 观察空间: 当前所有无人机库的坐标 (每个库2个坐标值)
        self.observation_space = spaces.Box(
            low=np.array([self.bounds[0], self.bounds[1]] * self.drone_num),
            high=np.array([self.bounds[2], self.bounds[3]] * self.drone_num),
            shape=(self.drone_num * 2,),
            dtype=np.float32
        )
        
        # 初始化状态
        self.state = None
        self.current_step = 0
        self.max_steps = 100  # 每个回合最大步数
        
        print(f"环境初始化完成，无人机数量: {self.drone_num}, 无人机覆盖半径: {self.drone_radius}米")
        
    def reset(self, seed=None, options=None):
        """
        重置环境
        
        返回:
            observation: 初始状态
            info: 额外信息
        """
        super().reset(seed=seed)
        
        if seed is not None:
            np.random.seed(seed)
        
        # 随机初始化无人机库位置 (确保在区域内)
        positions = self._generate_random_positions()
        
        # 验证生成的位置
        positions_2d = positions.reshape(-1, 2)
        print(f"重置环境，生成{len(positions_2d)}个无人机位置")
        in_region_count = 0
        for i, pos in enumerate(positions_2d):
            point = Point(pos[0], pos[1])
            if self.region_geometry.contains(point):
                in_region_count += 1
                print(f"  无人机 {i+1}: 经度={pos[0]:.6f}, 纬度={pos[1]:.6f} (在区域内)")
            else:
                print(f"  无人机 {i+1}: 经度={pos[0]:.6f}, 纬度={pos[1]:.6f} (在区域外!)")
        
        if in_region_count < self.drone_num:
            print(f"警告: 只有{in_region_count}/{self.drone_num}个无人机在区域内")
        
        self.state = positions
        self.current_step = 0
        
        info = {}
        return self.state, info
    
    def step(self, action):
        """
        执行一步动作
        
        参数:
            action: 更新后的无人机库位置坐标
            
        返回:
            observation: 新的状态
            reward: 奖励值
            terminated: 是否结束
            truncated: 是否截断
            info: 额外信息
        """
        self.current_step += 1
        
        # 将当前状态和动作重塑为n个无人机的坐标
        action_reshaped = action.reshape(-1, 2)
        current_state = self.state.reshape(-1, 2)
        
        # 探索参数
        exploration_noise = max(0.1, 0.5 * (1 - self.current_step / self.max_steps))  # 递减的探索噪声
        step_size = 0.005  # 每步动作的最大变化幅度（经纬度单位）
        
        # 创建新的状态数组，用于增量更新
        new_state = np.copy(current_state)
        
        # 修改后的主动分散逻辑
        for i in range(len(new_state)):
            for j in range(i):
                if np.linalg.norm(new_state[i] - new_state[j]) < 0.001:
                    # 添加扰动
                    new_state[i, 0] += np.random.uniform(-0.01, 0.01)
                    new_state[i, 1] += np.random.uniform(-0.01, 0.01)
                    
                    # ✅ 强制裁剪（使用 np.clip 的精确计算）
                    new_state[i, 0] = np.clip(
                        new_state[i, 0], 
                        np.float32(self.bounds[0]),  # 保持数据类型一致
                        np.float32(self.bounds[2])
                    )
                    new_state[i, 1] = np.clip(
                        new_state[i, 1],
                        np.float32(self.bounds[1]),
                        np.float32(self.bounds[3])
                    )
                    break
        
        # 将处理后的状态重新展平
        self.state = new_state.flatten()
        
        # 检查是否所有点都有效
        valid_positions = 0
        for pos in new_state:
            point = Point(pos[0], pos[1])
            if self.region_geometry.contains(point):
                valid_positions += 1
        
        if valid_positions == 0:
            print("严重警告: 所有无人机点都在区域外，重新生成随机点")
            self.state = self._generate_random_positions()
        
        # 计算奖励
        reward, info = self._compute_reward()
        
        # 判断是否结束
        terminated = False
        truncated = self.current_step >= self.max_steps
        
        return self.state, reward, terminated, truncated, info
    
    def _generate_random_positions(self):
        """
        生成随机的无人机库位置 (确保在区域内)
        
        返回:
            positions: 无人机库位置坐标数组
        """
        positions = []
        min_distance_degree = self.drone_radius / 111000 * 0.2  # 最小距离为无人机半径的20%，转为度
        
        # 获取区域内的随机点的备选方法
        def get_random_point_in_region(max_attempts=100):
            # 方法1: 边界框采样
            for _ in range(max_attempts):
                x = np.random.uniform(self.bounds[0], self.bounds[2])
                y = np.random.uniform(self.bounds[1], self.bounds[3])
                point = Point(x, y)
                if self.region_geometry.contains(point):
                    return [x, y]
                
            # 方法2: 如果方法1失败，使用区域质心，并添加小扰动
            centroid = self.region_geometry.centroid
            return [
                centroid.x + np.random.uniform(-0.01, 0.01),
                centroid.y + np.random.uniform(-0.01, 0.01)
            ]
        
        # 确保空间足够放置所有无人机
        region_area = self.region_geometry.area
        min_area_needed = self.drone_num * (np.pi * min_distance_degree**2)
        if region_area < min_area_needed:
            print(f"警告: 区域面积({region_area:.6f})可能不足以放置{self.drone_num}个无人机(最小所需面积:{min_area_needed:.6f})")
            # 降低最小距离要求
            min_distance_degree *= 0.5
            print(f"降低最小距离要求为: {min_distance_degree * 111000:.0f}米")
        
        # 尝试生成无人机位置
        max_placement_attempts = 30  # 每个无人机的最大尝试次数
        print(f"开始生成{self.drone_num}个无人机位置，最小间距: {min_distance_degree * 111000:.0f}米")
        
        for i in range(self.drone_num):
            point_added = False
            attempts = 0
            
            while not point_added and attempts < max_placement_attempts:
                # 获取随机点
                candidate = get_random_point_in_region()
                
                # 检查与现有点的最小距离
                too_close = False
                for j in range(0, len(positions), 2):
                    distance = np.sqrt(
                        (candidate[0] - positions[j])**2 + 
                        (candidate[1] - positions[j+1])**2
                    )
                    if distance < min_distance_degree:
                        too_close = True
                        break
                
                if not too_close:
                    positions.extend(candidate)
                    point_added = True
                    print(f"  成功放置无人机 {i+1}: 经度={candidate[0]:.6f}, 纬度={candidate[1]:.6f}")
                
                attempts += 1
            
            # 如果经过多次尝试还是没有成功，就忽略最小距离限制
            if not point_added:
                print(f"警告: 无人机 {i+1} 无法满足最小距离要求，忽略距离限制")
                candidate = get_random_point_in_region()
                positions.extend(candidate)
                print(f"  放置无人机 {i+1}: 经度={candidate[0]:.6f}, 纬度={candidate[1]:.6f}")
        
        print(f"成功生成{len(positions)//2}个无人机位置")
        return np.array(positions, dtype=np.float32)
    
    def _get_elevation(self, lon, lat):
        """
        获取指定经纬度的海拔高度
        
        参数:
            lon: 经度 (GCJ-02)
            lat: 纬度 (GCJ-02)
            
        返回:
            elevation: 海拔高度 (米)，如果无法获取则返回0
        """
        if self.dem_data is None:
            return 0
        
        try:
            # 转换坐标 (GCJ-02 -> DEM的坐标系统)
            x, y = self.transformer.transform(lon, lat)
            
            # 将坐标转换为像素索引
            row, col = self.dem_data.index(x, y)
            
            # 读取高程值
            if 0 <= row < self.dem_data.height and 0 <= col < self.dem_data.width:
                elevation = self.dem_data.read(1)[row, col]
                # 检查是否为NODATA
                if elevation == self.dem_data.nodata:
                    return 0
                return float(elevation)
            else:
                return 0
        except Exception as e:
            print(f"获取海拔高度时出错: {e}")
            return 0
    
    def _compute_reward(self):
        """
        计算奖励
        
        返回:
            reward: 奖励值
            info: 额外信息，包含覆盖率等
        """
        # 重塑状态为无人机库坐标列表
        drone_positions = self.state.reshape(-1, 2)
        
        # 构建无人机库的点
        drone_points = []
        # 存储无人机海拔高度
        drone_elevations = []
        
        for pos in drone_positions:
            point = Point(pos[0], pos[1])
            drone_points.append(point)
            # 获取无人机位置的海拔高度
            elevation = self._get_elevation(pos[0], pos[1])
            drone_elevations.append(elevation)
        
        try:
            # 检查无人机库是否都在区域内
            for i, point in enumerate(drone_points):
                if not self.region_geometry.contains(point):
                    print(f"警告: 无人机 {i+1} 不在区域边界内，坐标: {point.x}, {point.y}")
                    print(f"  区域边界: {self.bounds}")
            
            # 计算每个无人机库的覆盖范围 (buffer) - 注意单位转换
            # GCJ-02坐标是经纬度，约1度=111km，所以需要将米转为度
            drone_radius_degree = self.drone_radius / 111000  # 转换为度
            drone_buffers = [point.buffer(drone_radius_degree) for point in drone_points]
            
            # 合并所有覆盖范围
            merged_buffer = None
            if drone_buffers:
                merged_buffer = drone_buffers[0]
                for buffer in drone_buffers[1:]:
                    merged_buffer = merged_buffer.union(buffer)
            
            # 计算覆盖重叠度
            overlap_area = 0
            for i in range(len(drone_buffers)):
                for j in range(i + 1, len(drone_buffers)):
                    try:
                        intersection = drone_buffers[i].intersection(drone_buffers[j])
                        if not intersection.is_empty:
                            overlap_area += intersection.area
                    except Exception as e:
                        print(f"计算重叠区域时出错: {e}")
            
            # 计算与行政区域的交集面积
            region_area = self.region_geometry.area
            coverage_area = 0
            
            if merged_buffer and region_area > 0:
                try:
                    if isinstance(merged_buffer, MultiPolygon):
                        coverage_area = sum(
                            p.intersection(self.region_geometry).area 
                            for p in merged_buffer.geoms 
                            if not p.is_empty
                        )
                    else:
                        intersection = merged_buffer.intersection(self.region_geometry)
                        if not intersection.is_empty:
                            coverage_area = intersection.area
                except Exception as e:
                    print(f"计算有效覆盖区域时出错: {e}")
            
            # 计算覆盖率
            coverage_ratio = coverage_area / region_area if region_area > 0 else 0
            
            # 计算POI覆盖率
            poi_covered = 0
            for _, poi in self.poi_gdf.iterrows():
                poi_point = poi.geometry
                for buffer in drone_buffers:
                    try:
                        if buffer.contains(poi_point):
                            poi_covered += 1
                            break
                    except Exception as e:
                        print(f"计算POI覆盖时出错: {e}")
            
            poi_coverage_ratio = poi_covered / len(self.poi_gdf) if len(self.poi_gdf) > 0 else 0
            
            # 计算海拔惩罚
            elevation_penalty = 0
            for elevation in drone_elevations:
                if elevation > self.elevation_threshold:
                    # 超过阈值，惩罚正比于超出部分
                    elevation_penalty += (elevation - self.elevation_threshold) / 100  # 缩放系数
            
            # 计算奖励值 (根据覆盖率、重叠度和海拔惩罚)
            normalized_overlap = (overlap_area / region_area) if region_area > 0 else 0
            
            # 防止奖励值过大或过小
            poi_term = poi_coverage_ratio * 1
            area_term = coverage_ratio * 0.3
            overlap_term = normalized_overlap * 0.1
            elevation_term = elevation_penalty * self.elevation_penalty_weight
            
            # 确保各项值在合理范围内
            if np.isnan(poi_term) or np.isinf(poi_term):
                print(f"警告: POI覆盖率计算异常: {poi_coverage_ratio}")
                poi_term = 0
            
            if np.isnan(area_term) or np.isinf(area_term):
                print(f"警告: 区域覆盖率计算异常: {coverage_ratio}")
                area_term = 0
            
            if np.isnan(overlap_term) or np.isinf(overlap_term):
                print(f"警告: 重叠度计算异常: {normalized_overlap}")
                overlap_term = 0
                
            if np.isnan(elevation_term) or np.isinf(elevation_term):
                print(f"警告: 海拔惩罚计算异常: {elevation_penalty}")
                elevation_term = 0
            
            reward = poi_term + area_term - overlap_term - elevation_term
            
            # 添加额外检查，确保奖励值在合理范围内
            if np.isnan(reward) or np.isinf(reward):
                print(f"警告: 奖励值计算异常: {reward}，使用默认值0")
                reward = 0
        
        except Exception as e:
            print(f"计算奖励时发生严重错误: {e}")
            reward = -10  # 出错时给予负面奖励
            poi_coverage_ratio = 0
            coverage_ratio = 0
            normalized_overlap = 0
            poi_covered = 0
            elevation_penalty = 0
            drone_elevations = [0] * len(drone_positions)
        
        info = {
            'poi_coverage': poi_coverage_ratio,
            'area_coverage': coverage_ratio,
            'overlap_ratio': normalized_overlap,
            'poi_covered': poi_covered,
            'total_poi': len(self.poi_gdf),
            'drone_positions': drone_positions,
            'drone_buffers': drone_buffers if 'drone_buffers' in locals() else None,
            'merged_buffer': merged_buffer if 'merged_buffer' in locals() else None,
            'drone_elevations': drone_elevations if 'drone_elevations' in locals() else [0] * len(drone_positions),
            'elevation_penalty': elevation_penalty if 'elevation_penalty' in locals() else 0
        }
        
        return reward, info
    
    def render(self):
        """
        渲染环境 (用于可视化)
        """
        pass  # 渲染功能在view.py中实现 