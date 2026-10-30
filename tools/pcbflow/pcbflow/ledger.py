"""TD1 追加式裁决账本（decision-ledger.jsonl；SPEC-v3.0-PROPOSAL TD1/§1.2）。

合同要点（本模块机器侧落地）：
- 追加式 hash 链：每条 entry 含 entry_seq（0 起）、prev_entry_sha256
  （首条 Genesis 恒 null）、entry_sha256（记录体 canonical hash，不含自身
  与 ledger_head_sha256）、ledger_head_sha256
  = sha256_text(prev_head + ":" + entry_sha256)（prev_head=None → "GENESIS"）；
- 事实修正只能新增 supersedes/revokes 事件，禁止回写/删除/重排——
  verify_supersedes 只做结构校验（引用存在、追加式、不被重复 supersede）；
- trust_level 由 validator 控制不可手写升级：verify_chain 强制
  authority→trust_level 白名单（TRUST_POLICY）；Human 的「事实信任」恒不可升
  ——human authority 只允许出现在 disposition 类 entry 且恒 untrusted
  （处置是决定，不是事实）；
- checkpoint：可信 root（entry_seq/head/条数/累计 hash），用于受控提交
  证明与截断检测；普通 hash 链不单独作为防篡改授权证明（§6 风险表）；
- fail-closed：append 前先 verify_chain，链不合法即抛异常。

生成器模式：纯函数、零子进程、零写盘、零网络、无 wall-clock、标准库 only。
账本只提供离线只读 projection 输入，不驱动运行时自适应（L1）。
"""

from __future__ import annotations

from . import hashing, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 创世哨兵：空账本续写首条 head 时的 prev_head 占位（不出现在任何 entry 里）
GENESIS = "GENESIS"

#: authority → 允许的 trust_level 白名单（TD1：validator 强制，不可手写升级）
TRUST_POLICY = {
    # 外部/模型输出恒 untrusted（引擎自报分数/旗标不具 authority）
    "critic_model": frozenset({"untrusted"}),
    "external_backend": frozenset({"untrusted"}),
    # 机器观察：observed 起步，独立重放/交叉验证后才可 verified
    "kicad_cli": frozenset({"observed", "verified"}),
    "deterministic_evaluator": frozenset({"observed", "verified"}),
    "solver": frozenset({"observed", "verified"}),
    "replay": frozenset({"observed", "verified"}),
    "test_manifest": frozenset({"observed", "verified"}),
    "ledger_validator": frozenset({"observed", "verified"}),
    # Human 只写处置：处置本身不是事实，恒不可升级为 observed/verified
    "human": frozenset({"untrusted"}),
}

#: human authority 允许的 entry_kind（adoption 决定按 §1.4 以
#: scope="adoption" 的 disposition 记录，不另设 human adoption entry）
HUMAN_AUTHORITY_ENTRY_KINDS = ("disposition",)

#: 三级信任语义说明（随 ledger 产物一并归档的常量文本）
trust_policy_note = (
    "trust_level 三级语义（TD1：validator 控制的证据成熟度，不是可手写的权威升级标签）：\n"
    "- untrusted：外部引擎/模型产出的原始记录（critic_model、external_backend）——"
    "只能以未信任身份入账，自报分数不具 authority；\n"
    "- observed：kicad_cli/确定性 evaluator/solver/replay/test_manifest 的机器观察——"
    "可复核，但未经独立重放；\n"
    "- verified：经独立重放或交叉验证后的机器观察（仅机器 authority 可达）。\n"
    "Human 的「事实信任」恒不可升：human authority 只允许出现在 disposition 类 entry "
    "且恒 untrusted——处置是决定，不是事实；judge_fact 不可变，修正只能追加 supersedes。"
)

#: make_entry 保留键（由链构造逻辑独占，调用方 fields 不得覆盖）
_RESERVED_ENTRY_KEYS = ("schema_version", "entry_seq", "prev_entry_sha256",
                        "entry_sha256", "ledger_head_sha256")


# ---------------------------------------------------------------------------
# 构造辅助
# ---------------------------------------------------------------------------

def make_schema_validation(schema_name: str, *, valid: bool = True,
                           errors=()) -> dict:
    """构造 entry.schema_validation 块（绑定验证时所用 schema 版本哈希）。

    未知 schema 名 fail-closed 抛 ValueError（schema_hash 无法绑定的
    validation 记录不可入账）。
    """
    if schema_name not in schemas.SCHEMAS:
        raise ValueError(
            f"未知 schema 名 {schema_name!r}（注册表 v{schemas.REGISTRY_VERSION}）"
            f"——schema_validation 必须绑定注册表内 schema")
    block = {"schema_name": schema_name,
             "schema_sha256": schemas.schema_hash(schema_name),
             "valid": valid}
    if errors:
        block["errors"] = list(errors)
    return block


def entry_body_sha256(entry: dict) -> str:
    """entry 记录体 canonical hash：剔除 entry_sha256 与 ledger_head_sha256。"""
    body = {k: v for k, v in entry.items()
            if k not in ("entry_sha256", "ledger_head_sha256")}
    return hashing.sha256_bytes(hashing.canonical_json_bytes(body))


