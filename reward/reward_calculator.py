import numpy as np
from shapely.geometry import Point, MultiPolygon
import geopandas as gpd

class RewardCalculator:
    """
    奖励计算器，用于计算无人机覆盖的奖励
    """
    
    def __init__(self, config):
        """
        初始化奖励计算器
        
        参数:
            config: 配置类实例
        """
        self.config = config
        self.drone_radius = config.DRONE_RADIUS
        
        # 权重配置
        self.poi_weight = 0.7  # POI覆盖率权重
        self.area_weight = 0.3  # 区域覆盖率权重
        self.overlap_penalty = 0.5  # 重叠惩罚系数
        
    def calculate(self, drone_positions, region_geometry, poi_gdf):
        """
        计算奖励
        
        参数:
            drone_positions: 无人机库位置坐标列表
            region_geometry: 区域几何形状
            poi_gdf: POI的GeoDataFrame
            
        返回:
            reward: 奖励值
            info: 额外信息，包含覆盖率等
        """
        # 构建无人机库的点
        drone_points = [Point(pos[0], pos[1]) for pos in drone_positions]
        
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
        region_area = region_geometry.area
        if isinstance(merged_buffer, MultiPolygon):
            coverage_area = sum(
                p.intersection(region_geometry).area 
                for p in merged_buffer.geoms 
                if not p.is_empty
            )
        else:
            coverage_area = merged_buffer.intersection(region_geometry).area
        
        # 计算覆盖率
        coverage_ratio = coverage_area / region_area
        
        # 计算POI覆盖率
        poi_covered = 0
        for idx, poi in poi_gdf.iterrows():
            poi_point = poi.geometry
            for buffer in drone_buffers:
                if buffer.contains(poi_point):
                    poi_covered += 1
                    break
        
        poi_coverage_ratio = poi_covered / len(poi_gdf)
        
        # 计算奖励值
        reward = (
            poi_coverage_ratio * self.poi_weight +
            coverage_ratio * self.area_weight -
            (overlap_area / region_area) * self.overlap_penalty
        )
        
        # 每个无人机库单独的奖励
        drone_rewards = []
        for i, buffer in enumerate(drone_buffers):
            # 计算单个无人机的POI覆盖
            poi_covered_single = 0
            for idx, poi in poi_gdf.iterrows():
                if buffer.contains(poi.geometry):
                    poi_covered_single += 1
            
            # 计算单个无人机的区域覆盖
            area_covered_single = buffer.intersection(region_geometry).area
            
            # 计算与其他无人机的重叠
            overlap_single = 0
            for j, other_buffer in enumerate(drone_buffers):
                if i != j:
                    overlap_single += buffer.intersection(other_buffer).area
            
            # 单个无人机的奖励
            drone_reward = (
                (poi_covered_single / len(poi_gdf)) * self.poi_weight +
                (area_covered_single / region_area) * self.area_weight -
                (overlap_single / region_area) * self.overlap_penalty
            )
            
            drone_rewards.append(drone_reward)
        
        info = {
            'poi_coverage': poi_coverage_ratio,
            'area_coverage': coverage_ratio,
            'overlap_ratio': overlap_area / region_area,
            'poi_covered': poi_covered,
            'total_poi': len(poi_gdf),
            'drone_rewards': drone_rewards,
            'merged_buffer': merged_buffer,
            'drone_buffers': drone_buffers
        }
        
        return reward, info 