# PCBFLOW V5 发布证据包 · evidence-manifest（成包件 sha 清单+版本锚+读数绑定表）

- 批次：PCBFLOW-V5-EVIDENCE-R1（C5）；生成 2026-10-19；发布阶段=**draft-1（两段式第一段=内部定格版草案，不 tag 不外发；tag 属 C8）**
- 权威链：任务书 PCBFLOW-V5-EVIDENCE-R1-TASKBOOK-2026-10-19 → 设计件 §3.4 → 台账正本 §2（证据锚基准）→ M0 批复登记节（G3 措辞原文）
- 纪律：一切 sha256/计数程序化现算注入（沙箱 out/evidence-hashes.json 机读总表）；本包引用值均经本批复算；LF/utf-8。

## 1. 版本锚

| 锚 | 值 | 源（实测） |
|---|---|---|
| executor | `v5.executor/0.11.0` | route-v5 `v5/executor.py:351` `EXECUTOR_VERSION = "v5.executor/0.11.0"` |
| postprocess | `v5.postprocess/2.1.0` | route-v5 `v5/postprocess.py:117` `POSTPROCESS_VERSION = "v5.postprocess/2.1.0"` |
| route-v5 HEAD | `9389787587b6922dbdc4a2d31d5de58b2ab93f82` | 开工探盘实测（branch=main，porcelain 恰三件 r 系白名单：a6x_run_c1c2.py/r9e3_run.py/r9e4_run.py） |
| 套件仓 HEAD | `f0fedf3d7a397a84a40ff97b3b02067342b97d72` | 开工探盘实测（workspace 仓；写面两件 M=baseline.json+exec-r5 台账，余为批目录 untracked） |

## 2. 处置名册件（失败证据门现行形态）

| 件 | 板数 | bytes | sha256 |
|---|---|---|---|
| `<ENGINE_ROOT>/out/v5-p5/p5-gate/dispositions-r1-2026-09-28.json` | 10 | 5618 | `08d3370d10401a5071ceed5b2594f957d96988240af0bad69680521cc9aa2197` |
| `<ENGINE_ROOT>/out/v5-p5/p5-gate/dispositions-2026-09-23.json` | 8 | 3346 | `72c84c34133cc494d48ad94bc7e751a9908e2db2f28a9a8f3dd2b1d9562d8e74` |

## 3. 记分牌与门读数件

| id | 件 | bytes | sha256 | 说明 |
|---|---|---|---|---|
| S09_gate_r1 | `<ENGINE_ROOT>/out/v5-p5/p5-gate/r1-2026-09-28b/gate-report.json` | 19932 | `db76d7965be43f67b1ec1299accb65c374146969fbef968dd6bd6f8a04ce3736` | R1 gate（判据一/判据二/可布域/名册分母机读源） |
| S10_gate_r2 | `<ENGINE_ROOT>/out/v5-p5/p5-gate/r2-2026-09-24/gate-report.json` | 18292 | `03aaf3a0517c5a0bda8d0a3af49de7751b2c252696672de27e371974a6f01ed9` | R2 gate（旧世代历史对照，OPT-01 纪律不得挪用补数） |
| S11_scoreboard_b | `<ENGINE_ROOT>/out/v5-p5/r1/R1-SCOREBOARD-REBASE-2026-09-28B.json` | 2373 | `fe90b8679dbeb3f5564c14464aeb54a3a56b49e6c4344b69a7a87978faefb631` | 记分牌 B 版（主值 4/4+并记 4/6+W-D 直读 4/4） |
| S12_wd_direct | `<ENGINE_ROOT>/out/v5-p5/r1/w6d-g1-direct-read.json` | 3655 | `8371a388fd53d81e1e6e95da44115f3b2d82d9809a926214b31cf070d560cdc8` | W-D 重跑面直读（ED-X 呈裁期披露口径 4/4） |
| S13_s5_01_scoreboard_md | `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/packages/s5/s5-01-scoreboard.md` | 10541 | `b06c8e7fae5b015715a3ef80f4dc58a434b204b45b12d39361dcfc6d2db480a3` | S5-01 分母闭合核验报告（board hash 三向闭合 12/12 口径全等） |
| S14_s5_01_results | `<DATA_ROOT>/tmp/optimap-s5/s5-01/s5-01-results.json` | 25997 | `fd095648043691dbfa5da793c236ad52f095ac1bc34b132bd988fa66701147fc` | S5-01 机读结果件（沙箱单副本，随包登记） |

## 4. 读数绑定表（OPT-01 纪律：executor/world/board/schema/candidate hash 五绑定，逐读数行）

