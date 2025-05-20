import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import styles from '../styles/Weiwei.module.css';

export default function Weiwei() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/weiwei', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        console.error('Error:', data.error);
        setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，我现在无法回应。请稍后再试。' }]);
      }
    } catch (error) {
      console.error('Fetch error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: '网络错误，请检查您的连接。' }]);
    } finally {
      setIsLoading(false);
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
                  className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.botMessage}`}
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
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className={styles.sendButton}
              disabled={isLoading || !input.trim()}
            >
              发送
            </button>
          </form>
        </div>
      </main>
    </>
  );
} 