import os
import torch

class Config:
    # 数据相关配置
    DATA_PATH = 'data'
    POI_FILE = os.path.join(DATA_PATH, 'poi', '富阳区.csv')
    REGION_FILE = os.path.join(DATA_PATH, 'fuyang_json', '富阳区.json')
    # DEM_FILE = os.path.join(DATA_PATH, 'dem', 'merged_dem.tif')
    DEM_FILE = os.path.join(DATA_PATH, 'dem', 'merged_specific_dem.img')
    
# 绘制DEM数据失败: 'Axes' object has no attribute 'get_array'

    # 海拔相关配置
    ELEVATION_THRESHOLD = 50  # 海拔阈值（米）
    ELEVATION_PENALTY_WEIGHT = 0.2  # 海拔惩罚权重

    # 训练相关配置
    SEED = 42
    DRONE_NUM = 8  # 无人机库数量
    DRONE_RADIUS = 8000  # 无人机覆盖半径(米)
    
    # PPO算法超参数
    GAMMA = 0.99  # 折扣因子
    GAE_LAMBDA = 0.95  # GAE参数
    CLIP_RATIO = 0.2  # PPO裁剪参数
    ENTROPY_COEF = 0.01  # 熵正则化系数
    VALUE_COEF = 0.5  # 价值函数损失系数
    MAX_GRAD_NORM = 0.5  # 梯度裁剪
    
    # 神经网络配置
    HIDDEN_DIM = 128  # 隐藏层维度
    LEARNING_RATE = 3e-4  # 学习率
    
    # 训练过程配置
    EPOCHS = 500  # 总训练轮次
    BATCH_SIZE = 64  # 批大小
    # NUM_STEPS = 2048  # 每轮收集的步数
    NUM_STEPS = 1000  # 每轮收集的步数
    NUM_MINI_BATCHES = 4  # 小批次数
    EVAL_INTERVAL = 10  # 评估间隔
    SAVE_INTERVAL = 100  # 保存模型间隔
    VISUAL_INTERVAL = 1  # 可视化间隔
    
    # 目录配置
    RESULT_DIR = 'result'
    MODEL_DIR = os.path.join(RESULT_DIR, 'models')
    VISUAL_DIR = os.path.join(RESULT_DIR, 'visuals')
    
    # 设备配置
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 创建必要的目录
    @staticmethod
    def make_dirs():
        os.makedirs(Config.MODEL_DIR, exist_ok=True)
        os.makedirs(Config.VISUAL_DIR, exist_ok=True) 