import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from models.networks import ActorNetwork, CriticNetwork
import torch.nn.functional as F

class PPO:
    """
    PPO算法实现
    """
    
    def __init__(self, state_dim, action_dim, config):
        """
        初始化PPO算法
        
        参数:
            state_dim: 状态维度
            action_dim: 动作维度
            config: 配置类实例
        """
        self.config = config
        self.device = config.DEVICE
        
        # 超参数
        self.gamma = config.GAMMA
        self.gae_lambda = config.GAE_LAMBDA
        self.clip_ratio = config.CLIP_RATIO
        self.entropy_coef = config.ENTROPY_COEF
        self.value_coef = config.VALUE_COEF
        self.max_grad_norm = config.MAX_GRAD_NORM
        self.learning_rate = config.LEARNING_RATE
        
        # 创建Actor和Critic网络
        self.actor = ActorNetwork(state_dim, action_dim, config.HIDDEN_DIM).to(self.device)
        self.critic = CriticNetwork(state_dim, config.HIDDEN_DIM).to(self.device)
        
        # 优化器
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=self.learning_rate)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=self.learning_rate)
        
        # 记录训练信息
        self.total_steps = 0
        
    def select_action(self, state):
        """
        根据状态选择动作
        
        参数:
            state: 状态
            
        返回:
            action: 采样的动作
            log_prob: 动作的对数概率
            value: 状态价值
        """
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action, log_prob, _ = self.actor.sample(state)
            value = self.critic(state)
        
        return action.cpu().numpy()[0], log_prob.cpu().item(), value.cpu().item()
    
    def evaluate_actions(self, states, actions):
        """
        评估动作
        
        参数:
            states: 状态批次
            actions: 动作批次
            
        返回:
            values: 状态价值
            log_probs: 动作的对数概率
            entropy: 策略熵
        """
        mu, sigma = self.actor(states)
        dist = torch.distributions.Normal(mu, sigma)
        
        log_probs = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        values = self.critic(states)
        
        return values, log_probs, entropy
    
    def update(self, memory):
        """
        更新网络参数
        
        参数:
            memory: 经验回放缓冲区
            
        返回:
            actor_loss: Actor网络损失
            critic_loss: Critic网络损失
        """
        # 从经验回放中获取数据
        states = torch.FloatTensor(memory.states).to(self.device)
        actions = torch.FloatTensor(memory.actions).to(self.device)
        old_log_probs = torch.FloatTensor(memory.log_probs).to(self.device)
        rewards = torch.FloatTensor(memory.rewards).to(self.device)
        dones = torch.FloatTensor(memory.dones).to(self.device)
        
        # 计算优势函数和回报
        advantages, returns = self._compute_gae(rewards, dones, memory.values)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO更新
        for _ in range(self.config.NUM_MINI_BATCHES):
            # 随机采样
            batch_indices = np.random.choice(len(states), self.config.BATCH_SIZE, replace=False)
            
            batch_states = states[batch_indices]
            batch_actions = actions[batch_indices]
            batch_old_log_probs = old_log_probs[batch_indices]
            batch_advantages = advantages[batch_indices]
            batch_returns = returns[batch_indices]
            
            # 评估动作
            values, log_probs, entropy = self.evaluate_actions(batch_states, batch_actions)
            
            # 计算actor损失
            ratio = torch.exp(log_probs - batch_old_log_probs)
            surr1 = ratio * batch_advantages
            surr2 = torch.clamp(ratio, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio) * batch_advantages
            actor_loss = -torch.min(surr1, surr2).mean() - self.entropy_coef * entropy.mean()
            
            # 计算critic损失
            values = values.squeeze(-1)
            critic_loss = F.mse_loss(values, batch_returns)
            
            # 更新网络
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
            self.actor_optimizer.step()
            
            self.critic_optimizer.zero_grad()
            critic_loss.backward()
            nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm)
            self.critic_optimizer.step()
        
        self.total_steps += 1
        
        return actor_loss.item(), critic_loss.item()
    
    def _compute_gae(self, rewards, dones, values):
        """
        计算广义优势估计(GAE)和回报
        
        参数:
            rewards: 奖励序列
            dones: 结束标志序列
            values: 价值估计序列
            
        返回:
            advantages: 优势函数
            returns: 回报
        """
        values = values + [0.0]  # 添加最后一个状态的价值(0)
        
        # 计算GAE
        advantages = torch.zeros_like(rewards)
        returns = torch.zeros_like(rewards)
        gae = 0
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae
            returns[t] = advantages[t] + values[t]
        
        return advantages, returns
    
    def save_models(self, path):
        """
        保存模型
        
        参数:
            path: 保存路径
        """
        torch.save({
            'actor': self.actor.state_dict(),
            'critic': self.critic.state_dict(),
            'actor_optimizer': self.actor_optimizer.state_dict(),
            'critic_optimizer': self.critic_optimizer.state_dict(),
            'total_steps': self.total_steps
        }, path)
    
    def load_models(self, path):
        """
        加载模型
        
        参数:
            path: 加载路径
        """
        checkpoint = torch.load(path)
        
        self.actor.load_state_dict(checkpoint['actor'])
        self.critic.load_state_dict(checkpoint['critic'])
        self.actor_optimizer.load_state_dict(checkpoint['actor_optimizer'])
        self.critic_optimizer.load_state_dict(checkpoint['critic_optimizer'])
        self.total_steps = checkpoint['total_steps'] 