### R1 判据一（原口径）n_sat vs require 5 = 4/5（并记=SCOREBOARD-B 4/4 主值+4/6 六板全量）
- 读数：`{"n_sat": 4, "require": 5, "pass": false}`
- 证据：S09 g1.criterion_1_sat_ge_5 + S11 calibers + S13 §3.2 口径对照 12/12
- executor：v5.executor/0.8.0（评估器）
- world：executor 0.8.0(V5-R1 Steiner 拓扑换版)/route_check 0.4.1(ED-2 PTH union 修复，09-26 R-A)/kicad_export 0.5.0(ED-X 修复批，09-27)（R1 世界产物树；W-D 四板=W-D 重跑+ED-X 修复批 check,export,drc 补跑面，其余板按各自落盘时点；7 块已处置 board-inherent 板 R1 未重跑=convert-only 形态）
- board：gate 17 板集（SAT 4：badgeleds-do-electronics/pmod-crypto/thatmicpre-v2/thin-pod）
- schema：build_p5_gate.py G1-G5（r1-2026-09-28b gate-report.json）
- candidate hash：A_LAYER_PREREG 24 板 sha256（route-v5 tools/p5_holdout_ledger.py:51；S5-01 三向核验 17/17 全等=board.json.source_sha256↔prereg↔源 kicad_pcb 实算）

### R2 判据二干净板（微段豁免后）= 4/5
- 读数：`{"n_clean": 4, "require": 5, "pass": false, "genuine_outstanding": 0, "microseg_exempt_total": 6}`
- 证据：S09 g1.criterion_2_zero_violation + S26d :97 重算一致
- executor：v5.executor/0.8.0（评估器）
- world：executor 0.8.0(V5-R1 Steiner 拓扑换版)/route_check 0.4.1(ED-2 PTH union 修复，09-26 R-A)/kicad_export 0.5.0(ED-X 修复批，09-27)（R1 世界产物树；W-D 四板=W-D 重跑+ED-X 修复批 check,export,drc 补跑面，其余板按各自落盘时点；7 块已处置 board-inherent 板 R1 未重跑=convert-only 形态）
- board：gate 17 板集（干净板 4，同判据一 SAT 名单）
- schema：criterion_2_zero_violation（微段豁免类 track_dangling<0.06mm 计入豁免）
- candidate hash：A_LAYER_PREREG 24 板 sha256（route-v5 tools/p5_holdout_ledger.py:51；S5-01 三向核验 17/17 全等=board.json.source_sha256↔prereg↔源 kicad_pcb 实算）

### R3 R1 可布域（(c) 豁免后）SAT 主值 = 4/4
- 读数：`{"numerator": 4, "denominator": 4, "pass": true}`
- 证据：S11 calibers[0]（主值）
- executor：v5.executor/0.8.0（评估器）
- world：executor 0.8.0(V5-R1 Steiner 拓扑换版)/route_check 0.4.1(ED-2 PTH union 修复，09-26 R-A)/kicad_export 0.5.0(ED-X 修复批，09-27)（R1 世界产物树；W-D 四板=W-D 重跑+ED-X 修复批 check,export,drc 补跑面，其余板按各自落盘时点；7 块已处置 board-inherent 板 R1 未重跑=convert-only 形态）
- board：17−弃3−名册10=4（域内零 FAILED）
- schema：R1-SCOREBOARD-REBASE-2026-09-28B calibers
- candidate hash：S07 名册 10 板 sha=08d3370d10401a50…

### R4 R1 六板全量口径并记 = 4/6
- 读数：`{"numerator": 4, "denominator": 6, "failed_in_domain": ["pmod-bme280", "tmp108"]}`
- 证据：S11 calibers[1]
- executor：v5.executor/0.8.0（评估器）
- world：executor 0.8.0(V5-R1 Steiner 拓扑换版)/route_check 0.4.1(ED-2 PTH union 修复，09-26 R-A)/kicad_export 0.5.0(ED-X 修复批，09-27)（R1 世界产物树；W-D 四板=W-D 重跑+ED-X 修复批 check,export,drc 补跑面，其余板按各自落盘时点；7 块已处置 board-inherent 板 R1 未重跑=convert-only 形态）
- board：17−弃3−固有8=6（bme280+tmp108 留分母计 FAILED）
- schema：R1-SCOREBOARD-REBASE-2026-09-28B calibers
- candidate hash：A_LAYER_PREREG 24 板 sha256（route-v5 tools/p5_holdout_ledger.py:51；S5-01 三向核验 17/17 全等=board.json.source_sha256↔prereg↔源 kicad_pcb 实算）

