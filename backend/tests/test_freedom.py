"""自由度档位测试：字数指令注入、档位钳制、max_tokens 随档位传递。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

import main
from api import routes
from game import save_manager as sm
from game import session_manager
from game.prompt_builder import build_narrative_messages, build_opening_messages, _history_messages
from game.state_schema import default_state


def make_state():
    return default_state({"character": {"name": "自由度", "innate_soul_power": 5, "origin": "平民"}})


def test_freedom_tier_clamps():
    assert routes._freedom_tier(1)["chars"] == 200
    assert routes._freedom_tier(3)["chars"] == 1000
    assert routes._freedom_tier(5)["chars"] == 2000
    assert routes._freedom_tier(5)["max_tokens"] == 3200
    # 非法输入回落默认档（标准 1000 字）
    assert routes._freedom_tier(99)["chars"] == 1000
    assert routes._freedom_tier("abc")["chars"] == 1000
    assert routes._freedom_tier(None)["chars"] == 1000


def test_narrative_length_hint_present_and_optional():
    s = make_state()
    msgs = build_narrative_messages(s, [], "行动", 500)
    assert "500 字" in msgs[-1]["content"]
    assert "字数要求" in msgs[-1]["content"]
    # ±15% 区间明确给出（500 → 425～575），让模型严格守区间
    assert "425～575" in msgs[-1]["content"]
    # 不传 chars 时不注入指令（旧调用兼容）
    msgs2 = build_narrative_messages(s, [], "行动")
    assert "字数要求" not in msgs2[-1]["content"]


def test_opening_length_hint():
    s = make_state()
    msgs = build_opening_messages(s, {}, 2000)
    assert "2000 字" in msgs[-1]["content"]


def test_history_token_budget_truncates():
    """高档位长叙述下，历史按估算 token 预算裁剪，防止撑爆 DeepSeek 64K 上下文。"""
    history = []
    for i in range(10):
        history.append(json.dumps({"role": "user", "content": "短" * 1000}))       # ~1300 tokens
        history.append(json.dumps({"role": "assistant", "content": "长" * 1000}))  # ~1300 tokens
    msgs = _history_messages(history, token_budget=3000)
    # 预算内只保留最新 2 条（user+assistant），且保持旧→新顺序
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    # 默认预算（20000）比紧预算（3000）保留更多，但同样按 token 裁剪、不超 60 条
    default = _history_messages(history)
    assert len(default) > len(msgs)
    assert len(default) <= 60


def test_freedom_max_tokens_passed_through(monkeypatch, tmp_path):
    monkeypatch.setattr(sm, "SAVES_DIR", tmp_path)
    monkeypatch.setattr(sm, "ACTIVATIONS_PATH", tmp_path / "activations.json")
    session_manager._SESSIONS.clear()
    seen = {}

    def record_call_turn(messages, api_key=None, max_tokens=2800):
        seen["max_tokens"] = max_tokens
        return {
            "narrative": "一段叙述。",
            "options": [],
            "state_delta": {},
            "notes": [],
            "event": "",
        }

    monkeypatch.setattr(routes, "_call_turn", record_call_turn)
    c = TestClient(main.app)

    # new-game freedom=5 → min(3200 + 6000, 8192) = 8192，顶到模型上限但不越界
    r = c.post("/api/new-game", json={
        "archive": {"character": {"name": "X", "innate_soul_power": 5, "origin": "平民"}},
        "session_id": "f1", "freedom": 5,
    })
    assert r.status_code == 200
    assert seen.get("max_tokens") == routes.MODEL_MAX_TOKENS

    # act freedom=2 → 800 + 6000 = 6800，未触顶
    r2 = c.post("/api/act", json={"session_id": "f1", "action": "行动", "freedom": 2})
    assert r2.status_code == 200
    assert seen.get("max_tokens") == 6800

    # act 缺省 freedom → 1600 + 6000 = 7600，未触顶
    r3 = c.post("/api/act", json={"session_id": "f1", "action": "再行动"})
    assert r3.status_code == 200
    assert seen.get("max_tokens") == 7600


def test_freedom_over_cap_tiers_are_clamped():
    """回归护栏：档位 4/5 的原始预算越界，routes 必须钳到模型上限。

    带 6000 预留量时档位 4/5 为 8400/9200 > deepseek-chat 的 8192，会直接 HTTP 400；
    异常被 _call_turn 吞掉后玩家只看到模板叙述 + 单个「继续前行」选项。
    这条测试会在有人删掉 routes 里的 min(...) 钳制、或上调档位/预留量时失败。
    """
    over_cap = [v for v, t in routes.FREEDOM_TIERS.items()
                if t["max_tokens"] + 6000 > routes.MODEL_MAX_TOKENS]
    assert over_cap == [4, 5], (
        f"预期恰好档位 4/5 越界，实际 {over_cap}；"
        "若档位表或模型上限变了，请同步复核 routes.py 里 unified_max_tokens 的 min(...) 钳制"
    )
