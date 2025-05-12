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
        
        # 加载区域边界数据
        self.region_gdf = gpd.read_file(config.REGION_FILE)
        self.region_geometry = self.region_gdf.geometry.iloc[0]
        
        # 获取区域边界的坐标范围
        self.bounds = self.region_geometry.bounds  # (min_x, min_y, max_x, max_y)
        
        # 加载POI数据
        self.poi_df = pd.read_csv(config.POI_FILE)
        self.poi_gdf = gpd.GeoDataFrame(
            self.poi_df, 
            geometry=gpd.points_from_xy(self.poi_df.longitude, self.poi_df.latitude),
            crs="EPSG:4326"
        )
        
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
        
        for _ in range(self.drone_num):
            while True:
                # 在边界范围内随机生成一个点
                x = np.random.uniform(self.bounds[0], self.bounds[2])
                y = np.random.uniform(self.bounds[1], self.bounds[3])
                point = Point(x, y)
                
                # 检查点是否在区域内
                if self.region_geometry.contains(point):
                    positions.extend([x, y])
                    break
        
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
        
        # 构建无人机库的GeoDataFrame
        drone_points = [Point(pos[0], pos[1]) for pos in drone_positions]
        drone_gdf = gpd.GeoDataFrame(geometry=drone_points)
        
        # 计算每个无人机库的覆盖范围 (buffer)
        drone_buffers = [point.buffer(self.drone_radius) for point in drone_points]
        
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
                intersection = drone_buffers[i].intersection(drone_buffers[j])
                overlap_area += intersection.area
        
        # 计算与行政区域的交集面积
        region_area = self.region_geometry.area
        if isinstance(merged_buffer, MultiPolygon):
            coverage_area = sum(
                p.intersection(self.region_geometry).area 
                for p in merged_buffer.geoms 
                if not p.is_empty
            )
        else:
            coverage_area = merged_buffer.intersection(self.region_geometry).area
        
        # 计算覆盖率
        coverage_ratio = coverage_area / region_area
        
        # 计算POI覆盖率
        poi_covered = 0
        for idx, poi in self.poi_gdf.iterrows():
            poi_point = poi.geometry
            for buffer in drone_buffers:
                if buffer.contains(poi_point):
                    poi_covered += 1
                    break
        
        poi_coverage_ratio = poi_covered / len(self.poi_gdf)
        
        # 计算奖励值 (根据覆盖率和重叠度)
        reward = (
            poi_coverage_ratio * 0.7 +  # POI覆盖率权重0.7
            coverage_ratio * 0.3 -      # 区域覆盖率权重0.3
            (overlap_area / region_area) * 0.5  # 重叠度惩罚
        )
        
        info = {
            'poi_coverage': poi_coverage_ratio,
            'area_coverage': coverage_ratio,
            'overlap_ratio': overlap_area / region_area,
            'poi_covered': poi_covered,
            'total_poi': len(self.poi_gdf)
        }
        
        return reward, info
    
    def render(self):
        """
        渲染环境 (用于可视化)
        """
        pass  # 渲染功能在view.py中实现 