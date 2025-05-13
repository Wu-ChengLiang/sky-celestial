import React, { useRef, useEffect, useState } from 'react';
import useEarth from '@/hooks/useEarth';
import styles from '@/styles/Earth.module.css';

interface EarthCoreProps {
  className?: string;
}

const EarthCore: React.FC<EarthCoreProps> = ({ className }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollPosition, setScrollPosition] = useState(0);
  
  // 直接在组件顶层调用hook
  const { loading, error, updateScroll } = useEarth(containerRef);
  
  // 监听滚动事件
  useEffect(() => {
    const handleScroll = () => {
      const position = window.scrollY;
      const height = document.body.scrollHeight - window.innerHeight;
      const scrollPercent = Math.min(position / (height * 0.7), 1);
      
      setScrollPosition(scrollPercent);
      if (typeof updateScroll === 'function') {
        updateScroll(scrollPercent);
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [updateScroll]);
  
  return (
    <div className={`${styles.earthContainer} ${className || ''}`} ref={containerRef}>
      {loading && (
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p>加载地球中...</p>
        </div>
      )}
      
      {error && (
        <div className={styles.errorContainer}>
          <p>加载失败: {error}</p>
          <button onClick={() => window.location.reload()}>重试</button>
        </div>
      )}
    </div>
  );
};

export default EarthCore; 