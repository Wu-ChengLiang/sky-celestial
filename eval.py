import os
import numpy as np
import torch
import argparse
from configs import Config
from env import DroneEnvironment
from models import PPO
from view import visualize
from shapely.geometry import Point

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
        print(f"\n===== 开始评估第 {episode+1} 轮 =====")
        
        # 重置环境
        state, _ = env.reset()
        episode_reward = 0
        done = False
        
        # 打印初始状态信息
        drone_positions = state.reshape(-1, 2)
        print(f"初始无人机位置数量: {len(drone_positions)}")
        for i, pos in enumerate(drone_positions):
            print(f"  无人机 {i+1}: 经度={pos[0]:.6f}, 纬度={pos[1]:.6f}")
        
        steps = 0
        while not done:
            # 选择动作
            action, _, _ = agent.select_action(state)
            
            # 执行动作
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # 更新状态
            state = next_state
            episode_reward += reward
            steps += 1
        
        # 最终状态信息
        final_positions = state.reshape(-1, 2)
        print(f"完成步数: {steps}, 最终无人机位置数量: {len(final_positions)}")
        for i, pos in enumerate(final_positions):
            print(f"  无人机 {i+1}: 经度={pos[0]:.6f}, 纬度={pos[1]:.6f}")
        
        # 记录结果
        rewards.append(episode_reward)
        poi_coverages.append(info['poi_coverage'])
        area_coverages.append(info['area_coverage'])
        overlap_ratios.append(info['overlap_ratio'])
        
        print(f"Episode {episode+1}: Reward = {episode_reward:.2f}, POI Coverage = {info['poi_coverage']:.2f}, Area Coverage = {info['area_coverage']:.2f}, Overlap = {info['overlap_ratio']:.2f}")
        
        # 渲染结果
        if render:
            try:
                # 使用最终状态渲染
                drone_positions = state.reshape(-1, 2)
                output_path = os.path.join(config.VISUAL_DIR, f"eval_episode_{episode+1}.png")
                
                # 检查无人机位置是否在区域内
                in_region_count = 0
                for pos in drone_positions:
                    if env.region_geometry.contains(Point(pos[0], pos[1])):
                        in_region_count += 1
                
                print(f"无人机在区域内的数量: {in_region_count}/{len(drone_positions)}")
                
                # 增加渲染信息
                print(f"开始生成可视化结果，无人机数量: {len(drone_positions)}")
                visualize(env.region_geometry, env.poi_gdf, drone_positions, config.DRONE_RADIUS, output_path, info)
            except Exception as e:
                print(f"渲染出错: {e}")
    
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