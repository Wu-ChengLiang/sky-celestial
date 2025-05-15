# ​Sky-Celestial天枢 强化学习机库选址系统


🎉 **重磅消息！无人机选址系统天枢开源啦！** 🎈

🌌 ​SkyCelestial 天枢​ 是2025届毕业生吴城良的本科毕业设计，基于PPO算法强化学习的AI选址系统，名称源自北斗七星之首"天枢"✨

天枢使用深度强化学习（PPO算法）优化无人机库的选址，以富阳为案例，实现对区域POI点和区域的高效覆盖。

**选址渲染图    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  🚀 b站：跟着阿良学AI** 🚀
![eval_episode_2](/frontend/public/images/eval_episode_2.png)





👀 **想了解更多？**  

web网站链接，一探究竟！👇

🔗 [无人机选址系统 | 基于POI点密度与强化学习](http://wcl.323424.xyz/)

## 项目概述

- **目标**：在富阳区选择8个最优的无人机库位置，使得无人机可以覆盖尽可能多的POI点和区域
- **约束**：
  - 每个无人机库的覆盖半径为8km
  - 需要避免无人机库之间的覆盖区域重叠
  - 无人机库必须位于富阳区行政边界内


## 项目结构

```
├── configs.py            # 项目配置文件
├── env/                  # 环境模块
│   ├── __init__.py
│   └── drone_env.py      # 无人机环境实现
├── reward/               # 奖励模块
│   ├── __init__.py
│   └── reward_calculator.py  # 奖励计算器
├── models/               # 模型模块
│   ├── __init__.py
│   ├── networks.py       # 神经网络定义
│   ├── ppo.py            # PPO算法实现
│   └── memory.py         # 经验回放缓冲区
├── train.py              # 训练脚本
├── eval.py               # 评估脚本
├── view.py               # 可视化模块
├── data/                 # 数据目录
│   ├── poi/              # POI数据
│   └── fuyang_json/      # 富阳区边界数据
├── result/               # 结果目录
│   ├── models/           # 保存的模型
│   └── visuals/          # 可视化结果
├── requirements.txt      # 依赖包列表
└── README.md             # 项目说明
├── frontend/             # 前端项目目录
│   ├── public/           # 静态资源
│   ├── src/              # 前端源码
│   │   ├── components/   # 可视化组件
│   │   │   ├── Earth/    # 3D地球组件
│   │   │   ├── Map/      # 2D地图组件
│   │   │   └── LocationCard/ # 选址卡片组件
│   │   ├── styles/       # 样式文件
│   │   └── pages/        # Next.js页面路由
```



## 快速启动


### 后端依赖

💬单独启动后端即可开始训练
```bash
pip install -r requirements.txt
```



### 训练模型

```bash
python train.py
```

训练过程中，将在`result/models/`目录下保存模型，在`result/visuals/`目录下保存可视化结果。

### 评估模型

```bash
python eval.py --model result/models/best_model.pth --episodes 10 --render
```
参数说明：
- `--model`：模型路径
- `--episodes`：评估回合数
- `--render`：是否生成可视化结果

## 前端可视化

### 前端依赖

```bash
cd frontend
npm install
npm run build
npx serve@latest out
```

访问3000端口http://localhost:3000




## 论文研究细节

### 1. 具体研究内容

​**研究目标**​：基于GIS与强化学习（PPO算法）优化无人值守固定机库的部署选址，提升生态环境巡查监测效率。  
​**核心内容**​：

- 构建多源地理数据融合模型（DEM地形、POI兴趣点、现有机库位置）
- 设计强化学习智能体，以PPO算法动态优化选址策略
- 建立覆盖效率、地形适配、成本控制的多目标奖励机制
- 开发可视化系统验证选址方案的合理性

---

### 2. 技术路线

​**关键技术**​：

1. ​**数据层**​：整合ASTER GDEM 30M地形数据与高德API的POI数据
2. ​**算法层**​：
    - 采用PPO算法构建Actor-Critic网络
    - 设计状态空间（经纬度、覆盖率、海拔、邻近机库距离）
    - 动作空间为连续经纬度坐标输出
3. ​**验证层**​：
    - 通过覆盖率、重叠度等指标评估选址效果
    - 与传统方法（遗传算法、DQN）进行对比实验

---

### 3. 具体研究过程
![eval_episode_2](/frontend/public/images/论文架构.png)

### 4. 取得成果（效率比较）

​**关键指标提升**​：

| 指标          | 传统方法  | 本方法   | 提升幅度  |
| ----------- | ----- | ----- | ----- |
| POI覆盖率      | 68%   | 89%   | +21%  |
| 机库数量（同等覆盖）  | 9个    | 6个    | -33%  |
| 选址决策耗时      | 4.2小时 | 0.5小时 | 88%缩短 |

---

### 5. 结论

1. ​**方法有效性**​：GIS与PPO融合显著提升选址科学性，POI覆盖率提升至89%，机库数量减少33%。
2. ​**创新点**​：
   实现多目标优化（覆盖/成本/地形）的协同决策
3. ​**应用价值**​：为智慧城市、应急管理提供可扩展的选址决策框架，推动无人机监测网络智能化发展。