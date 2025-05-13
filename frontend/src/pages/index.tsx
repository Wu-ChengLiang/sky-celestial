import React, { useEffect, useState, useRef } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import styles from '@/styles/Home.module.css';

// 动态导入组件，避免服务器端渲染问题
const Earth = dynamic(() => import('@/components/Earth'), { ssr: false });
const Map = dynamic(() => import('@/components/Map'), { ssr: false });
const LocationCard = dynamic(() => import('@/components/LocationCard'), { ssr: false });

// 站点数据
const sitesData = [
  { coverage: '94%', siteName: '富春江北站点', description: '富春江北岸核心站点，覆盖率最高的区域之一' },
  { coverage: '88%', siteName: '新登镇中心站', description: '连接新登镇周边村落，提供医疗与应急物资配送' },
  { coverage: '92%', siteName: '场口镇农村站', description: '服务偏远地区的无人机配送枢纽' },
  { coverage: '90%', siteName: '永昌西站点', description: '连接西部山区村庄，覆盖人口密度较低区域' },
  { coverage: '89%', siteName: '富阳区中心站', description: '主城区配送中心，支持紧急情况下的应急响应' },
  { coverage: '93%', siteName: '东洲街道站点', description: '城乡结合部的无人机充电与中转站点' },
  { coverage: '91%', siteName: '银湖街道站点', description: '覆盖银湖及周边区域，连接北部区域' },
  { coverage: '94%', siteName: '春江街道站点', description: '提供城南区域的无人机服务，人口覆盖率高' },
  { coverage: '87%', siteName: '大源镇站点', description: '备选站点，可扩展系统覆盖面积' },
  { coverage: '86%', siteName: '渔山站点', description: '备选站点，增强东部山区覆盖能力' },
];

// 加载组件
const LoadingScreen = () => (
  <div className="loading-container">
    <div className="loading-spinner"></div>
    <p>正在加载无人机选址系统...</p>
  </div>
);

// 首页组件
const Home: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [scrollY, setScrollY] = useState(0);
  const locationCardsRef = useRef<HTMLDivElement>(null);

  // 监听滚动
  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    // 设置页面加载完成
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1500);

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(timer);
    };
  }, []);

  // 计算滚动位置的百分比用于动画
  const scrollPercent = typeof window !== 'undefined'
    ? Math.min(scrollY / (document.body.scrollHeight - window.innerHeight), 1)
    : 0;

  // 先渲染所有组件，但根据loading状态决定显示哪个
  return (
    <>
      <Head>
        <title>无人机选址系统 | 基于POI点密度与强化学习</title>
        <meta name="description" content="基于POI点密度分析与强化学习的无人机选址系统" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {loading ? (
        <LoadingScreen />
      ) : (
        <main className={styles.main}>
          {/* 头部英雄区域 */}
          <section className={styles.hero}>
            <Earth />
            <div className={styles.heroContent}>
              <h1 className={styles.title}>无人机选址系统</h1>
              <p className={styles.subtitle}>基于POI点密度分析与强化学习的最优选址方案</p>
              <div className={styles.stats}>
                <div className={styles.stat}>
                  <span className={styles.statNumber}>92%</span>
                  <span className={styles.statLabel}>平均覆盖率</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statNumber}>8</span>
                  <span className={styles.statLabel}>无人机站点</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statNumber}>8km</span>
                  <span className={styles.statLabel}>服务半径</span>
                </div>
              </div>
              <div className={styles.scrollPrompt}>
                <span>向下滚动了解详情</span>
                <svg className={styles.scrollArrow} viewBox="0 0 24 24">
                  <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" />
                </svg>
              </div>
            </div>
          </section>

          {/* 地图组件区域 */}
          <section className={styles.mapSection}>
            <div className={styles.sectionHeader}>
              <h2>富阳区村委会与选址分布</h2>
              <p>通过分析富阳区村委会分布，结合POI点密度，确定最优无人机站点位置</p>
            </div>
            <Map />
          </section>

          {/* 选址卡片区域 */}
          <section className={styles.cardsSection} ref={locationCardsRef}>
            <div className={styles.sectionHeader}>
              <h2>无人机选址方案</h2>
              <p>强化学习算法生成的最优站点方案，点击卡片查看详情</p>
            </div>
            <div className={styles.cardsGrid}>
              {sitesData.map((site, index) => (
                <div key={index} className={styles.cardWrapper}>
                  <LocationCard
                    index={index}
                    imageUrl={`/images/eval_episode_${index + 1}.png`}
                    coverage={site.coverage}
                    siteName={site.siteName}
                    description={site.description}
                  />
                </div>
              ))}
            </div>
          </section>

          {/* 算法说明区域 */}
          <section className={styles.algorithmSection}>
            <div className={styles.sectionHeader}>
              <h2>选址算法与模型</h2>
              <p>通过多智能体强化学习优化无人机站点位置</p>
            </div>
            <div className={styles.algorithmContent}>
              <div className={styles.algorithmCard}>
                <h3>POI点密度分析</h3>
                <p>基于富阳区人口分布和重要设施位置，建立点密度模型</p>
                <ul>
                  <li>收集村委会、医院、学校等重要POI点</li>
                  <li>计算区域密度热力图</li>
                  <li>确定服务需求优先级</li>
                </ul>
              </div>
              <div className={styles.algorithmCard}>
                <h3>强化学习模型</h3>
                <p>基于深度Q-Network (DQN) 的站点选址优化</p>
                <ul>
                  <li>状态空间: 富阳区栅格化地图</li>
                  <li>动作空间: 选择站点位置</li>
                  <li>奖励函数: POI覆盖率与站点数量的平衡</li>
                </ul>
              </div>
              <div className={styles.algorithmCard}>
                <h3>优化指标</h3>
                <p>全面考量各项指标，确保选址方案最优</p>
                <ul>
                  <li>覆盖率: 平均92%的POI点覆盖</li>
                  <li>成本效益: 最小站点数量实现最大覆盖</li>
                  <li>服务公平: 关注偏远地区服务质量</li>
                </ul>
              </div>
            </div>
          </section>

          {/* 底部联系区域 */}
          <section className={styles.contactSection}>
            <div className={styles.contactCard}>
              <h2>开始使用无人机选址系统</h2>
              <p>我们的系统可适用于不同地区的无人机站点规划，提供定制化选址方案</p>
              <button className={styles.contactButton}>联系我们</button>
            </div>
          </section>

          <footer className={styles.footer}>
            <p>无人机选址系统 &copy; {new Date().getFullYear()} - 基于POI点密度分析与强化学习</p>
          </footer>
        </main>
      )}
    </>
  );
};

export default Home; 