import numpy as np

class Memory:
    """
    经验回放缓冲区，用于存储训练数据
    """
    
    def __init__(self):
        """
        初始化经验回放缓冲区
        """
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.dones = []
        self.values = []
        
    def push(self, state, action, log_prob, reward, done, value):
        """
        添加经验
        
        参数:
            state: 状态
            action: 动作
            log_prob: 动作的对数概率
            reward: 奖励
            done: 是否结束
            value: 状态价值
        """
        self.states.append(state)
        self.actions.append(action)
        self.log_probs.append(log_prob)
        self.rewards.append(reward)
        self.dones.append(done)
        self.values.append(value)
        
    def clear(self):
        """
        清空缓冲区
        """
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.dones = []
        self.values = []
        
    def __len__(self):
        """
        返回缓冲区长度
        """
        return len(self.states) 