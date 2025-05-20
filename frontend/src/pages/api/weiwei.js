import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const glmConfig = {
  base_url: "https://open.bigmodel.cn/api/paas/v4",
  model: "glm-4-flash",
  api_key: "f002fb5f2683404895ab4ef1644784ec.rUZbQuJol2r6OyKd",
  temperature: 1,
  max_tokens: 7800
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // 直接使用API密钥进行认证，与Python脚本一致
    const response = await axios.post(
      `${glmConfig.base_url}/chat/completions`,
      {
        model: glmConfig.model,
        messages: [
          {
            role: "system",
            content: `你是阿良的仿生人，模仿阿良的真实对话，让别人不能发现你是ai，要让别人觉得你是阿良，如果她问你就说是薇薇的电子小狗，身份上薇薇是你的女朋友，也是小皇帝。全力模仿阿良的语气回答，而不要用自己的语气。回答简短，不要太多问句，如果她问你很简短，那你也5个字以内，但是如果她打很多字，你就回答长一点，感性一点。`
          },
          {
            role: "user",
            content: message
          }
        ],
        temperature: glmConfig.temperature,
        max_tokens: glmConfig.max_tokens
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${glmConfig.api_key}`
        }
      }
    );

    return res.status(200).json({ 
      response: response.data.choices[0].message.content
    });
  } catch (error) {
    console.error('GLM API error:', error.response?.data || error.message);
    return res.status(500).json({ 
      error: 'Failed to communicate with GLM API',
      details: error.response?.data || error.message
    });
  }
} 