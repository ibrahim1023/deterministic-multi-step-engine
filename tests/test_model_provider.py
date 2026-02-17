from src.model_provider import LiteLLMProvider


def test_litellm_provider_parses_first_choice() -> None:
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"summary":"ok"}',
                    }
                }
            ]
        }

    provider = LiteLLMProvider(completion_fn=fake_completion)
    response = provider.complete(
        model="gpt-test",
        messages=[{"role": "user", "content": "test"}],
    )

    assert captured["model"] == "gpt-test"
    assert captured["temperature"] == 0.0
    assert captured["n"] == 1
    assert response.content == '{"summary":"ok"}'
