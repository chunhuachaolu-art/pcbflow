"""TL-2 advisory run 扩样批处理纯函数（S17；run-r2 选板）。

只承载确定性选板与批 manifest 的可测纯逻辑；渲染（kicad-cli 外部
工具链）与落盘由编排脚本 scripts/s17_run_r2.py 完成。

选板纪律（run-r2 确定性准则，禁止手挑）：
- 论域=pcbench-r1 语料的 **train split** profile（split 归属以
  profiles/<id>/manifest.json dataset_splits.train 为准）；
- 排除本轨道 critic run 已渲染过的板（run-r1：launchxl）；
- 按 profile_id 升序排序取前 N（N=4）；
- 不使用 holdout 板（run-r2 为扩样准备，holdout 纪律保持）。

生成器模式：纯函数、零 IO、零子进程、零网络、无 wall-clock。
"""

from __future__ import annotations

#: run-r2 选板规则文档化（入 render-manifest.selection_rule）
SELECTION_RULE_R2 = (
    "pcbench-r1 train-split profile 论域（split 归属以 profiles/<id>/"
    "manifest.json dataset_splits.train 为准）按 profile_id 升序，排除"
    "本轨道 critic run 已渲染板（run-r1=pcbench-launchxl-f28027-"
    "isolation-pcb-project1），取前 4 块；禁止手挑；holdout 板不入选。"
    "四板均取 datasets raw 参考 routed 态（profile manifest "
    "reference_route 指向文件），staging 逐字节断言后 kicad-cli "
    "10.0.5 pcb render 出顶/底 PNG。")

#: 本轨道 critic run 已渲染板（排除集；run-r1 两板）
ALREADY_RENDERED_PROFILE_IDS = (
    "pcbench-launchxl-f28027-isolation-pcb-project1",   # run-r1（train）
    "pcbbm-bm11",                                        # run-r1（holdout）
)

#: run-r2 观察维度提示（只入 render-manifest 与派发文本，类别枚举不变；
#: reader 任务卡的 allowed_categories=critic.FLAG_CATEGORIES 零改动）
OBSERVATION_DIMENSION_HINTS_R2 = (
    "本 run 任务卡在丝印可读性之外增加观察维度提示（均为可见现象，"
    "advisory 类别枚举不变）：(1) 放置重叠可见现象——元件轮廓/丝印"
    "相互叠压、器件压焊盘；(2) 平面覆盖可见现象——敷铜覆盖范围分界、"
    "铜面与丝印/焊盘关系；(3) clearance 可见现象——焊盘/走线间距的"
    "明显贴邻（以可见现象为准，不构成任何 DRC/电气结论）。")


def select_train_boards(records, *, count: int, exclude=()) -> list:
    """确定性选板（纯函数；非法输入 ValueError，fail-closed）。

    records 每项：{profile_id, split, split_basis, source_rel}；
    只收 split=="train" 且 profile_id 不在 exclude（及
    ALREADY_RENDERED_PROFILE_IDS）的记录，按 profile_id 升序取前 count。
    """
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError(f"select_train_boards: count 非法 {count!r}")
    excl = set(exclude) | set(ALREADY_RENDERED_PROFILE_IDS)
    eligible = []
    seen = set()
    for r in records:
        if not isinstance(r, dict):
            raise ValueError("select_train_boards: record 必须为 dict")
        unknown = sorted(set(r) - {"profile_id", "split", "split_basis",
                                   "source_rel"})
        missing = [k for k in ("profile_id", "split", "split_basis",
                               "source_rel") if k not in r]
        if unknown or missing:
            raise ValueError(f"select_train_boards: record 键非法 "
                             f"unknown={unknown} missing={missing}")
        pid = r["profile_id"]
        if pid in seen:
            raise ValueError(f"select_train_boards: profile_id 重复 {pid}")
        seen.add(pid)
        if r["split"] != "train":
            continue
        if pid in excl:
            continue
        eligible.append({"profile_id": pid, "split": r["split"],
                         "split_basis": r["split_basis"],
                         "source_rel": r["source_rel"]})
    eligible.sort(key=lambda r: r["profile_id"])
    selected = eligible[:count]
    if len(selected) < count:
        raise ValueError(f"select_train_boards: 合格 train 板不足 "
                         f"（需 {count}，得 {len(selected)}；fail-closed）")
    return selected