def _prev_state(entries_or_head):
    """返回 (entry_seq, prev_entry_sha256, prev_ledger_head)。"""
    if entries_or_head is None:
        return 0, None, None
    if isinstance(entries_or_head, (list, tuple)):
        if not entries_or_head:
            return 0, None, None
        last = entries_or_head[-1]
        if not isinstance(last, dict):
            raise TypeError("账本末条 entry 必须为 dict")
        return (len(entries_or_head), last.get("entry_sha256"),
                last.get("ledger_head_sha256"))
    raise TypeError(
        f"entries_or_head 需为 entry 列表或 None（空账本），"
        f"得到 {type(entries_or_head).__name__}")


def make_entry(entries_or_head, *, entry_kind, schema_validation, authority,
               trust_level, **fields) -> dict:
    """构造完整合法 ledger entry（schema 违例即抛 ValueError）。

    entry_seq=len(账本)、prev_entry_sha256=上一条 entry_sha256（空账本→None）、
    entry_sha256=记录体 canonical hash、ledger_head_sha256
    =sha256_text(prev_head + ":" + entry_sha256)（prev_head=None → GENESIS）。
    注意：本函数只保证 schema 合法；authority→trust_level 白名单与链一致性
    由 verify_chain 强制（validator 职责，构造不代替验证）。
    """
    seq, prev_sha, prev_head = _prev_state(entries_or_head)
    for k in _RESERVED_ENTRY_KEYS:
        if k in fields:
            raise ValueError(f"fields 不得覆盖链构造保留键 {k!r}")
    entry = {
        "schema_version": SCHEMA_VERSION,
        "entry_seq": seq,
        "prev_entry_sha256": prev_sha,
        "entry_kind": entry_kind,
        "authority": authority,
        "trust_level": trust_level,
        "schema_validation": schema_validation,
    }
    entry.update(fields)
    entry["entry_sha256"] = entry_body_sha256(entry)
    entry["ledger_head_sha256"] = hashing.sha256_text(
        (GENESIS if prev_head is None else prev_head) + ":" +
        entry["entry_sha256"])
    errs = schemas.validate("decision_ledger_entry", entry)
    if errs:
        raise ValueError(f"ledger entry 非法（fail-closed 拒绝入账）: {errs}")
    return entry


# ---------------------------------------------------------------------------
# 链验证（validator 侧；fail-closed）
# ---------------------------------------------------------------------------

def verify_chain(entries) -> list:
    """逐条校验账本链，返回错误列表（[] = 合法）。

    检查项：逐条 decision_ledger_entry schema 严格验证；entry_seq 从 0 起
    连续；prev_entry_sha256 与上一条 entry_sha256 一致（首条 Genesis 恒
    null）；entry_sha256 / ledger_head_sha256 重算一致；authority→trust_level
    白名单强制（TRUST_POLICY）；human authority 仅限 disposition 类 entry。
    """
    errors: list = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry[{i}]: 非 dict（{type(entry).__name__}）")
            continue
        for e in schemas.validate("decision_ledger_entry", entry):
            errors.append(f"entry[{i}]: {e}")
        if entry.get("entry_seq") != i:
            errors.append(f"entry[{i}]: entry_seq 应为 {i}（0 起连续），"
                          f"得到 {entry.get('entry_seq')!r}")
        # entry_sha256 重算
        if entry.get("entry_sha256") != entry_body_sha256(entry):
            errors.append(f"entry[{i}]: entry_sha256 重算不一致"
                          f"（记录体被篡改或哈希未按 canonical 规则计算）")
        # prev / head 链
        if i == 0:
            if entry.get("prev_entry_sha256") is not None:
                errors.append(f"entry[0]: Genesis prev_entry_sha256 必须为 "
                              f"null，得到 {entry.get('prev_entry_sha256')!r}")
            prev_head = None
        else:
            prev = entries[i - 1] if isinstance(entries[i - 1], dict) else {}
            if entry.get("prev_entry_sha256") != prev.get("entry_sha256"):
                errors.append(
                    f"entry[{i}]: prev_entry_sha256 与上一条 entry_sha256 "
                    f"不一致（期望 {str(prev.get('entry_sha256'))[:12]}…，"
                    f"得到 {str(entry.get('prev_entry_sha256'))[:12]}…）")
            prev_head = prev.get("ledger_head_sha256")
        expected_head = hashing.sha256_text(
            (GENESIS if prev_head is None else prev_head) + ":" +
            str(entry.get("entry_sha256")))
        if entry.get("ledger_head_sha256") != expected_head:
            errors.append(f"entry[{i}]: ledger_head_sha256 重算不一致")
        # trust 白名单（TD1：validator 强制）
        authority = entry.get("authority")
        trust = entry.get("trust_level")
        allowed = TRUST_POLICY.get(authority)
        if allowed is None:
            errors.append(f"entry[{i}]: 未知 authority {authority!r}")
        elif trust not in allowed:
            errors.append(
                f"entry[{i}]: authority {authority!r} 不允许 trust_level "
                f"{trust!r}（白名单 {sorted(allowed)}；trust_level 由 "
                f"validator 控制不可手写升级）")
        if authority == "human":
            if entry.get("entry_kind") not in HUMAN_AUTHORITY_ENTRY_KINDS:
                errors.append(
                    f"entry[{i}]: human authority 只允许出现在 "
                    f"{list(HUMAN_AUTHORITY_ENTRY_KINDS)} 类 entry，得到 "
                    f"{entry.get('entry_kind')!r}（处置不是事实）")
    return errors


