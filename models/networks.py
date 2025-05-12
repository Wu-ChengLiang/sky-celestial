import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class ActorNetwork(nn.Module):
    """
    Actor网络，用于生成动作
    """
    
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        """
        初始化Actor网络
        
        参数:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_dim: 隐藏层维度
        """
        super(ActorNetwork, self).__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.mu = nn.Linear(hidden_dim, action_dim)
        self.sigma = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, state):
        """
        前向传播
        
        参数:
            state: 状态张量
            
        返回:
            mu: 动作均值
            sigma: 动作标准差
        """
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        mu = self.mu(x)
        sigma = F.softplus(self.sigma(x)) + 1e-3  # 确保方差为正
        
        return mu, sigma
    
    def sample(self, state):
        """
        根据状态采样动作
        
        参数:
            state: 状态张量
            
        返回:
            action: 采样的动作
            log_prob: 动作的对数概率
            entropy: 熵
        """
        mu, sigma = self.forward(state)
        dist = torch.distributions.Normal(mu, sigma)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        
        return action, log_prob, entropy


class CriticNetwork(nn.Module):
    """
    Critic网络，用于估计价值函数
    """
    
    def __init__(self, state_dim, hidden_dim=128):
        """
        初始化Critic网络
        
        参数:
            state_dim: 状态维度
            hidden_dim: 隐藏层维度
        """
        super(CriticNetwork, self).__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.value = nn.Linear(hidden_dim, 1)
        
    def forward(self, state):
        """
        前向传播
        
        参数:
            state: 状态张量
            
        返回:
            value: 状态价值
        """
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        value = self.value(x)
        
        return value 