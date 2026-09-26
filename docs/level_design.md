# Level Design Department (试点)

本文件为 Level Design 部门的详细设计与可执行模版，作为 PoC 的第一个试点部门。内容包含：组织角色、任务拆解模板、微任务样例、合并规则、自动化 QA 与示例 JSON，可直接导入 PoC 系统进行演示。

目标
- 将“做一张大地图/第一关”拆成可并行执行的 microtasks
- 支持主管（Manager）将任务分配给多个 worker（AI/human）并行执行
- 支持冗余执行（N-way）并用合并/投票/合成策略产出最终稿
- 提供 QA 自动检测与人工抽查流程

组织角色（Level Design 部门）
- WorldDesigner (Manager)
  - 职责：总体拆分、跨区连续性检查、合并与最终验收
- LevelDesigner (Worker)
  - 职责：负责若干区块（chunk）的地形、流程与 encounters
- EncounterDesigner (Worker)
  - 职责：设计区块内关键战斗/事件点（敌人、陷阱、谜题）
- TileAssembler (Worker)
  - 职责：把多个区块的地形与艺术资源拼接成可用 tilemap/scene
- PlaytestAgent / QA (Auto + Human)
  - 职责：运行自动化可玩性测试、检查连通性和性能问题

拆解策略
- 先把地图按“区块（chunk）”划分，chunk 数量由地图规模决定（例如：小图 20、 中图 200、 大图 2000）
- 每个 chunk 定义为独立 microtask，包含：地形要点、关键 POI、入口/出口连接点
- 对关键区域（boss room、城镇、关卡交汇处）设置冗余 factor=3（3 个独立 worker 输出）
- 每个 chunk 由对应的 LevelDesigner 输出初稿，EncounterDesigner 输出敌人/事件表，TileAssembler 输出拼接建议

microtask schema（JSON）
{
  "task_id": "chunk-001",
  "project": "Mist Dungeon - Level 1",
  "chunk_index": 1,
  "bounds": {"x":0, "y":0, "w":64, "h":64},
  "instructions": "生成该区块的地形要点、3 个兴趣点(POI)、推荐敌人类型和巡逻路线，标注入口/出口与高度差",
  "role": "level_design",
  "redundancy": 1
}

示例拆解流程（WorldDesigner）
1. 接收 project brief 和地图总体参数（尺寸、难度、主题）
2. 计算 chunk 划分并为每个 chunk 生成 microtask（含 role、priority、redundancy）
3. 下发到 Department Queue（按 role 分片）

Worker 执行模板
- LevelDesigner 输出：
  - chunk_id
  - layout_summary (简短文本)
  - poi_list: [ {"name":"Ancient Gate","type":"puzzle","pos":{x,y}} ]
  - connectors: {"north":"chunk-0002","east":"chunk-0005"}
  - artifacts: ["tilemap-v1.png"]
- EncounterDesigner 输出：
  - enemy_list: [{"type":"Ghoul","count":6,"behavior":"patrol"}]
  - spawn_table: ...
- TileAssembler 输出：
  - stitch_notes: 文本
  - asset_refs: [s3://...]

合并规则（Manager）
- 如果 redundancy=1：直接采纳 worker 输出
- 如果 redundancy>1：
  - 自动投票：对结构化字段（poi names, connector ids）进行多数表决
  - 文本合成：使用合成模型（Synthesis tier）把多个草案合成为 1 个连贯描述
  - 连通性检查：检测相邻 chunk 的 connectors 是否一致，若不一致生成修复子任务

自动 QA & Playtest
- 运行自动可玩性脚本：从入口出发，检查是否能到达主要 POI、是否有孤岛区
- 性能检测脚本：估算 chunk 的渲染负荷（基于 asset_refs）
- 抽样人工审查：对每 50 个 chunk 抽样 1 个人工复核

任务状态流（stage）
- new -> assigned -> in_progress -> completed -> merged -> qa_failed/qa_passed -> reviewed

API/操作举例
- POST /projects -> 创建 project
- POST /projects/{id}/dispatch?chunks=200 -> WorldDesigner 生成 200 个微任务
- GET /tasks?project_id=...&role=level_design -> 拉取队列
- POST /tasks/{id}/result -> worker 提交结果
- POST /projects/{id}/merge -> Manager 合并并触发 QA

Metrics & Scaling
- 每个 LevelDesigner worker 处理速度：约 5-20 microtasks/小时（取决于 prompt 与模型）
- 并行策略：使用 K8s autoscale 将 worker pool 大小按队列长度扩缩
- 成本控制：把第一轮草稿分配给 Draft-tier 模型，汇总时使用 Synthesis-tier，再用 Review-tier 做抽样复核

示例：把地图分为 100 个 chunk
- 100 个 LevelDesigner microtasks
- 100 个 EncounterDesigner microtasks
- 50 个 TileAssembler microtasks
- QA: 自动 playtest 覆盖 100% + 人工抽样 2%

---

请确认该 Level Design 部门模版是否满足你的期望，或指出你想优先调节的参数（例如 chunk 大小、冗余因子、抽样率）。
