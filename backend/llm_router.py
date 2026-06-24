"""Routes chat requests to different LLM providers."""

import anthropic
import openai
import google.generativeai as genai


PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter (Multi-Model)",
        "models": [
            {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4"},
            {"id": "anthropic/claude-opus-4", "name": "Claude Opus 4"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "openai/o3-mini", "name": "o3 Mini"},
            {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
            {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
            {"id": "meta-llama/llama-4-maverick", "name": "Llama 4 Maverick"},
            {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1"},
        ],
        "key_url": "https://openrouter.ai/keys",
    },
    "anthropic": {
        "name": "Anthropic",
        "models": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
        ],
        "key_url": "https://console.anthropic.com/settings/keys",
    },
    "openai": {
        "name": "OpenAI",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "o3-mini", "name": "o3 Mini"},
        ],
        "key_url": "https://platform.openai.com/api-keys",
    },
    "google": {
        "name": "Google",
        "models": [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
        ],
        "key_url": "https://aistudio.google.com/apikey",
    },
}


async def send_message(
    provider: str,
    api_key: str,
    model: str,
    messages: list[dict],
    system_prompt: str,
) -> str:
    if provider == "openrouter":
        return await _send_openrouter(api_key, model, messages, system_prompt)
    elif provider == "anthropic":
        return await _send_anthropic(api_key, model, messages, system_prompt)
    elif provider == "openai":
        return await _send_openai(api_key, model, messages, system_prompt)
    elif provider == "google":
        return await _send_google(api_key, model, messages, system_prompt)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def _send_openrouter(api_key: str, model: str, messages: list[dict], system_prompt: str) -> str:
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    oai_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        oai_messages.append({"role": msg["role"], "content": msg["content"]})
    response = client.chat.completions.create(
        model=model,
        messages=oai_messages,
        max_tokens=4096,
    )
    return response.choices[0].message.content


async def _send_anthropic(api_key: str, model: str, messages: list[dict], system_prompt: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


async def _send_openai(api_key: str, model: str, messages: list[dict], system_prompt: str) -> str:
    client = openai.OpenAI(api_key=api_key)
    oai_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        oai_messages.append({"role": msg["role"], "content": msg["content"]})
    response = client.chat.completions.create(
        model=model,
        messages=oai_messages,
        max_tokens=4096,
    )
    return response.choices[0].message.content


async def _send_google(api_key: str, model: str, messages: list[dict], system_prompt: str) -> str:
    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt,
    )
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    chat = gen_model.start_chat(history=history)
    last_msg = messages[-1]["content"] if messages else ""
    response = chat.send_message(last_msg)
    return response.text


def list_providers() -> dict:
    return PROVIDERS
