"""
LLM 调用封装：基于 OpenAI 兼容接口（如 DeepSeek via SiliconFlow）
"""
from typing import List, Dict, Any, Generator

import json
import requests

from config import Config


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 512) -> str:
    """
    通用 LLM 调用封装，返回模型生成的文本内容
    """
    if not Config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY 未配置，请在 .env 中设置")

    headers = {
        "Authorization": f"Bearer {Config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": Config.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "text"},
    }
    resp = requests.post(Config.LLM_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def build_vehicle_context(vehicles: List[Dict[str, Any]]) -> str:
    """
    将检索到的车辆信息列表格式化为 prompt 片段
    """
    lines = []
    for i, v in enumerate(vehicles):
        idx = i + 1
        lines.append(
            f"{idx}. 车牌: {v.get('plate_number','')}, 品牌型号: {v.get('brand_model','')}, "
            f"车主: {v.get('owner_name','')}, 电话: {v.get('owner_phone','')}, "
            f"地址/车位: {v.get('owner_address','')}, 描述: {v.get('description','')}"
        )
    return "\n".join(lines)


def ask_about_vehicles(question: str, vehicles: List[Dict[str, Any]]) -> str:
    """
    基于检索到的车辆信息，让大模型生成自然语言回答
    """
    context = build_vehicle_context(vehicles)
    prompt = (
        "你是一个智能小区车辆管理助手，根据提供的车辆信息回答用户问题。\n"
        "如果问题是统计类问题（例如“白色的车有多少辆”），请给出数量并列出相关车牌。\n"
        "如果问题询问车主或停车位信息，请结合车主地址字段进行说明。\n"
        "如果问题询问某辆车的停车费用，请结合后端提供的费用信息（若有）进行回答。\n\n"
        f"用户问题：{question}\n"
        f"可用车辆数据：\n{context}\n\n"
        "请用简洁的中文回答，尽量给出清晰的列表或统计结果。"
    )

    messages = [
        {"role": "user", "content": prompt},
    ]
    return call_llm(messages)


def stream_ask_about_vehicles(
    question: str, vehicles: List[Dict[str, Any]], temperature: float = 0.2, max_tokens: int = 512
) -> Generator[str, None, None]:
    """
    基于检索到的车辆信息，流式调用大模型，逐段返回回答内容
    （基于 OpenAI 兼容的 stream 接口，使用 SSE data: 行）
    """
    if not Config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY 未配置，请在 .env 中设置")

    context = build_vehicle_context(vehicles)
    prompt = (
        "你是一个智能小区车辆管理助手，根据提供的车辆信息回答用户问题。\n"
        "如果问题是统计类问题（例如“白色的车有多少辆”），请给出数量并列出相关车牌。\n"
        "如果问题询问车主或停车位信息，请结合车主地址字段进行说明。\n"
        "如果问题询问某辆车的停车费用，请结合后端提供的费用信息（若有）进行回答。\n\n"
        f"用户问题：{question}\n"
        f"可用车辆数据：\n{context}\n\n"
        "请用简洁的中文回答，尽量给出清晰的列表或统计结果。"
    )

    messages: List[Dict[str, str]] = [
        {"role": "user", "content": prompt},
    ]

    headers = {
        "Authorization": f"Bearer {Config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": Config.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    with requests.post(
        Config.LLM_API_URL,
        json=payload,
        headers=headers,
        stream=True,
        timeout=300,
    ) as resp:
        resp.raise_for_status()
        # Some SSE endpoints omit charset; requests may fall back to latin-1.
        # Force UTF-8 to avoid mojibake for Chinese tokens.
        resp.encoding = "utf-8"
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            # 兼容 data: 前缀或纯 JSON 行
            if line.startswith("data:"):
                data_str = line[len("data:") :].strip()
            else:
                data_str = line.strip()

            if not data_str or data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except Exception:
                continue

            choices = data.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            chunk = delta.get("content") or ""
            if chunk:
                yield chunk

