from app import ai


def test_public_assistant_knows_platform_facts(monkeypatch):
    captured = {}

    def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return "رد تجريبي", "test-model"

    monkeypatch.setattr(ai, "chat", fake_chat)

    result = ai.public_assistant(
        [{"role": "user", "content": "ما هو كاييروس؟"}],
        "عنوان من الأخبار",
    )

    assert result == ("رد تجريبي", "test-model")
    system = captured["messages"][0]["content"]
    assert "كاييروس إيه آي هو المحلل الآلي للمنصة" in system
    assert "عنوان من الأخبار" in system
    assert captured["messages"][-1] == {"role": "user", "content": "ما هو كاييروس؟"}
