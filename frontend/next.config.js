/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    images: {
      unoptimized: true, // 必须添加！禁用图片优化
      domains: [], // 保留空数组
      deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048]
    },
    // 完全删除 telemetry 相关配置
  }

module.exports = nextConfig 