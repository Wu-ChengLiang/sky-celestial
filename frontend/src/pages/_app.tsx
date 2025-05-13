import React, { ErrorInfo } from 'react';
import { AppProps } from 'next/app';
import '@/styles/globals.css';

interface ErrorState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

// 扩展AppProps以包含err属性
interface MyAppProps extends AppProps {
  err?: Error;
}

class MyApp extends React.Component<MyAppProps, ErrorState> {
  constructor(props: MyAppProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorState {
    // 更新状态，下次渲染时显示错误UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 可以记录错误信息
    console.error('应用错误:', error, errorInfo);
    this.setState({ errorInfo });
  }

  render(): React.ReactNode {
    const { Component, pageProps, err } = this.props;
    const error = err || this.state.error;
    
    // 如果有客户端渲染错误，显示备用错误UI
    if (this.state.hasError || error) {
      return (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: '#f8f9fa'
        }}>
          <h1 style={{ marginBottom: '20px', color: '#333' }}>抱歉，出现了问题</h1>
          <p style={{ marginBottom: '30px', color: '#666' }}>
            我们正在努力解决这个问题，请稍后再试
          </p>
          <button 
            onClick={() => window.location.reload()} 
            style={{
              padding: '10px 20px',
              background: '#1e88e5',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            刷新页面
          </button>
          {process.env.NODE_ENV === 'development' && (
            <div style={{ 
              margin: '30px 0', 
              textAlign: 'left', 
              background: '#f1f1f1', 
              padding: '15px',
              borderRadius: '4px',
              maxWidth: '800px',
              overflowX: 'auto'
            }}>
              <h2 style={{ fontSize: '16px', marginBottom: '10px' }}>错误详情 (仅开发模式可见):</h2>
              <p style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                {error?.toString()}
                {this.state.errorInfo?.componentStack}
              </p>
            </div>
          )}
        </div>
      );
    }

    // 正常渲染
    return <Component {...pageProps} />;
  }
}

export default MyApp; 