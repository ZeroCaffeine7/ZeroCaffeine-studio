# 架构扩展：公司组织与部门扩展

此文档描述如何将 PoC 扩展为公司级 AI 游戏工作室的组织结构、部门模板与管理比率，面向后续在系统中实现自动化调度、分片与大规模并行执行。

目标：支持每个部门从几十人扩展到数百、上千名 worker（AI 实例或人类），并保证可追溯、可恢复、成本可控。

1. 顶层组织
- Studio（公司）
  - Projects（项目线）
  - Departments（部门：LevelDesign / Enemy / Art / Narrative / QA / Programming / Ops / Marketing）
  - Platform Services（Orchestration / ModelPool / Storage / Observability）

2. 部门与角色模板（示例）
- Level Design
  - Manager: WorldDesigner
  - Roles: LevelDesigner, TileAssembler, EncounterDesigner
  - 建议规模：试点 1 Manager:20 Workers → 可扩展到 1:200（资产批量生成场景）

- Enemy Design
  - Manager: CombatLead
  - Roles: EnemyDesigner, BehaviorScripter, BalanceTuner
  - 建议规模：1 Manager:20-100 Workers（复杂数值调整需要更多 Manager）

- Art
  - Manager: ArtLead
  - Roles: ConceptArtist, TextureGenerator, AssetAssembler
  - 建议规模：传统艺术更多人工/审核，AI 辅助下 1:50-200

- QA
  - Manager: QA Lead
  - Roles: AutoTester, PlaytestAgent, RegressionChecker
  - 建议规模：1 Manager:100-500 AutoTester（自动化） + 抽样人工审查

3. 管理层级与比率（推荐）
- Worker 类型区分：High-parallel（Assets/Textures）、High-judgement（Game Design/Balance）
- 推荐 Manager:Worker 比例：
  - 高并行：1:200–500
  - 高判断：1:20–100
- Supervisor 层：每 5–20 Manager 再上升一层 Supervisor 负责跨经理冲突与里程碑验收

4. 调度与分片建议
- Project 分片：按地理（map chunk）或功能（AI、Art、SFX）分片
- 每个 Department 使用独立队列（减小互相影响）
- 使用 Workflow 引擎（Temporal）管理 DAG 与补偿逻辑

5. 冗余与合并策略
- 关键子任务使用 N-way redundancy（N=2..5），合并策略采用 Weighted Merge / Voting / Synthesizer
- 历史评分（Worker Rating）用于加权合并

6. 绩效与评分系统
- 每个 worker（AI 实例/人）记录评分：质量、速度、可靠性
- Manager 根据评分调整调度权重与冗余因子

7. 成本控制要点
- 模型分层（Draft / Synthesis / Review）减少 expensive calls
- 批量化与缓存常见 prompts
- 将高频任务迁移到本地推理集群

8. 安全与合规
- 强制对对外交付的产物做人工审核（IP、法律、品牌风险）
- 保存完整审计链（prompt、model、seed、版本）以便回溯

9. 里程碑与渐进实施
- 阶段 0（试点）：完成 Level Design 部门 PoC（1 Manager + 4 角色）
- 阶段 1：扩展到 1 Manager:50 Workers（自动化 asset 生成）
- 阶段 2：多部门并行（Level + Enemy + Art + QA），引入 Temporal
- 阶段 3：规模化（数百/上千 worker），引入 Kafka、Autoscaling、GPU 池

---

请告诉我你希望我们先以哪个部门为试点（推荐：Level Design），我会基于该部门创建更详细的拆分模版、任务 schema 与前端页面样式。