import os
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
import gymnasium as gym
from gymnasium import spaces

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
        self.state = self._generate_random_positions()
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
        
        # 确保动作在有效范围内
        action = np.clip(
            action,
            [self.bounds[0], self.bounds[1]] * self.drone_num,
            [self.bounds[2], self.bounds[3]] * self.drone_num
        )
        
        # 应用动作，更新无人机库位置
        self.state = action
        
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
        min_distance_degree = self.drone_radius / 111000 * 1.0  # 最小距离为无人机半径的1倍，转为度
        
        for _ in range(self.drone_num):
            valid_position_found = False
            attempts = 0
            max_attempts = 1000
            
            while not valid_position_found and attempts < max_attempts:
                # 在边界范围内随机生成一个点
                x = np.random.uniform(self.bounds[0], self.bounds[2])
                y = np.random.uniform(self.bounds[1], self.bounds[3])
                point = Point(x, y)
                
                # 检查点是否在区域内
                if not self.region_geometry.contains(point):
                    attempts += 1
                    continue
                    
                # 检查是否与现有点保持最小距离
                if positions:  # 如果已经有点了
                    too_close = False
                    for i in range(0, len(positions), 2):
                        existing_x, existing_y = positions[i], positions[i+1]
                        distance = np.sqrt((x - existing_x)**2 + (y - existing_y)**2)
                        if distance < min_distance_degree:
                            too_close = True
                            break
                    
                    if too_close:
                        attempts += 1
                        continue
                
                # 如果通过所有检查，添加这个点
                positions.extend([x, y])
                valid_position_found = True
            
            # 如果尝试次数过多，就在边界内随机取一点
            if not valid_position_found:
                print(f"警告: 为第{len(positions)//2 + 1}个无人机找不到合适位置，使用区域内随机点")
                while True:
                    # 在边界范围内随机生成一个点
                    x = np.random.uniform(self.bounds[0], self.bounds[2])
                    y = np.random.uniform(self.bounds[1], self.bounds[3])
                    point = Point(x, y)
                    
                    # 确保至少在区域内
                    if self.region_geometry.contains(point):
                        positions.extend([x, y])
                        break
        
        print(f"成功生成{len(positions)//2}个无人机位置")
        return np.array(positions, dtype=np.float32)
    
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
        drone_points = [Point(pos[0], pos[1]) for pos in drone_positions]
        
        # 计算每个无人机库的覆盖范围 (buffer) - 注意单位转换
        # GCJ-02坐标是经纬度，约1度=111km，所以需要将米转为度
        drone_radius_degree = self.drone_radius / 111000  # 转换为度
        drone_buffers = [point.buffer(drone_radius_degree) for point in drone_points]
        
        try:
            # 检查无人机库是否都在区域内
            for i, point in enumerate(drone_points):
                if not self.region_geometry.contains(point):
                    print(f"警告: 无人机 {i+1} 不在区域边界内，坐标: {point.x}, {point.y}")
            
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
            
            # 计算奖励值 (根据覆盖率和重叠度)
            normalized_overlap = (overlap_area / region_area) if region_area > 0 else 0
            
            # 防止奖励值过大或过小
            poi_term = poi_coverage_ratio * 0.7
            area_term = coverage_ratio * 0.3
            overlap_term = normalized_overlap * 0.5
            
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
            
            reward = poi_term + area_term - overlap_term
            
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
        
        info = {
            'poi_coverage': poi_coverage_ratio,
            'area_coverage': coverage_ratio,
            'overlap_ratio': normalized_overlap,
            'poi_covered': poi_covered,
            'total_poi': len(self.poi_gdf),
            'drone_positions': drone_positions,
            'drone_buffers': drone_buffers,
            'merged_buffer': merged_buffer if 'merged_buffer' in locals() else None
        }
        
        return reward, info
    
    def render(self):
        """
        渲染环境 (用于可视化)
        """
        pass  # 渲染功能在view.py中实现 