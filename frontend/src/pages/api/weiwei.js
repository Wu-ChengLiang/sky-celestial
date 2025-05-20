import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const glmConfig = {
  base_url: "https://open.bigmodel.cn/api/paas/v4",
  model: "glm-4-flash",
  api_key: "f002fb5f2683404895ab4ef1644784ec.rUZbQuJol2r6OyKd",
  temperature: 1,
  max_tokens: 7800,
  timeout: 30000 // 30 second timeout
};

const systemPrompt = process.env.NEXT_PUBLIC_SYSTEM_PROMPT;

// Create a reusable axios instance with proper configuration
const apiClient = axios.create({
  baseURL: glmConfig.base_url,
  timeout: glmConfig.timeout,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${glmConfig.api_key}`
  }
});

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), glmConfig.timeout);

    try {
      const response = await apiClient.post(
        "/chat/completions", 
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
          signal: controller.signal
        }
      );

      clearTimeout(timeoutId);
      return res.status(200).json({ 
        response: response.data.choices[0].message.content
      });
    } catch (apiError) {
      clearTimeout(timeoutId);
      
      if (apiError.name === 'AbortError' || apiError.code === 'ECONNABORTED') {
        console.error('API request timed out');
        return res.status(503).json({ 
          error: 'Request timed out, please try again later'
        });
      }

      throw apiError; // Let the outer catch handle other errors
    }
  } catch (error) {
    console.error('GLM API error:', 
      error.response?.data || error.message || 'Unknown error');
    
    // Determine appropriate status code based on error
    const statusCode = error.response?.status || 500;
    
    return res.status(statusCode).json({ 
      error: 'Failed to communicate with GLM API',
      details: error.response?.data || error.message || 'Unknown error'
    });
  }
} 