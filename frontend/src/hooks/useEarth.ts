
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

type EarthRefs = {
  scene: THREE.Scene | null;
  camera: THREE.PerspectiveCamera | null;
  renderer: THREE.WebGLRenderer | null;
  earth: THREE.Group | null;
};

const useEarth = (containerRef: React.RefObject<HTMLDivElement>) => {
  const requestRef = useRef<number>();
  const refs = useRef<EarthRefs>({
    scene: null,
    camera: null,
    renderer: null,
    earth: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    try {
      // 初始化场景
      const scene = new THREE.Scene();
      refs.current.scene = scene;

      // 初始化相机
      const camera = new THREE.PerspectiveCamera(
        60,
        containerRef.current.clientWidth / containerRef.current.clientHeight,
        0.1,
        1000
      );
      camera.position.set(0, 0, 8);
      refs.current.camera = camera;

      // 初始化渲染器
      const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true
      });
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0xf5f5f5, 0);
      containerRef.current.appendChild(renderer.domElement);
      refs.current.renderer = renderer;

      // 光源设置
      const ambientLight = new THREE.AmbientLight(0xffffff, 2);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
      directionalLight.position.set(3, 10, 5);
      scene.add(directionalLight);
      
      const hemisphereLight = new THREE.HemisphereLight(0x4488bb, 0xcc8844, 0.3);
      scene.add(hemisphereLight);

      // 地球组
      const earth = new THREE.Group();
      refs.current.earth = earth;

      const createEarthModel = async () => {
        const textureLoader = new THREE.TextureLoader();
        
        try {
          const [earthTexture, bumpMap, specularMap] = await Promise.all([
            textureLoader.loadAsync('/textures/earth_daymap.jpg'),
            textureLoader.loadAsync('/textures/earth_normal_map.jpg'),
            textureLoader.loadAsync('/textures/earth_specular_map.jpg')
          ]);
          
          // 地球主体
          const geometry = new THREE.SphereGeometry(2.5, 64, 64);
          const material = new THREE.MeshPhongMaterial({ 
            map: earthTexture,
            bumpMap,
            bumpScale: 0.025,
            specularMap,
            specular: 0x333333,
            shininess: 10,
          });
          
          const earthMesh = new THREE.Mesh(geometry, material);
          
          // 大气层
          const atmosphereMaterial = new THREE.MeshPhongMaterial({
            color: 0x3399ff,
            transparent: true,
            opacity: 0.2,
            side: THREE.BackSide
          });
          const atmosphere = new THREE.Mesh(
            new THREE.SphereGeometry(2.55, 64, 64),
            atmosphereMaterial
          );
          
          // 边框
          const borderMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x3a5169,
            transparent: true,
            opacity: 0.8
          });
          const border = new THREE.Mesh(
            new THREE.TorusGeometry(2.7, 0.05, 16, 100),
            borderMaterial
          );
          border.rotation.x = Math.PI / 2;
          
          earth.add(earthMesh, atmosphere, border);
          scene.add(earth);
          earth.position.x = -2;
          
          setLoading(false);
        } catch (err) {
          console.error("加载纹理失败:", err);
          setError("加载纹理失败");
          setLoading(false);
        }
      };

      createEarthModel();

      // 动画循环
      const animate = () => {
        if (refs.current.earth) {
          refs.current.earth.rotation.y += 0.002;
        }
        
        if (refs.current.renderer && refs.current.scene && refs.current.camera) {
          refs.current.renderer.render(refs.current.scene, refs.current.camera);
        }
        
        requestRef.current = requestAnimationFrame(animate);
      };
      
      requestRef.current = requestAnimationFrame(animate);

      // 窗口大小调整
      const handleResize = () => {
        if (!containerRef.current || !refs.current.camera || !refs.current.renderer) return;
        
        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;
        
        refs.current.camera.aspect = width / height;
        refs.current.camera.updateProjectionMatrix();
        refs.current.renderer.setSize(width, height);
      };
      
      window.addEventListener('resize', handleResize);
      
      return () => {
        window.removeEventListener('resize', handleResize);
        if (requestRef.current) cancelAnimationFrame(requestRef.current);
        if (refs.current.renderer && containerRef.current) {
          containerRef.current.removeChild(refs.current.renderer.domElement);
          refs.current.renderer.dispose();
        }
      };
    } catch (err) {
      console.error("初始化场景失败:", err);
      setError("初始化场景失败");
      setLoading(false);
    }
  }, [containerRef]);
  
  const updateScroll = (scrollPercent: number) => {
    const { earth, camera } = refs.current;
    if (!earth || !camera) return;
    
    const earthOpacity = THREE.MathUtils.lerp(1, 0, (scrollPercent - 0.3) / 0.4);
    
    if (scrollPercent < 0.3) {
      earth.visible = true;
      camera.position.z = 8 - scrollPercent * 3;
      camera.position.y = scrollPercent * 2;
      earth.rotation.y = scrollPercent * Math.PI * 2;
    } else {
      // 更新材质透明度
      [0, 1, 2].forEach(i => {
        if (earth.children[i] instanceof THREE.Mesh) {
          const mesh = earth.children[i] as THREE.Mesh;
          if (mesh.material instanceof THREE.MeshPhongMaterial || 
              mesh.material instanceof THREE.MeshBasicMaterial) {
            mesh.material.transparent = true;
            mesh.material.opacity = i === 0 ? earthOpacity : 
                                  i === 1 ? earthOpacity * 0.2 : 
                                  earthOpacity * 0.8;
          }
        }
      });

      earth.visible = scrollPercent <= 0.7;
    }
  };
  
  return { loading, error, updateScroll };
};

export default useEarth;