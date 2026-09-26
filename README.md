# ZeroCaffeine Studio

ZeroCaffeine Studio 是一个面向复杂游戏开发的 AI 工作室平台。

它的目标不是仅仅让单个 AI 作为一个“聊天助手”，而是让一个“老板”可以提交复杂需求，并让系统自动拆解任务，分配给多个 AI/人类员工协同完成。系统支持多层管理结构：

- 老板 / 业务负责人：提交需求、审批成果、提供反馈
- 主管 / Manager：拆分任务、分配给角色、统一交付
- 员工 / Worker：执行具体工作，如策划、程序、艺术、音效、测试、运营等
- 中间层 / Coordinator：管理任务队列、权限、优先级、调度、审计

这个平台适合做“AI 游戏工作室”，且可以扩展成复杂的多人协作场景，而不只是单机 AI 生成内容。

设计目标

1. 把复杂需求拆成可执行任务
2. 自动分配给多个子角色执行
3. 多层经理负责汇总、复核与质量控制
4. 支持并发工作流、优先级、反馈闭环
5. 允许未来扩展为真实多人工作室（AI + 人类协同）

项目结构

- docs/architecture.md：系统架构与设计文档
- docs/agent_roles.md：角色设计与职责定义
- backend/: 后端服务
  - app/: FastAPI / Express 入口
  - agents/: Manager / Worker / Coordinator 逻辑
  - services/: 任务调度、队列、模型适配、日志
  - models/: 数据模型
- frontend/: 前端面板（老板仪表盘 / 主管视图 / 员工视图）
- infra/: Docker / 环境部署配置
- examples/: 示例任务与流程

推荐技术栈

- Backend: Python + FastAPI（适合 AI/LLM 集成），或 Node.js + TypeScript
- Database: PostgreSQL
- Queue / Event Bus: Redis + Celery / BullMQ
- Vector DB: Weaviate / Milvus / FAISS（可选，用于知识库与记忆）
- Frontend: React + Vite
- AI access: OpenAI-like APIs / local LLM adapters

核心思想：不是单 AI，而是 AI 工作室

对你这个思路来说，最关键的不是“一个 AI 能回答一个问题”，而是：

- 一张地图开发，不是一个开发者做完，而是多个负责人协作
- 地图设计、关卡布局、敌人设计、数值配置、视觉风格、音效、测试、优化分别由不同角色来做
- 主管负责把复杂项目拆成任务，让不同员工并行执行
- Boss 只面对最终结果和审批，而不关心底层执行细节

这就像一个真实游戏公司：

- CEO/Boss：提出目标、审批、控制资源
- 项目经理：拆分项目、追踪进度
- 设计师：机制、剧情、玩法规划
- 程序员：功能实现、脚本、优化
- 画师：视觉风格、资源制作
- 测试：BUG 检查、细节修正
- 运维/平台：部署、监控、数据分析

接下来要做的扩展

这个项目的下一步，不是做一个单人 AI 助手，而是做一个“多层 AI 管理结构”。

建议按以下层级扩展：

1. Boss Layer
   - 提交 game brief
   - 设置目标、预算、时间、质量要求
   - 审批任务成果

2. Manager Layer
   - 将项目拆为多个子任务
   - 分配给不同角色
   - 检查中间产物
   - 最终输出成品

3. Worker Layer
   - Level Designer
   - Story Designer
   - Programmer Agent
   - Test Agent
   - UI/UX Agent
   - Sound Agent
   - Marketing Agent
   - etc.

4. Ops / Infrastructure Layer
   - 调度器
   - 日志审计
   - 任务状态管理
   - 权限控制
   - 成本管理

最小可运行 MVP

MVP 不用一开始做成完整工作室，而是先做：

- Boss 提交任务
- Manager 自动拆分任务
- 至少 2-3 个角色 Worker 执行
- Manager 汇总结果
- Boss 审核

例如：

任务：做一个《迷雾副本》的第一关

拆为：
- LevelDesigner：地图布局
- EnemyDesigner：敌人配置
- NarrativeDesigner：背景叙事
- QA：测试可玩性

Manager 汇总输出，并提供“可交付版本”。

这才符合你要的“复杂、多人协作、可扩展”的思路。

接下来如果你愿意，我可以继续直接在这个仓库里补：

- docs/architecture.md
- docs/agent_roles.md
- backend/app/main.py
- backend/agents/manager.py
- backend/agents/worker.py
- backend/services/task_queue.py
- frontend/README.md

并设计一个真实的任务工作流，支持“老板提交任务 → 主管拆分 → 员工执行 → 主管汇总 → 老板审批”的闭环。