### R5 W-D 重跑面直读 = 4/4
- 读数：`{"n_sat": 4, "denominator": 4}`
- 证据：S12（ED-X 呈裁期披露口径）
- executor：v5.executor/0.8.0（评估器）
- world：executor 0.8.0(V5-R1 Steiner 拓扑换版)/route_check 0.4.1(ED-2 PTH union 修复，09-26 R-A)/kicad_export 0.5.0(ED-X 修复批，09-27)（R1 世界产物树；W-D 四板=W-D 重跑+ED-X 修复批 check,export,drc 补跑面，其余板按各自落盘时点；7 块已处置 board-inherent 板 R1 未重跑=convert-only 形态）（W-D 四板=W-D 重跑+ED-X 修复批补跑面）
- board：W-D 四板
- schema：全端点连通口径 route_check 0.4.1（plated 孔筒连通计入）
- candidate hash：A_LAYER_PREREG 24 板 sha256（route-v5 tools/p5_holdout_ledger.py:51；S5-01 三向核验 17/17 全等=board.json.source_sha256↔prereg↔源 kicad_pcb 实算）

### R6 R2 可布域 SAT = 6/6（历史对照，不外推）
- 读数：`{"n_sat": 6, "denominator": 6, "pass": true}`
- 证据：S10（09-23 旧引擎世代读数；OPT-01 纪律降历史对照）
- executor：v5.executor/0.7.0（评估器）
- world：executor 0.5.0(+R1/NUMBA 性能件)/route_check 0.3.0/drc 0.2.0/run_p5_board 0.4.0/kicad_export 0.4.0
- board：17−弃3−名册8=6
- schema：build_p5_gate.py G1-G5（r2-2026-09-24 gate-report.json）
- candidate hash：S08 名册 8 板 sha=72c84c34133cc494…

### R7 套件全量 = 3884 collected = 3880 passed + 4 xfailed，0F/0E，EXIT=0
- 读数：`{"passed": 3880, "xfailed": 4, "failed": 0, "errors": 0, "skipped": 0, "warnings": 3, "collected": 3884, "duration_s": 2705.38, "exit_code": 0, "window": ["2026-10-17T22:51:15+08:00", "2026-10-17T23:36:22+08:00"]}`
- 证据：S04 §3 全量双照+§6 机器 JSON（本批复算两修复件 sha 与登记值逐位同）
- executor：v5.postprocess/2.1.0（套件内 postprocess 线）
- world：套件仓（workspace）HEAD=f0fedf3d7a397a84a40ff97b3b02067342b97d72；pytest.ini 口径 cwd=tools/pcbflow
- board：n/a（套件面，无板）
- schema：pytest collect/断言口径+baseline.json total_collected=3884
- candidate hash：修复件 sha=3cae449203a665f1… / 845389da81b21513…（本批复算一致）

### R8 A 板（HR1-BOARD-A）orig 引擎面五字段双跑
- 读数：`{"five_fields": {"failed_nets": 0, "negotiation_rows": 1434, "ok_nets": 57, "routes": 0, "status": null}, "canonical_sha256": "be49db64d61faab29aec7539d448f874784de2f325f0d3bee58b4c9ae8c619a0", "walls_s": [30843.927, 37303.324]}`
- 证据：S05 §0/§3 + S21b/S21c/S21d（J1 双跑字节等；J2 对 0.9.0 锚逐位等）
- executor：v5.executor/0.11.0
- world：route-v5 HEAD 93897875 (executor 0.11.0 era)
- board：HR1-BOARD-A:orig:baseline（恰 2 跑）
- schema：五字段 canonical（AENG-R2 prereg §2 冻结定义；wall 剔除门沿 A6X/R9-E3 先例）
- candidate hash：five_field_canonical_sha256=be49db64d61faab29aec7539d448f874784de2f325f0d3bee58b4c9ae8c619a0

### R9 judge qualification G1..G5 = all_passed=true（+judge 线 sign-off=false 维持）
- 读数：`{"all_passed": true, "gates": {"G1": true, "G2": true, "G3": true, "G4": true, "G5": true}, "G1_precision": 0.6585365853658537, "G1_ci95_low": 0.47368421052631576, "G2_abstention_rate": 0.013550135501355014}`
- 证据：S18（qual-r2）+S19（对照零回归）+S15（R7-E2 未过门历史件 all_passed=false）
- executor：n/a（模型判读面，非引擎）
- world：R7-E3 qual-r2 会话（<DATA_ROOT>/tmp/optimap-exec-r7-e3/qual-r2/）
- board：Q/CTR 两臂×rep1-3×PIDS16（R7-E2 96 基读数+S18 根 99 件 rollup）
- schema：pcbflow.v4_2-jq-qualification-gate/1（PREREG §3.10 冻结值）
- candidate hash：qualification-gate.json sha=14922bbdaa357b15…；readings rollup=8b0c6dd030d555f3…

