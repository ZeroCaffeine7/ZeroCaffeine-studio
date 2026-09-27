# 运行 PoC Demo

本说明介绍如何在本地把 PoC 启动为一个可演示的程序（后端 + 前端静态页面）。

要求

- Python 3.10+
- Git

快速启动

1. 克隆并切换到 poc 分支：

   git clone https://github.com/ZeroCaffeine7/ZeroCaffeine-studio.git
   cd ZeroCaffeine-studio
   git checkout poc/multi-agent-studio

2. 运行一键启动脚本（Unix/macOS）：

   chmod +x start_demo.sh
   ./start_demo.sh

   - 后端 (FastAPI) 将在 http://localhost:8000
   - 前端静态页面将由 Python http.server 提供在 http://localhost:8080/index.html

3. 打开浏览器：

   - 前端演示： http://localhost:8080/index.html
   - API 文档：   http://localhost:8000/docs

交互流程（在前端页面）

- “创建示例项目”：在后端创建一个示例 project
- “批量生成任务”：为项目创建 12 个 chunk 任务
- “注册 Workers”：注册若干 level_design worker
- “Dispatch”：把 new 状态任务分配给空闲 worker
- （对于 PoC，我们用手动合并）“Merge”：Manager 触发合并并检测冲突

注意

- 当前 Demo 使用内存数据存储（重启服务会丢失数据）
- 若要在团队中分享，请使用 docker-compose 部署或移植到服务器

下一步建议

- 把前端升级为 React/Vite 并做更丰富的交互
- 用 worker 模拟器自动执行任务（便于展示并发）
- 把数据持久化到 Postgres 并使用 Redis/Kafka 做队列
