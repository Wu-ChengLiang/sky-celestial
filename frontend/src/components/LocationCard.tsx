import React, { useState } from 'react';
import Image from 'next/image';
import styles from '@/styles/LocationCard.module.css';

interface LocationCardProps {
  index: number;
  imageUrl: string;
  coverage: string;
  siteName: string;
  description?: string;
  className?: string;
}

const LocationCard: React.FC<LocationCardProps> = ({
  index,
  imageUrl,
  coverage,
  siteName,
  description = '基于POI点密度分析与强化学习优化的选址方案',
  className,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  
  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };

  return (
    <div 
      className={`${styles.card} ${className || ''} ${showDetails ? styles.expanded : ''}`}
      onClick={toggleDetails}
    >
      <div className={styles.preview}>
        <Image
          src={imageUrl}
          alt={`选址方案 #${index + 1}`}
          width={500}
          height={300}
          layout="responsive"
          className={styles.image}
        />
        <div className={styles.coverageTag}>{coverage}</div>
        <div className={styles.indexTag}>#{index + 1}</div>
      </div>
      
      <div className={styles.content}>
        <h3>{siteName}</h3>
        <p className={styles.description}>{description}</p>
        
        {showDetails && (
          <div className={styles.details}>
            <div className={styles.detail}>
              <span className={styles.detailLabel}>服务半径</span>
              <span className={styles.detailValue}>8km</span>
            </div>
            <div className={styles.detail}>
              <span className={styles.detailLabel}>POI覆盖率</span>
              <span className={styles.detailValue}>{coverage}</span>
            </div>
            <div className={styles.detail}>
              <span className={styles.detailLabel}>站点类型</span>
              <span className={styles.detailValue}>无人机停放与充电站</span>
            </div>
            <div className={styles.detail}>
              <span className={styles.detailLabel}>建设成本</span>
              <span className={styles.detailValue}>中等</span>
            </div>
            <button className={styles.viewButton}>
              在地图中查看
            </button>
          </div>
        )}
      </div>
      
      <div className={styles.cardFooter}>
        <span className={styles.viewMore}>
          {showDetails ? '点击关闭' : '点击查看详情'}
        </span>
      </div>
    </div>
  );
};

export default LocationCard; 