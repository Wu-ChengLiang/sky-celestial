import { useEffect, useRef, useState } from 'react';
// 使用import方式导入Three.js，而不是require
import * as THREE from 'three';

// 自定义Hook - 处理3D地球逻辑
const useEarth = (containerRef: React.RefObject<HTMLDivElement>) => {
  const requestRef = useRef<number>();
  const sceneRef = useRef<THREE.Scene>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const earthRef = useRef<THREE.Group>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 初始化Three.js场景
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      // 创建场景
      const scene = new THREE.Scene();
      sceneRef.current = scene;

      // 创建相机
      const camera = new THREE.PerspectiveCamera(
        60, 
        containerRef.current.clientWidth / containerRef.current.clientHeight, 
        0.1, 
        1000
      );
      camera.position.set(0, 0, 8);
      cameraRef.current = camera;

      // 创建渲染器
      const renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true
      });
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0xf5f5f5, 0);
      containerRef.current.appendChild(renderer.domElement);
      rendererRef.current = renderer;

      // 添加光源
      //环境光
      const ambientLight = new THREE.AmbientLight(0xffffff, 2);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
      directionalLight.position.set(3, 10, 5);
      scene.add(directionalLight);
      
      const hemisphereLight = new THREE.HemisphereLight(0x4488bb, 0xcc8844, 0.3);
      scene.add(hemisphereLight);

      // 创建地球组
      const earth = new THREE.Group();
      earthRef.current = earth;
      
      // 创建地球模型(使用Promise来处理纹理加载)
      const createEarthModel = async () => {
        const textureLoader = new THREE.TextureLoader();
        
        // 加载纹理 (使用Promise包装，便于处理加载状态)
        const loadTexture = (url: string) => {
          return new Promise<THREE.Texture>((resolve, reject) => {
            textureLoader.load(
              url, 
              (texture) => resolve(texture),
              undefined,
              // 错误处理
              (error: unknown) => {
                console.error("加载纹理失败:", error);
                reject(new Error("加载纹理失败"));
              }
            );
          });
        };
        
        try {
          // 加载三个纹理 (使用本地路径，不依赖外部资源)
          const [earthTexture, bumpMap, specularMap] = await Promise.all([
            loadTexture('/textures/earth_daymap.jpg'),
            loadTexture('/textures/earth_normal_map.jpg'),
            loadTexture('/textures/earth_specular_map.jpg')
          ]);
          
          // 创建地球几何体
          const geometry = new THREE.SphereGeometry(2.5, 64, 64);
          const material = new THREE.MeshPhongMaterial({ 
            map: earthTexture,
            bumpMap: bumpMap,
            bumpScale: 0.025,
            specularMap: specularMap,
            specular: 0x333333,
            shininess: 10,
          });
          
          const earthMesh = new THREE.Mesh(geometry, material);
          earthMesh.castShadow = true;
          earthMesh.receiveShadow = true;
          
          // 添加大气层效果
          const atmosphereGeometry = new THREE.SphereGeometry(2.55, 64, 64);
          const atmosphereMaterial = new THREE.MeshPhongMaterial({
            color: 0x3399ff,
            transparent: true,
            opacity: 0.2,
            side: THREE.BackSide
          });
          const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
          
          // 添加边框环
          const borderGeometry = new THREE.TorusGeometry(2.7, 0.05, 16, 100);
          const borderMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x3a5169,
            transparent: true,
            opacity: 0.8
          });
          const border = new THREE.Mesh(borderGeometry, borderMaterial);
          border.rotation.x = Math.PI / 2;
          
          earth.add(earthMesh);
          earth.add(atmosphere);
          earth.add(border);
          scene.add(earth);
          
          // 设置初始位置偏移
          earth.position.x = -2;
          
          setLoading(false);
        } catch (error) {
          console.error("加载地球纹理失败:", error);
          setError("加载地球纹理失败");
          setLoading(false);
        }
      };
      
      createEarthModel();
      
      // 动画循环
      const animate = () => {
        if (earthRef.current) {
          earthRef.current.rotation.y += 0.002;
        }
        
        if (rendererRef.current && sceneRef.current && cameraRef.current) {
          rendererRef.current.render(sceneRef.current, cameraRef.current);
        }
        
        requestRef.current = requestAnimationFrame(animate);
      };
      
      requestRef.current = requestAnimationFrame(animate);

      // 响应窗口大小变化
      const handleResize = () => {
        if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;
        
        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;
        
        cameraRef.current.aspect = width / height;
        cameraRef.current.updateProjectionMatrix();
        
        rendererRef.current.setSize(width, height);
      };
      
      window.addEventListener('resize', handleResize);
      
      // 清理函数
      return () => {
        window.removeEventListener('resize', handleResize);
        
        if (requestRef.current) {
          cancelAnimationFrame(requestRef.current);
        }
        
        if (rendererRef.current && containerRef.current) {
          containerRef.current.removeChild(rendererRef.current.domElement);
          rendererRef.current.dispose();
        }
      };
    } catch (err) {
      console.error("初始化地球场景失败:", err);
      setError("初始化地球场景失败");
      setLoading(false);
    }
  }, [containerRef]);
  
  // 控制地球根据滚动位置进行动画
  const updateScroll = (scrollPercent: number) => {
    if (!earthRef.current || !cameraRef.current) return;
    
    // 地球响应滚动
    if (scrollPercent < 0.3) {
      // 第一阶段：显示地球并旋转
      earthRef.current.visible = true;
      cameraRef.current.position.z = 8 - scrollPercent * 3;
      cameraRef.current.position.y = scrollPercent * 2;
      
      // 地球旋转
      earthRef.current.rotation.y = scrollPercent * Math.PI * 2;
    } else {
      // 第二阶段：地球渐隐
      const earthOpacity = THREE.MathUtils.lerp(1, 0, (scrollPercent - 0.3) / 0.4);
      
      // 调整材质透明度
      if (earthRef.current.children[0] instanceof THREE.Mesh) {
        const earthMesh = earthRef.current.children[0] as THREE.Mesh;
        const material = earthMesh.material as THREE.MeshPhongMaterial;
        material.transparent = true;
        material.opacity = earthOpacity;
      }
      
      // 调整大气层透明度
      if (earthRef.current.children[1] instanceof THREE.Mesh) {
        const atmosphere = earthRef.current.children[1] as THREE.Mesh;
        const material = atmosphere.material as THREE.MeshPhongMaterial;
        material.opacity = earthOpacity * 0.2;
      }
      
      // 调整边框透明度
      if (earthRef.current.children[2] instanceof THREE.Mesh) {
        const border = earthRef.current.children[2] as THREE.Mesh;
        const material = border.material as THREE.MeshBasicMaterial;
        material.opacity = earthOpacity * 0.8;
      }
      
      // 超过一定阈值隐藏地球
      if (scrollPercent > 0.7) {
        earthRef.current.visible = false;
      } else {
        earthRef.current.visible = true;
      }
    }
  };
  
  return {
    loading,
    error,
    updateScroll, // 导出滚动更新函数
  };
};

export default useEarth; 