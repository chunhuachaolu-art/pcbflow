# NEXT.md — pcbagent 工具链会话状态（每会话收尾**重写**本文件，保持 ≤50 行）

## 下一步

- **DONE —— 工具链 B1–B5 全部交付（S5 收尾，2026-08-29，规划方裁决 a）**
- 本工具链不再有后续强制会话；无需再按本文件启动新 S 会话
- 残网收口 = GUI 人工会话：按 `<工程>/pcbagent-out/gui-session-kit/README.md`
  施工（7 信号批 + 1 GND 批，每批落盘后跑 `verify` 回归门）
- F4 等长 / F5 制板不在工具链范围（GUI 调谐；`length`/`render`/
  `audit-checklist` 是其输入）
- 可选后续（由规划方决定，均不影响 Rev-C）：S6=B6 布局闭环（SPEC §3.5，
  服务未来板）；SW_NODE 类 ripup 启用前先补 B1「信号铺铜重灌」探针

## 门状态表（终局）

| 门 | 状态 | 证据 |
|---|---|---|
| B1：L1 vs kicad-cli 100% 一致 | **PASS**（25/25） | `out/b1/b1-gate-report.json` |
| B2：拥塞回验 ≥70% + 3V3 ≥15/22 | **PASS**（57/61、59/61、21/22） | `out/b2/gate.json` |
| B3：实战（裁决 a 改口径：零新增+上界尽收 8/8+施工包） | **PASS** | `PHASE-REPORT-4.md` + `<工程>/pcbagent-out/b3/` |
| B4：四命令全通 + length 对账 | **PASS**（对账 113 项逐键一致） | `out/b4/b4-gate-report.json` |
| B5：gui-session-kit | **交付**（53 信号+4 GND，46/53 有走廊） | `<工程>/pcbagent-out/gui-session-kit/` |

## 关键指针

- 最终中文报告（各门数字/偏离清单/残网原因）：`PHASE-REPORT-5.md`
- 板态：Rev-C = 战前 + 8 条 3V3 分支；fresh DRC 与 final/baseline 逐键一致
  （10 既有 violations，unconnected 57）——`out/b4/s5-drc-recheck.log`
- 新命令：verify（基线 diff 回归）/ length / render / audit-checklist；
  生成器 `tests/run_b5_kit.py`；README 已同步
- 残网施工包：`<工程>/pcbagent-out/gui-session-kit/`（走廊图+分批清单+
  每批 verify 命令）

## 约束提醒（GUI 会话/可选后续必读）

- GUI 施工每批保存后必跑 `python -m pcbagent.cli verify --project <工程>`
  （首跑自动建基线；回归=新增违规才算失败）
- L1 已知盲区：信号铺铜（5V pour）vs 新孔的重灌语义未建模——SW_NODE 不在
  工具自动提交集；人工 GUI 施工不受影响（KiCad 自动重灌+板内 DRC）
- DRC 只走 kicad-cli（工程目录 + refill+save 口径）；同一时刻仅一个会话操作
  工程；PROGRESS.md 只追加；禁随机性；禁为凑数放宽规则
