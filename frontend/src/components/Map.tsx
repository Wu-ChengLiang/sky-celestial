import React, { useEffect, useRef, useState } from 'react';
import styles from '@/styles/Map.module.css';
import dynamic from 'next/dynamic';

// 动态导入Leaflet地图组件，避免服务端渲染问题
const LeafletMap = dynamic(
  () => import('@/components/LeafletMap'),
  { 
    ssr: false,
    loading: () => (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}></div>
        <p>加载地图中...</p>
      </div>
    )
  }
);

// 地图主组件
const Map: React.FC<{ className?: string }> = ({ className }) => {
  const [mapVisible, setMapVisible] = useState(false);
  const [shouldRenderMap, setShouldRenderMap] = useState(false);
  const mapRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // 监听滚动以控制地图展示
    const handleScroll = () => {
      if (!mapRef.current) return;
      
      const mapPosition = mapRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      
      // 当地图进入视口时显示
      if (mapPosition.top < windowHeight * 0.8 && mapPosition.bottom > 0) {
        setMapVisible(true);
        // 延迟加载Leaflet地图组件
        if (!shouldRenderMap) {
          setShouldRenderMap(true);
        }
      }
    };
    
    // 初始检查
    handleScroll();
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [shouldRenderMap]);
  
  return (
    <div 
      ref={mapRef} 
      className={`${styles.mapContainer} ${className || ''} ${mapVisible ? styles.visible : ''}`}
    >
      <div className={styles.mapTitle}>富阳区村委会分布图</div>
      
      {shouldRenderMap && <LeafletMap />}
      
      <div className={styles.mapDescription}>
        <p>通过POI点密度分析，优化选址算法</p>
        <p>92% 覆盖率 | 8 个无人机库 | 8km 服务半径</p>
      </div>
    </div>
  );
};

export default Map; 