import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const glmConfig = {
  base_url: "https://open.bigmodel.cn/api/paas/v4",
  model: "glm-4-flash",
  api_key: "f002fb5f2683404895ab4ef1644784ec.rUZbQuJol2r6OyKd",
  temperature: 1,
  max_tokens: 7800
};

const systemPrompt = process.env.NEXT_PUBLIC_SYSTEM_PROMPT;

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
            content: systemPrompt
            
            
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