from scripts.run_unified_mixed_route_policy import build_prompt, normalize_route, parse_json_response, proxy_prompt_payload


def test_unified_proxy_prompt_does_not_expose_kind_label():
    payload, top_memories = proxy_prompt_payload("proxy_easy_edit_none_timeout", display_id="task_001")
    prompt = build_prompt(payload)

    assert "proxy_easy" not in prompt
    assert "swe_hard" not in prompt
    assert "route L" in prompt
    assert "route P" in prompt
    assert payload["task_id"] == "task_001"
    assert top_memories[0]["id"] == "mem_1"


def test_parse_and_normalize_route_json_response():
    parsed, error = parse_json_response(
        """```json
        {"route": "DELEGATE_PACKET", "selected_memory_ids": ["mem_1"]}
        ```"""
    )

    assert error == ""
    assert normalize_route(parsed) == "P"
    assert normalize_route({"route": "SELF_HANDLE"}) == "L"
