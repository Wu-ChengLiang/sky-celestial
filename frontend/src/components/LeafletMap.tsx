import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import styles from '@/styles/LeafletMap.module.css';
import 'leaflet/dist/leaflet.css';

// 修复Leaflet默认图标问题
const fixLeafletIcon = () => {
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  });
};

// 村委会数据
const villages = [
  {name: "富阳区人民政府", latlng: [30.049712, 119.951153], address: "富春街道桂花西路28号望江楼"},
  {name: "大山村", latlng: [29.973123, 119.788043], address: "新登镇"},
  {name: "新岭村村委会", latlng: [29.941509, 119.789385], address: "新岭村杨家"},
  {name: "双联村村委会", latlng: [29.955238, 119.759999], address: "杭州市富阳区双胜线东50米"},
  {name: "上山村村委会", latlng: [29.999293, 119.775633], address: "上对线与宝万线交叉口东120米"},
  {name: "富阳区新登镇上旺村村民委员会", latlng: [29.995378, 119.758284], address: "新登镇上旺村"},
  {name: "昌东村村委会", latlng: [30.008115, 119.805772], address: "横凉亭路辅路"},
  {name: "双江村村委会", latlng: [29.970707, 119.742904], address: "双江路与金城路交叉口东北280米"},
  {name: "五四村村委会", latlng: [29.981202, 119.840755], address: "鹿山街道五四村", tel: "0571-63488224"},
  {name: "松溪村村委会", latlng: [29.999451, 119.752269], address: "新登镇松溪村", tel: "0571-63205808"},
  {name: "乘庄村村委会", latlng: [29.990192, 119.744531], address: "金城北路与松涛路交叉口南120米"},
  {name: "双塔村村委会(郎家庄)", latlng: [29.951262, 119.742534], address: "305省道与双胜线交叉口南460米"},
  {name: "官山村村委会", latlng: [29.997690, 119.745573], address: "沃新线新堰阳光家园38栋"},
  {name: "方家井村村委会", latlng: [30.013673, 119.837991], address: "辛平线东北30米"},
  {name: "包秦村村委会", latlng: [30.012831, 119.743889], address: "新登镇包秦村"},
  {name: "宵井村村委会", latlng: [30.025657, 119.829161], address: "方贝线"},
  {name: "新中村村委会", latlng: [29.906259, 119.818932], address: "新桐乡坞口村", tel: "0571-63487692"},
  {name: "春渚村村委会", latlng: [29.898936, 119.807880], address: "窄后线与庙大段交叉口北340米"},
  {name: "洋沙村委会", latlng: [29.916825, 119.853994], address: "洋沙村", tel: "0571-63570506"},
  {name: "九儿村村委会", latlng: [29.966182, 119.702027], address: "新龙线附近"},
  {name: "南山村村委会", latlng: [29.986750, 119.883883], address: "横大线附近"},
  {name: "唐昌村村委会", latlng: [30.040808, 119.741725], address: "永青线永昌镇唐昌村村民委员会"},
  {name: "上沙村村委会", latlng: [29.899547, 119.842776], address: "场口镇上沙村"},
  {name: "董湾村", latlng: [29.896798, 119.737180], address: "富董线与渌渚江绿道交叉口西北240米"},
  {name: "葛溪村村委会", latlng: [29.989721, 119.692622], address: "新淳线与新兴西路交叉口东北260米"},
  {name: "徐家村村委会", latlng: [29.905407, 119.859633], address: "瓜桥江绿道与塘上线交叉口西北260米"},
  {name: "华丰村村委会", latlng: [29.936859, 119.888831], address: "叶华线西北侧"},
  {name: "富阳区鹿山街道三合村村民委员会", latlng: [29.984620, 119.854386], address: "南新线附近"},
  {name: "富阳区富春街道春华村村民委员会", latlng: [30.044653, 119.900834], address: "302省道附近"},
  {name: "富阳区富春街道三桥村村民委员会", latlng: [30.067878, 119.902709], address: "三桥路附近"},
];

// 简化后的富阳区边界数据 (前面几个点作为示例)
const fuyangAreaCoordinates = [
  [119.996335,30.181542],[119.993905,30.179289],[119.987987,30.174908],[119.984136,30.174104],
  [119.980171,30.174046],[119.976881,30.174845],[119.974302,30.175111],[119.969393,30.174267],
  [119.964668,30.172853],[119.963105,30.170469],[119.960938,30.16855],[119.959275,30.168003],
  // ...更多坐标点
];

const LeafletMap: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !mapRef.current || leafletMapRef.current) return;
    
    // 修复Leaflet图标
    fixLeafletIcon();
    
    // 初始化地图
    const map = L.map(mapRef.current).setView([30.05, 119.95], 11);
    leafletMapRef.current = map;
    
    // 添加OpenStreetMap底图
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // 绘制富阳区边界
    const fuyangAreaPoints = fuyangAreaCoordinates.map(coord => [coord[1], coord[0]]);
    L.polygon(fuyangAreaPoints as L.LatLngExpression[], {
      color: '#3388ff',
      weight: 2,
      fillOpacity: 0.2
    }).addTo(map);
    
    // 添加村委会点位
    villages.forEach(village => {
      L.circleMarker([village.latlng[0], village.latlng[1]], {
        radius: 6,
        color: '#ff7800',
        fillColor: '#ff7800',
        fillOpacity: 0.8
      })
      .bindPopup(`<b>${village.name}</b><br>${village.address}`)
      .addTo(map);
    });
    
    // 添加比例尺
    L.control.scale().addTo(map);
    
    // 添加选址算法结果点位 (模拟数据)
    const algorithmSites = [
      { name: "站点1", latlng: [30.080, 119.92], coverage: "94%" },
      { name: "站点2", latlng: [29.995, 119.82], coverage: "88%" },
      { name: "站点3", latlng: [29.915, 119.78], coverage: "92%" },
      { name: "站点4", latlng: [30.045, 119.80], coverage: "90%" },
      { name: "站点5", latlng: [29.95, 119.95], coverage: "89%" },
      { name: "站点6", latlng: [30.10, 120.02], coverage: "93%" },
      { name: "站点7", latlng: [29.90, 119.85], coverage: "91%" },
      { name: "站点8", latlng: [30.02, 119.94], coverage: "94%" },
    ];
    
    algorithmSites.forEach(site => {
      // 创建自定义图标
      const siteIcon = L.divIcon({
        className: styles.siteMarker,
        html: `<div class="${styles.siteMarkerInner}"></div>`,
        iconSize: [20, 20]
      });
      
      // 添加标记
      L.marker([site.latlng[0], site.latlng[1]], { icon: siteIcon })
        .bindPopup(`
          <div class="${styles.sitePopup}">
            <h3>${site.name}</h3>
            <p>覆盖率: ${site.coverage}</p>
            <p>服务半径: 8km</p>
          </div>
        `)
        .addTo(map);
      
      // 添加服务范围圆圈
      L.circle([site.latlng[0], site.latlng[1]], {
        radius: 8000, // 8公里半径
        color: '#43a047',
        fillColor: '#43a047',
        fillOpacity: 0.1,
        weight: 1
      }).addTo(map);
    });
    
    // 清理函数
    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  return <div ref={mapRef} className={styles.map}></div>;
};

export default LeafletMap; 