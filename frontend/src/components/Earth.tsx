import React, { useRef, useEffect, useState } from 'react';
import styles from '@/styles/Earth.module.css';
import dynamic from 'next/dynamic';
import Image from 'next/image';

// 为earth状态定义合适的接口
interface EarthState {
  loading: boolean;
  error: string | null;
  updateScroll: (scrollPos: number) => void;
}

// 动态导入useEarth hook，以避免在服务端渲染时加载Three.js
const EarthContainer = dynamic(() => Promise.resolve(({ className }: { className?: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollPosition, setScrollPosition] = useState(0);
  const [earthLoaded, setEarthLoaded] = useState(false);
  // 预先定义状态变量，使用正确的类型定义
  const [earth, setEarth] = useState<EarthState>({ 
    loading: true, 
    error: null, 
    updateScroll: (scrollPos: number) => {} 
  });
  
  useEffect(() => {
    // 只在客户端导入useEarth hook
    const loadEarthHook = async () => {
      try {
        const module = await import('@/hooks/useEarth');
        const hookFn = module.default;
        // 安全地调用hook并更新状态
        if (hookFn && containerRef.current) {
         c
          setEarth(earthInstance);
          // 设置初始加载状态
          setEarthLoaded(!earthInstance.loading);
        }
      } catch (error) {
        console.error("加载地球Hook失败:", error);
        setEarth(prev => ({ 
          ...prev, 
          error: "加载地球Hook失败" 
        }));
      }
    };
    
    loadEarthHook();
  }, []);
  
  useEffect(() => {
    // 监听滚动事件
    const handleScroll = () => {
      const position = window.scrollY;
      const height = document.body.scrollHeight - window.innerHeight;
      const scrollPercent = Math.min(position / (height * 0.7), 1);
      
      setScrollPosition(scrollPercent);
      // 安全地调用updateScroll
      if (earth && typeof earth.updateScroll === 'function') {
        earth.updateScroll(scrollPercent);
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [earth]); // 依赖于earth对象
  
  return (
    <div className={`${styles.earthContainer} ${className}`} ref={containerRef}>
      {earth.loading && !earthLoaded && (
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p>加载地球中...</p>
        </div>
      )}
      
      {earth.error && (
        <div className={styles.errorContainer}>
          <p>加载失败: {earth.error}</p>
          <button onClick={() => window.location.reload()}>重试</button>
        </div>
      )}
    </div>
  );
}), { ssr: false });

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
      <EarthContainer className={`${styles.earth} ${className || ''}`} />
      
      {/* 水墨流效果 (当滚动到一定位置显示) */}
      <div className={`${styles.waterFlow} ${showWaterFlow ? styles.visible : ''}`}>
        <div className={styles.waterFlowInner}></div>
      </div>
    </div>
  );
};

export default Earth; 

