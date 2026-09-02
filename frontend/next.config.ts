import type { NextConfig } from "next";

const isExport = process.env.DCA_EXPORT === "1";

const nextConfig: NextConfig = {
  // 单 exe 打包态（DCA_EXPORT=1）：静态导出，前端由后端 FastAPI 同源 serve（8000），
  // /api 直接命中后端，无需 rewrites。
  ...(isExport ? { output: "export" as const } : {}),
  // 开发/独立运行态：用 rewrites 把 /api 代理到本地 FastAPI（127.0.0.1:8000），避免跨域。
  ...(isExport
    ? {}
    : {
        async rewrites() {
          // 前端同源代理到本地 FastAPI（127.0.0.1:8000），避免跨域
          return [
            {
              source: "/api/:path*",
              destination: "http://127.0.0.1:8000/api/:path*",
            },
          ];
        },
      }),
};

export default nextConfig;
