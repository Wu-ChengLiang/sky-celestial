import os
import numpy as np
import torch
import argparse
from configs import Config
from env import DroneEnvironment
from models import PPO
from view import visualize

def evaluate(model_path, num_episodes=10, render=True):
    """
    评估训练好的模型
    
    参数:
        model_path: 模型路径
        num_episodes: 评估的轮数
        render: 是否渲染
    """
    # 创建配置
    config = Config()
    
    # 创建环境
    env = DroneEnvironment(config)
    
    # 初始化PPO算法
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    agent = PPO(state_dim, action_dim, config)
    
    # 加载模型
    agent.load_models(model_path)
    print(f"Loaded model from {model_path}")
    
    # 评估结果
    rewards = []
    poi_coverages = []
    area_coverages = []
    overlap_ratios = []
    
    # 开始评估
    for episode in range(num_episodes):
        # 重置环境
        state, _ = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            # 选择动作
            action, _, _ = agent.select_action(state)
            
            # 执行动作
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # 更新状态
            state = next_state
            episode_reward += reward
        
        # 记录结果
        rewards.append(episode_reward)
        poi_coverages.append(info['poi_coverage'])
        area_coverages.append(info['area_coverage'])
        overlap_ratios.append(info['overlap_ratio'])
        
        print(f"Episode {episode+1}: Reward = {episode_reward:.2f}, POI Coverage = {info['poi_coverage']:.2f}, Area Coverage = {info['area_coverage']:.2f}, Overlap = {info['overlap_ratio']:.2f}")
        
        # 渲染结果
        if render:
            drone_positions = state.reshape(-1, 2)
            output_path = os.path.join(config.VISUAL_DIR, f"eval_episode_{episode+1}.png")
            visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, output_path, info)
    
    # 打印平均结果
    avg_reward = np.mean(rewards)
    avg_poi_coverage = np.mean(poi_coverages)
    avg_area_coverage = np.mean(area_coverages)
    avg_overlap_ratio = np.mean(overlap_ratios)
    
    print("\nEvaluation Results:")
    print(f"Average Reward: {avg_reward:.2f}")
    print(f"Average POI Coverage: {avg_poi_coverage:.2f}")
    print(f"Average Area Coverage: {avg_area_coverage:.2f}")
    print(f"Average Overlap Ratio: {avg_overlap_ratio:.2f}")
    
    # 返回最佳结果
    best_idx = np.argmax(rewards)
    best_result = {
        'reward': rewards[best_idx],
        'poi_coverage': poi_coverages[best_idx],
        'area_coverage': area_coverages[best_idx],
        'overlap_ratio': overlap_ratios[best_idx],
        'episode': best_idx
    }
    
    print(f"\nBest Results (Episode {best_idx+1}):")
    print(f"Reward: {best_result['reward']:.2f}")
    print(f"POI Coverage: {best_result['poi_coverage']:.2f}")
    print(f"Area Coverage: {best_result['area_coverage']:.2f}")
    print(f"Overlap Ratio: {best_result['overlap_ratio']:.2f}")
    
    return best_result

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--model", type=str, default="result/models/best_model.pth", help="Path to model file")
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes to evaluate")
    parser.add_argument("--render", action="store_true", help="Render evaluation")
    
    args = parser.parse_args()
    
    # 评估
    evaluate(args.model, args.episodes, args.render) 