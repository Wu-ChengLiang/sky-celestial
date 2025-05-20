import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import styles from '../styles/Weiwei.module.css';

export default function Weiwei() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected'); // 'connected', 'reconnecting', 'disconnected'
  const [retryCount, setRetryCount] = useState(0);
  const messagesEndRef = useRef(null);
  const MAX_RETRIES = 3;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check server connection on mount and periodically
  useEffect(() => {
    // Simple ping function to check connectivity
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/ping', { 
          method: 'GET',
          cache: 'no-store',
          headers: { 'Cache-Control': 'no-cache' }
        });
        
        if (response.ok) {
          if (connectionStatus !== 'connected') {
            setConnectionStatus('connected');
            console.log('Connection restored');
          }
        } else {
          setConnectionStatus('disconnected');
        }
      } catch (error) {
        console.warn('Connection check failed:', error);
        setConnectionStatus('disconnected');
      }
    };

    // Check connection immediately and then every 30 seconds
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, [connectionStatus]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    const currentInput = input;
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setRetryCount(0);

    await sendMessage(currentInput);
  };

  const sendMessage = async (messageText, isRetry = false) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout

      const response = await fetch('/api/weiwei', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      const data = await response.json();

      if (response.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        setConnectionStatus('connected');
      } else {
        console.error('Error:', data.error);
        
        // If server is experiencing problems but we can still communicate
        if (response.status >= 500) {
          handleServerError(messageText);
        } else {
          // Other errors like 400s
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            content: `抱歉，发生了错误: ${data.error || '未知错误'}` 
          }]);
        }
      }
    } catch (error) {
      console.error('Fetch error:', error);
      
      // Network errors (connection lost, timeout, etc)
      if (error.name === 'AbortError') {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: '请求超时，服务器可能繁忙，请稍后再试。' 
        }]);
      } else {
        handleServerError(messageText);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleServerError = (messageText) => {
    if (retryCount < MAX_RETRIES) {
      // Attempt to reconnect
      setConnectionStatus('reconnecting');
      setMessages(prev => [...prev, { 
        role: 'system', 
        content: `连接出现问题，正在尝试重新连接... (${retryCount + 1}/${MAX_RETRIES})` 
      }]);
      
      // Exponential backoff for retries (1s, 2s, 4s)
      const backoffTime = 1000 * Math.pow(2, retryCount);
      
      setTimeout(() => {
        setRetryCount(prev => prev + 1);
        setIsLoading(true);
        sendMessage(messageText, true);
      }, backoffTime);
    } else {
      setConnectionStatus('disconnected');
      setMessages(prev => [...prev, { 
        role: 'system',
        content: '服务器连接失败，请刷新页面或稍后再试。'
      }]);
    }
  };

  const getStatusIndicator = () => {
    switch(connectionStatus) {
      case 'connected':
        return <div className={`${styles.statusIndicator} ${styles.connected}`}>服务正常</div>;
      case 'reconnecting':
        return <div className={`${styles.statusIndicator} ${styles.reconnecting}`}>正在重连</div>;
      case 'disconnected':
        return <div className={`${styles.statusIndicator} ${styles.disconnected}`}>
          服务不可用 <button onClick={() => window.location.reload()}>刷新</button>
        </div>;
      default:
        return null;
    }
  };

  return (
    <>
      <Head>
        <title>薇薇 - 聊天界面</title>
        <meta name="description" content="与阿良的仿生人聊天" />
      </Head>

      <main className={styles.container}>
        <h1 className={styles.title}>薇薇的电子小狗</h1>
        {getStatusIndicator()}
        
        <div className={styles.chatContainer}>
          <div className={styles.messages}>
            {messages.length === 0 ? (
              <div className={styles.welcome}>
                <p>你好！我是薇薇的电子小狗，像阿良一样陪你聊天。</p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div 
                  key={index} 
                  className={`${styles.message} ${
                    msg.role === 'user' 
                      ? styles.userMessage 
                      : msg.role === 'system' 
                        ? styles.systemMessage
                        : styles.botMessage
                  }`}
                >
                  <div className={styles.messageContent}>{msg.content}</div>
                </div>
              ))
            )}
            {isLoading && (
              <div className={`${styles.message} ${styles.botMessage}`}>
                <div className={styles.loading}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className={styles.inputForm}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入消息..."
              className={styles.input}
              disabled={isLoading || connectionStatus === 'disconnected'}
            />
            <button 
              type="submit" 
              className={styles.sendButton}
              disabled={isLoading || !input.trim() || connectionStatus === 'disconnected'}
            >
              发送
            </button>
          </form>
        </div>
      </main>
    </>
  );
} 