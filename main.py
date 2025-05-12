import argparse
import os
from configs import Config
from train import train
from eval import evaluate

def main():
    """
    项目主入口
    """
    parser = argparse.ArgumentParser(description="无人机库选址 - 深度强化学习项目")
    parser.add_argument("--mode", type=str, default="train", choices=["train", "eval"], help="运行模式：train或eval")
    parser.add_argument("--model", type=str, default=None, help="评估模式下的模型路径")
    parser.add_argument("--episodes", type=int, default=10, help="评估模式下的回合数")
    parser.add_argument("--render", action="store_true", help="是否生成可视化结果")
    
    args = parser.parse_args()
    
    # 创建配置和目录
    config = Config()
    config.make_dirs()
    
    if args.mode == "train":
        print("启动训练模式...")
        train()
    else:  # eval
        print("启动评估模式...")
        model_path = args.model
        if model_path is None:
            # 使用最佳模型
            model_path = os.path.join(config.MODEL_DIR, "best_model.pth")
            if not os.path.exists(model_path):
                # 使用最新模型
                model_files = [f for f in os.listdir(config.MODEL_DIR) if f.endswith(".pth")]
                if model_files:
                    model_path = os.path.join(config.MODEL_DIR, sorted(model_files)[-1])
                else:
                    raise FileNotFoundError("没有找到训练好的模型文件，请先训练或指定模型路径。")
        
        evaluate(model_path, args.episodes, args.render)

if __name__ == "__main__":
    main() 