def append(entries, body: dict) -> tuple:
    """fail-closed 追加：先 verify_chain，链不合法即抛 ValueError。

    body 为 make_entry 的关键字参数集（entry_kind/schema_validation/
    authority/trust_level + 其余字段）。返回 (new_entries, entry)；
    原列表不被修改。
    """
    errs = verify_chain(entries)
    if errs:
        raise ValueError(f"账本链不合法，拒绝追加（fail-closed）: {errs[:3]}")
    entry = make_entry(entries, **body)
    return list(entries) + [entry], entry


def verify_supersedes(entries) -> list:
    """supersedes/revokes 结构校验（validator 只查结构，不评语义）。

    引用的 entry_sha256 必须存在；只能引用更早的 entry（追加式，含禁自引）；
    同一目标至多被 supersede/revoke 一次（两类共享单次失效预算）；单条
    entry 的引用列表内不得重复。
    """
    errors: list = []
    sha_to_seq: dict = {}
    for i, entry in enumerate(entries):
        if isinstance(entry, dict) and entry.get("entry_sha256"):
            sha_to_seq[entry["entry_sha256"]] = i
    invalidated: dict = {}  # 目标 sha → 首次 supersede/revoke 的 entry seq
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        for field in ("supersedes", "revokes"):
            targets = entry.get(field) or []
            seen_local: set = set()
            for target in targets:
                if target in seen_local:
                    errors.append(f"entry[{i}]: {field} 列表内重复引用 "
                                  f"{str(target)[:12]}…")
                    continue
                seen_local.add(target)
                if target not in sha_to_seq:
                    errors.append(f"entry[{i}]: {field} 引用不存在的 "
                                  f"entry_sha256 {str(target)[:12]}…")
                elif sha_to_seq[target] >= i:
                    errors.append(f"entry[{i}]: {field} 违反追加式——"
                                  f"引用了自身或更晚的 entry（seq "
                                  f"{sha_to_seq[target]} >= {i}）")
                elif target in invalidated:
                    errors.append(f"entry[{i}]: {field} 重复 supersede——"
                                  f"{str(target)[:12]}… 已由 entry["
                                  f"{invalidated[target]}] 失效")
                else:
                    invalidated[target] = i
    return errors


# ---------------------------------------------------------------------------
# checkpoint（可信 root / 截断检测）
# ---------------------------------------------------------------------------

def make_checkpoint(entries, checkpoint_id: str) -> dict:
    """构造账本 checkpoint：{checkpoint_id, entry_seq, ledger_head_sha256,
    entry_count, entries_cum_sha256}。

    entries_cum_sha256 = 全部 entry_sha256 依次字符串串联的 sha256。
    空账本：entry_seq/ledger_head_sha256 为 None（下一 Entry 的 prev_head
    按 GENESIS 计算）。
    """
    if not isinstance(checkpoint_id, str) or not checkpoint_id:
        raise ValueError("checkpoint_id 必须为非空字符串")
    cum = "".join(e["entry_sha256"] for e in entries
                  if isinstance(e, dict))
    return {
        "checkpoint_id": checkpoint_id,
        "entry_seq": (entries[-1].get("entry_seq") if entries else None),
        "ledger_head_sha256": (entries[-1].get("ledger_head_sha256")
                               if entries else None),
        "entry_count": len(entries),
        "entries_cum_sha256": hashing.sha256_text(cum),
    }


def verify_against_checkpoint(entries, ckpt: dict) -> list:
    """账本是否与 checkpoint 一致（截断/延长/篡改均报错；fail-closed）。"""
    errors: list = []
    if not isinstance(ckpt, dict):
        return ["checkpoint 必须为 dict"]
    for key in ("checkpoint_id", "entry_seq", "ledger_head_sha256",
                "entry_count", "entries_cum_sha256"):
        if key not in ckpt:
            errors.append(f"checkpoint 缺必需键 {key!r}")
    if errors:
        return errors
    expected = make_checkpoint(entries, ckpt["checkpoint_id"])
    for key in ("entry_seq", "ledger_head_sha256", "entry_count",
                "entries_cum_sha256"):
        if ckpt.get(key) != expected[key]:
            errors.append(
                f"checkpoint 不一致：{key} 声明 {ckpt.get(key)!r}，"
                f"账本实为 {expected[key]!r}（截断/延长/篡改）")
    return errors
