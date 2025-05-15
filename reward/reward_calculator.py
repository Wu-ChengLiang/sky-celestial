import numpy as np
from shapely.geometry import Point, MultiPolygon
import geopandas as gpd
import rasterio
from pyproj import Transformer

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
        self.poi_weight = 0.1  # POI覆盖率权重
        self.area_weight = 0.1  # 区域覆盖率权重
        self.overlap_penalty = 0.1  # 重叠惩罚系数
        
        # 海拔相关配置
        self.elevation_threshold = config.ELEVATION_THRESHOLD  # 海拔阈值
        self.elevation_penalty_weight = config.ELEVATION_PENALTY_WEIGHT  # 海拔惩罚权重
        
        # 加载DEM数据
        try:
            self.dem_data = rasterio.open(config.DEM_FILE)
            # 创建坐标转换器 (GCJ-02 -> EPSG:4326，因为DEM通常是WGS84)
            self.transformer = Transformer.from_crs("EPSG:4326", self.dem_data.crs.to_string(), always_xy=True)
        except Exception as e:
            print(f"加载DEM数据失败: {e}")
            self.dem_data = None
            self.transformer = None
    
    def get_elevation(self, lon, lat):
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
        
        # 获取每个点的海拔高度
        drone_elevations = []
        for pos in drone_positions:
            elevation = self.get_elevation(pos[0], pos[1])
            drone_elevations.append(elevation)
        
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
        
        # 计算海拔惩罚
        elevation_penalty = 0
        for elevation in drone_elevations:
            if elevation > self.elevation_threshold:
                # 超过阈值，惩罚正比于超出部分
                elevation_penalty += (elevation - self.elevation_threshold) / 100  # 缩放系数
        
        # 计算奖励值
        reward = (
            poi_coverage_ratio * self.poi_weight +
            coverage_ratio * self.area_weight -
            (overlap_area / region_area) * self.overlap_penalty -
            elevation_penalty * self.elevation_penalty_weight
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
            
            # 获取该无人机的海拔惩罚
            elev_penalty_single = 0
            if drone_elevations[i] > self.elevation_threshold:
                elev_penalty_single = (drone_elevations[i] - self.elevation_threshold) / 100
            
            # 单个无人机的奖励
            drone_reward = (
                (poi_covered_single / len(poi_gdf)) * self.poi_weight +
                (area_covered_single / region_area) * self.area_weight -
                (overlap_single / region_area) * self.overlap_penalty -
                elev_penalty_single * self.elevation_penalty_weight
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
            'drone_buffers': drone_buffers,
            'drone_elevations': drone_elevations,
            'elevation_penalty': elevation_penalty
        }
        
        return reward, info 