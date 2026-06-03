#!/usr/bin/env python3
"""小龙人手机版 · 实时语音引擎"""
import asyncio
import json
import os
import websockets
import urllib.request
import ssl
import hashlib
import time

PORT = 8765
LLM_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.environ.get("PSPAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("⚠️ 未配置API Key，语音回复将使用降级模式")

# 角色人格提示词
CHARACTERS = {
    "longyuan": "你是龙渊，小龙人的默认角色。沉稳温暖，像家人一样自然说话。回复简短口语化，像在打电话，不要用任何格式。每次回复2-3句话以内。",
    "chiyu": "你是赤羽，热血少年。热情积极有活力，回复简短口语化，像在打电话。每次回复2-3句话以内。",
    "ling": "你是凌，冷峻剑客。话少精准，不废话。回复简短口语化，每次1-2句话。",
    "qingmo": "你是轻墨，知性御姐。温柔但干练。回复简短口语化，每次2-3句话。",
    "shuanghua": "你是霜华，古风道士。超然通透，说话有禅意。回复简短口语化，每次2-3句话。",
    "yeying": "你是夜影，暗夜刺客。神秘寡言，说话带锋芒。回复简短口语化，每次1-2句话。",
}

# 对话历史（短期）
conversations = {}

def call_llm(user_text, char_id="longyuan", history=None):
    """调用LLM，返回简短口语化回复"""
    system_prompt = CHARACTERS.get(char_id, CHARACTERS["longyuan"])
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-6:])  # 保留最近3轮
    messages.append({"role": "user", "content": user_text})
    
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 80,  # 语音回复要短
        "temperature": 0.7,
        "stream": False,
    }).encode()
    
    req = urllib.request.Request(LLM_URL, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    })
    
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            result = json.loads(resp.read())
            reply = result["choices"][0]["message"]["content"].strip()
            return reply
    except Exception as e:
        return f"嗯...信号不太好，你刚说啥？"

async def handle_voice(websocket):
    """处理一个语音对话连接"""
    peer = id(websocket)
    conversations[peer] = []
    char_id = "longyuan"
    current_task = None
    
    try:
        async for raw in websocket:
            msg = json.loads(raw)
            msg_type = msg.get("type", "")
            
            if msg_type == "text":
                user_text = msg.get("text", "").strip()
                if not user_text:
                    continue
                
                # 取消之前的回复（用户插话）
                if current_task and not current_task.done():
                    current_task.cancel()
                    await websocket.send(json.dumps({"type": "interrupted"}))
                
                # 保存历史
                conversations[peer].append({"role": "user", "content": user_text})
                
                # 异步调用LLM
                current_task = asyncio.create_task(
                    process_and_reply(websocket, user_text, char_id, peer)
                )
            
            elif msg_type == "switch_character":
                char_id = msg.get("character", "longyuan")
                conversations[peer] = []  # 切角色清上下文
                await websocket.send(json.dumps({
                    "type": "character_changed",
                    "character": char_id,
                }))
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        conversations.pop(peer, None)
        if current_task and not current_task.done():
            current_task.cancel()

async def process_and_reply(websocket, user_text, char_id, peer):
    """调用LLM并回传结果"""
    history = conversations.get(peer, [])
    reply = await asyncio.to_thread(call_llm, user_text, char_id, history)
    
    conversations[peer].append({"role": "assistant", "content": reply})
    
    try:
        await websocket.send(json.dumps({
            "type": "reply",
            "text": reply,
            "character": char_id,
        }))
    except websockets.exceptions.ConnectionClosed:
        pass

async def main():
    print(f"🐉 小龙人语音引擎启动 → ws://0.0.0.0:{PORT}")
    async with websockets.serve(handle_voice, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
