import React from 'react';
import { NextPage } from 'next';

interface ErrorProps {
  statusCode?: number;
  message?: string;
}

const Error: NextPage<ErrorProps> = ({ statusCode, message }) => {
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
      <h1 style={{ marginBottom: '20px', color: '#333' }}>
        {statusCode
          ? `发生错误: ${statusCode}`
          : '发生客户端错误'}
      </h1>
      <p style={{ marginBottom: '30px', color: '#666' }}>
        {message || '我们正在努力解决这个问题，请稍后再试'}
      </p>
      <button 
        onClick={() => window.location.href = '/'}
        style={{
          padding: '10px 20px',
          background: '#1e88e5',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          marginRight: '10px'
        }}
      >
        返回首页
      </button>
      <button 
        onClick={() => window.location.reload()}
        style={{
          padding: '10px 20px',
          background: 'transparent',
          color: '#1e88e5',
          border: '1px solid #1e88e5',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        刷新页面
      </button>
    </div>
  );
};

Error.getInitialProps = ({ res, err }) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
  return { statusCode };
};

export default Error; 