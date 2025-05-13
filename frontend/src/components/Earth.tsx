import React, { useEffect, useState } from 'react';
import styles from '@/styles/Earth.module.css';
import dynamic from 'next/dynamic';

// 为earth状态定义合适的接口
interface EarthState {
  loading: boolean;
  error: string | null;
  updateScroll: (scrollPos: number) => void;
}

// 动态导入地球核心组件，避免服务端渲染
// 使用类型断言来解决类型问题
const EarthCore = dynamic(() => import('@/components/EarthCore'), { 
  ssr: false,
  loading: () => (
    <div className={styles.loadingContainer}>
      <div className={styles.loadingSpinner}></div>
      <p>加载地球组件中...</p>
    </div>
  )
}) as React.ComponentType<{ className?: string }>;

// 主地球组件，附带水墨流效果
const Earth: React.FC<{ className?: string }> = ({ className }) => {
  const [showWaterFlow, setShowWaterFlow] = useState(false);
  
  useEffect(() => {
    // 监听滚动以控制水墨流展示
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const threshold = window.innerHeight * 0.5;
      
      if (scrollY > threshold) {
        setShowWaterFlow(true);
      } else {
        setShowWaterFlow(false);
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);
  
  return (
    <div className={styles.earthWrapper}>
      <EarthCore className={`${styles.earth} ${className || ''}`} />
      
      {/* 水墨流效果 (当滚动到一定位置显示) */}
      <div className={`${styles.waterFlow} ${showWaterFlow ? styles.visible : ''}`}>
        <div className={styles.waterFlowInner}></div>
      </div>
    </div>
  );
};

export default Earth; 

