import os
import time
import numpy as np
import torch
from configs import Config
from env import DroneEnvironment
from models import PPO, Memory
from view import visualize

def train():
    """
    训练主函数
    """
    # 创建配置和目录
    config = Config()
    config.make_dirs()
    
    # 设置随机种子
    np.random.seed(config.SEED)
    torch.manual_seed(config.SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(config.SEED)
    
    # 创建环境
    env = DroneEnvironment(config)
    
    # 初始化PPO算法
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    agent = PPO(state_dim, action_dim, config)
    
    # 创建经验回放缓冲区
    memory = Memory()
    
    # 训练参数
    total_rewards = []
    avg_rewards = []
    best_reward = float('-inf')
    
    # 开始训练
    for episode in range(config.EPOCHS):
        # 重置环境
        state, _ = env.reset()
        episode_reward = 0
        episode_steps = 0
        
        # 收集经验
        for step in range(config.NUM_STEPS):
            # 选择动作
            action, log_prob, value = agent.select_action(state)
            
            # 执行动作
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # 将经验添加到缓冲区
            memory.push(state, action, log_prob, reward, done, value)
            
            # 更新状态
            state = next_state
            episode_reward += reward
            episode_steps += 1
            
            # 如果回合结束，重置环境
            if done:
                # 最后状态的价值
                _, _, value = agent.select_action(state)
                memory.values.append(value)
                
                # 记录奖励
                total_rewards.append(episode_reward)
                if len(total_rewards) > 100:
                    avg_reward = np.mean(total_rewards[-100:])
                else:
                    avg_reward = np.mean(total_rewards)
                avg_rewards.append(avg_reward)
                
                print(f"Episode: {episode+1}, Step: {episode_steps}, Reward: {episode_reward:.2f}, Avg Reward: {avg_reward:.2f}")
                print(f"Info: POI Coverage: {info['poi_coverage']:.2f}, Area Coverage: {info['area_coverage']:.2f}, Overlap: {info['overlap_ratio']:.2f}")
                
                # 保存最佳模型
                if episode_reward > best_reward:
                    best_reward = episode_reward
                    agent.save_models(os.path.join(config.MODEL_DIR, "best_model.pth"))
                
                # 可视化
                if (episode + 1) % config.VISUAL_INTERVAL == 0:
                    print("Visualizing...")
                    drone_positions = state.reshape(-1, 2)
                    output_path = os.path.join(config.VISUAL_DIR, f"episode_{episode+1}.png")
                    visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, output_path, info)
                
                break
        
        # 更新PPO
        if len(memory) >= config.NUM_STEPS:
            agent.update(memory)
            memory.clear()
        
        # 定期保存模型
        if (episode + 1) % config.SAVE_INTERVAL == 0:
            agent.save_models(os.path.join(config.MODEL_DIR, f"model_{episode+1}.pth"))
    
    # 训练结束，保存最终模型
    agent.save_models(os.path.join(config.MODEL_DIR, "final_model.pth"))
    
    print("Training completed!")

if __name__ == "__main__":
    train() 