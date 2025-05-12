import geopandas as gpd
from shapely.geometry import Point, MultiPolygon
import pyproj
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely.geometry import Point, MultiPolygon, Polygon
import os
import time

坐标系和运算全部维持在GCJ-02
def calculate_area_coverage(region_geojson_path, 
                           points, 
                           drone_radius_meter, 
                           utm_zone=51):
    """
    计算无人机点位的地理覆盖率
    
    参数：
    region_geojson_path: str - 区域边界GeoJSON文件路径

    drone_radius_meter: float - 无人机覆盖半径（米）
    
    返回：
    coverage_ratio: float - 覆盖率百分比
    covered_area: float - 覆盖面积(平方公里)
    """
    
    
    # 4. 生成缓冲区（确保在UTM坐标系下）
    buffers = []
    for point in points_utm.geometry:
        buffers.append(point.buffer(drone_radius_meter))
    
    # 5. 合并缓冲区
    merged_buffer = gpd.GeoSeries(buffers).union_all()
    
    # 6. 计算覆盖区域（与行政区域的交集）
    if isinstance(merged_buffer, MultiPolygon):
    # 修正：对每个子多边形单独取交集后再求和
        coverage_area = sum(
            p.intersection(region_utm).area 
            for p in merged_buffer.geoms
            if not p.is_empty
        )
    else:
        coverage_area = merged_buffer.intersection(region_utm).area

    # # 验证行政区域面积（调试用）
    # print(f"行政区域面积: {region_utm.area/1e6:.2f} km²")  # 应为≈1821km²

    # 7. 计算覆盖率
  
    
    

    