### R10 production sign-off = false（L2 面，永久门外）
- 读数：`{"production_signoff_ready": false}`
- 证据：S24 STATUS.md:9/:34（外部 SI/PI/热/EMC/DFM+板厂叠层未接）
- executor：n/a
- world：V2 层次二线从未启动面（DIAG §1.1）
- board：n/a
- schema：W STATUS.md 合入验收边界（≠生产签核）
- candidate hash：out/repair-p5/signoff-gap-checklist-r1.json（STATUS.md:34 锚）

## 5. A 板状态件（C2 归位）

- 终读（0.11.0 世代，恰 2 跑）：五字段 `{"failed_nets": 0, "negotiation_rows": 1434, "ok_nets": 57, "routes": 0, "status": null}`；canonical sha256=`be49db64d61faab29aec7539d448f874784de2f325f0d3bee58b4c9ae8c619a0`（本批自 run 件 canonical 串复算逐位同）；墙钟 30843.927s/37303.324s（43200s 帽内）；J1 双跑字节等 PASS；J2 对 0.9.0 锚 [1434,57,0] 逐位等 PASS_ANCHORED；milestone_c2=True
- 历史 0.9.0 对照行：五字段同值 {rows:1434, ok:57, failed:0, routes:0, status:null}；墙钟 40373.034/40373.051（R5 A:orig:baseline）与 31846.288（probe3 A baseline）——跨引擎世代五字段逐位等。

| 件 | bytes | sha256 |
|---|---|---|
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/prereg/PREREG-AENG-R2-FROZEN.md` | 6393 | `125507a348bad295f8824da025dd7bf275737337730ac7bd766ebac4278c279e` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/runs/run-1.json` | 581 | `323d3e94431c8b155699386b78d421ab6a789f8174eef946b44b6c6e4e859fbe` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/runs/run-2.json` | 582 | `48cb3056f60d21375f3eac5add0ffd7e077cef3d21fbbe505f4e41e37a0d9851` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/verdict-r2.json` | 6518 | `1fd4a34fd57d89edbd212e857fefb9e1494065191dd367164d056a7dd26b5a0a` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/g0-r2-verdict.json` | 990 | `2edce22e6f19856aadd1bbc40c8fcd6b281f6b8a003b04b45f055ac552161d88` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/close-probe-r2.json` | 7560 | `d05841f5e1bccdf00fe4e26cc918d399fbcc73432828c14da96c2bf519d1ce9f` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/engine-window.json` | 1640 | `86bf6e400070a2085ecb8899ec61021603863eb00ca1113af7fa424ff19796fd` |
| `<DATA_ROOT>/tmp/optimap-exec-aeng-r2/out/p0-probe-r2.json` | 2845 | `b20b6e3335da75aa3f2c3ed67ca7b94973ee8a2c0480c44527a1b14ddf65503f` |

## 6. judge qualification 证据收编清单

| 件 | bytes | sha256 | 读数 |
|---|---|---|---|
| `<WORKSPACE>/tools/pcbflow/out/v4.2-judge-qual-r1/qualification-gate.json` | 2947 | `48060e014551bbc4ff7cb76bb82c94adc17440f55a26f8b4a7d66f6bcf3531a6` | all_passed=False（G3/G4 未过=未过门历史件） |
| `<WORKSPACE>/tools/pcbflow/out/v4.2-judge-qual-r1/ledger.jsonl` | 48011 | `df4483b817b098b729e1da7f54b739ee412847092fd216a5322efba8e5b12d6f` | 171 行 append-only |
| `<WORKSPACE>/tools/pcbflow/out/v4.2-judge-qual-r1/readings`（目录） | 96 件 | rollup=`6fe30bef7188745ab5a355719f21227ddfe169a0ceaf4f0245e1ce4829dcf181` | 96 基读数=Q/CTR×rep1-3×PIDS16 |
| `<DATA_ROOT>/tmp/optimap-exec-r7-e3/qual-r2/qualification-gate.json` | 2924 | `14922bbdaa357b15d8da7c7a917eceada20c00245b2a32d778fb0b70cba388ff` | **G1..G5 all_passed=true**（precision=0.6585/CI95低=0.4737/abstention=0.0136） |
| `<DATA_ROOT>/tmp/optimap-exec-r7-e3/qual-r2/gate-comparison.json` | 1524 | `4f9ca34904bffa72cb5faa718463f700dca88f4b78147c311621cd437a462974` | 回归核对 regression=[] |
| `<DATA_ROOT>/tmp/optimap-exec-r7-e3/qual-r2/ledger.jsonl` | 31070 | `7b6ea2c09d2932745cc5fe951d644cb03a7ea48ba8b5702b12d54074ce9035fc` | 117 行 |
| `<DATA_ROOT>/tmp/optimap-exec-r7-e3/qual-r2/readings`（目录） | 99 件 | rollup=`8b0c6dd030d555f3849005d942ad8e0436c7ed4d869c8b7fe11ff926567c2c39` | 96 基读数+3 旁挂 retry |

（目录 rollup=对排序后 relpath:sha256 逐行拼接的 sha256；逐件 sha 存沙箱 out/evidence-hashes.json readings_r7e2/readings_r7e3.files。）

## 7. 套件面（C1 清面）

- 终读：全量 **3884 collected = 3880 passed + 4 xfailed，0 failed / 0 errors，EXIT=0，2705.38s**（窗 2026-10-17T22:51:15→23:36:22；warnings=3；skip=0 维持）。
- 修复件① `<WORKSPACE>/tools/pcbflow/baseline.json`：bytes=5961，sha256=`3cae449203a665f13a9bc2709f4c26b5ee4fc1213f06d81c3ea4da60b1201dbe`（PYFIX 登记值 `3cae449203a665f13a9bc2709f4c26b5ee4fc1213f06d81c3ea4da60b1201dbe`，本批复算**一致**）。
- 修复件② `<WORKSPACE>/tools/pcbflow/tests/test_v4_2_jq.py`：bytes=55226，sha256=`845389da81b21513968c26dae94847fa41e3a5994cd1499e0a215be12cdc355f`（PYFIX 登记值 `845389da81b21513968c26dae94847fa41e3a5994cd1499e0a215be12cdc355f`，本批复算**一致**）。
- sign-off 锚：`<WORKSPACE>/tools/pcbflow/STATUS.md`:9 与 :34 production_signoff_ready=false（外部 SI/PI/热/EMC/DFM+板厂叠层未接）。

## 8. G3 披露锚件

| 件 | bytes | sha256 |
|---|---|---|
| `<ENGINE_ROOT>/V5.0-DEV-TASKBOOK-2026-09-13.md` | 44941 | `417c5976191e78ff5d91292cfe56626e8924fbd33da5a6d5e5bab5a0f66b61b2` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/packages/PCBFLOW-OPTI-PKG-DIAG-R1-2026-10-07.md` | 240737 | `9b695d735c4a9014332a7b080d3dbc602eb10d60f3fbbf102577103da91f84e3` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/packages/FINAL-ROADMAP-2026-10-08.md` | 60760 | `0d966831237091feec9ec64996a4338853bd488aedd5933411941b211e57bc4d` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/packages/MECH-VERIFY-REPORT.md` | 99843 | `1c6c714e396ae128b88981466258f2ab047543c2b0fe17a3490fe7072b11a823` |

