from cli import HermesCLI


def _stub_cli():
    cli = HermesCLI.__new__(HermesCLI)
    cli.model = "openrouter/selected-model"
    cli.api_key = "upstream-key"
    cli.base_url = "https://openrouter.ai/api/v1"
    cli.provider = "openrouter"
    cli.api_mode = "chat_completions"
    cli.acp_command = None
    cli.acp_args = []
    cli._credential_pool = None
    cli.service_tier = None
    cli.config = {
        "skillclaw": {
            "enabled": True,
            "proxy_base_url": "http://127.0.0.1:30000/v1",
            "proxy_api_key": "skillclaw",
            "proxy_model": "skillclaw-model",
        }
    }
    return cli


def test_skillclaw_proxy_preserves_selected_upstream_route():
    cli = _stub_cli()

    route = HermesCLI._resolve_turn_agent_config(cli, "hi")

    assert route["model"] == "openrouter/selected-model"
    assert route["runtime"]["base_url"] == "http://127.0.0.1:30000/v1"
    assert route["runtime"]["api_key"] == "skillclaw"
    assert route["runtime"]["provider"] == "openrouter"
    assert route["runtime"]["api_mode"] == "chat_completions"
    assert route["request_overrides"] == {
        "extra_headers": {
            "X-SkillClaw-Upstream-Base-Url": "https://openrouter.ai/api/v1",
            "X-SkillClaw-Upstream-Model": "openrouter/selected-model",
            "X-SkillClaw-Upstream-Provider": "openrouter",
            "X-SkillClaw-Upstream-Api-Mode": "chat_completions",
            "X-SkillClaw-Upstream-Api-Key": "upstream-key",
        }
    }


def test_skillclaw_proxy_noops_when_disabled():
    cli = _stub_cli()
    cli.config["skillclaw"]["enabled"] = False

    route = HermesCLI._resolve_turn_agent_config(cli, "hi")

    assert route["runtime"]["base_url"] == "https://openrouter.ai/api/v1"
    assert route["runtime"]["api_key"] == "upstream-key"
    assert route["request_overrides"] is None


def test_skillclaw_sidecar_does_not_proxy_selected_route():
    cli = _stub_cli()
    cli.config["skillclaw"] = {
        "enabled": True,
        "mode": "sidecar",
        "endpoint": "http://127.0.0.1:30000",
        "api_key": "skillclaw",
    }

    route = HermesCLI._resolve_turn_agent_config(cli, "hi")

    assert route["model"] == "openrouter/selected-model"
    assert route["runtime"]["base_url"] == "https://openrouter.ai/api/v1"
    assert route["runtime"]["api_key"] == "upstream-key"
    assert route["request_overrides"] is None


def test_skillclaw_proxy_noops_for_unsupported_api_mode():
    cli = _stub_cli()
    cli.api_mode = "anthropic_messages"

    route = HermesCLI._resolve_turn_agent_config(cli, "hi")

    assert route["runtime"]["base_url"] == "https://openrouter.ai/api/v1"
    assert route["runtime"]["api_key"] == "upstream-key"
    assert route["request_overrides"] is None