## 9. 上游输入正本

| 件 | bytes | sha256 |
|---|---|---|
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/exec-release-review/packages/V5-MILESTONE-DESIGN-R1.md` | 22123 | `b364732c0119e24d7598955ee41065f4c8534dbec0c43f2950309f22ce4a7ba4` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/exec-release-review/packages/V5-RELEASE-REVIEW-R1-REPORT.md` | 21014 | `2354aee48e5bd80b54ed8dfe458af13bfae818a720c1bf10381d759860879724` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/exec-release-review/DISPATCH-LOG.md` | 9331 | `86bf8c225e38c3138f7ad6d69e2275a56f721b91cc8424c1de8e33a1c27f5eaf` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/exec-pyfix/packages/EXEC-PYFIX-R1-REPORT.md` | 9654 | `a1d7065d74b3cc06ba0d5bc07366eddfe720d158d3d345c36ae367f65e79164d` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/exec-aeng/packages/EXEC-AENG-R2-REPORT.md` | 14561 | `b271209cf64bbc086ecdfd4fde0667538907f212564c3b13142565eace50be12` |
| `<WORKSPACE>/tools/pcbflow/pcbflow-optimap/exec-r9/packages/EXEC-R9-E4-REPORT.md` | 19468 | `6e357ba02b02656ce84d52a722f2a5efd5fb190f803d3ee7421fe71ee24f6c17` |

## 10. not_available 口径

- 本包无 not_available 项：A 板读数已归位（AENG-R2）、套件 0F（PYFIX-R1）、judge 证据收编齐；唯 R2 可布域 6/6 属 09-23 旧引擎世代历史对照（非现状主张）。

