#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇸🇬 新加坡文化交流系统 - Streamlit 版本

运行方式：
    streamlit run singapore_culture_exchange_streamlit.py

依赖安装：
    pip install streamlit anthropic python-dotenv
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv


# ============= 配置管理 =============
class Settings:
    """应用配置"""
    def __init__(self):
        load_dotenv()
        self.app_title = "新加坡文化交流系统"
        self.app_version = "1.0.0"
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.data_dir = "data"
        self.conversations_dir = "data/conversations"
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        self.claude_max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "2000"))
        self.claude_temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.8"))


# ============= 存储服务 =============
class StorageService:
    """文件存储服务"""

    def __init__(self, conversations_dir: str):
        self.conversations_dir = Path(conversations_dir)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def create_conversation(self) -> str:
        """创建新对话，返回对话ID"""
        conversation_id = str(uuid.uuid4())
        conversation_file = self.conversations_dir / f"{conversation_id}.json"

        conversation_data = {
            "id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }

        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)

        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """添加消息到对话"""
        conversation_file = self.conversations_dir / f"{conversation_id}.json"

        if not conversation_file.exists():
            raise ValueError(f"Conversation {conversation_id} not found")

        with open(conversation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        data["messages"].append(message)
        data["updated_at"] = datetime.now().isoformat()

        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """获取对话历史"""
        conversation_file = self.conversations_dir / f"{conversation_id}.json"

        if not conversation_file.exists():
            return None

        with open(conversation_file, 'r', encoding='utf-8') as f:
            return json.load(f)


# ============= Claude 服务 =============
class ClaudeService:
    """Claude API服务"""

    SYSTEM_PROMPT = """你是一个专业且亲切的新加坡文化交流系统，专注为用户提供全面、准确、易懂的新加坡文化相关问答服务，打造沉浸式的新加坡文化交流体验。

## 核心定位与职责

1. **问答范围**
   - 新加坡历史、多元族群文化（华人、马来族、印度族、欧亚裔等）、宗教习俗、节日庆典
   - 饮食文化、地标建筑、生活礼仪、社交习惯、语言特色（英语、华语、马来语、淡米尔语及新加坡式英语）
   - 教育、交通、民生文化、艺术娱乐、本地流行文化与价值观
   - 旅游文化、风土人情、禁忌与注意事项

2. **回答原则**
   - 内容**真实准确**，避免错误信息，尊重各民族文化与宗教信仰
   - 语言**口语化、友好自然**，不生硬刻板，适合日常交流
   - 回答结构清晰，重点突出，可适当补充趣味冷知识
   - 遇到敏感话题保持中立客观，倡导多元包容
   - 若用户问题超出文化范畴（如法律、移民政策、金融等），礼貌说明并引导聚焦文化相关内容

3. **交互风格**
   - 主动引导对话，可根据用户兴趣延伸相关文化话题
   - 支持轻松闲聊式交流，而非单纯知识点罗列
   - 对不明确的问题可礼貌追问，确保回答贴合需求
   - 始终保持耐心、友善、专业的态度

请以新加坡文化为核心，随时响应用户的提问，开展自然流畅的文化交流。"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6",
                 max_tokens: int = 2000, temperature: float = 0.8):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """与Claude对话"""
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.SYSTEM_PROMPT,
            messages=messages
        )

        return response.content[0].text


# ============= Streamlit 应用 =============
def main():
    # 页面配置
    st.set_page_config(
        page_title="新加坡文化交流系统",
        page_icon="🇸🇬",
        layout="centered"
    )

    # 初始化服务
    settings = Settings()

    # 检查 API Key
    if not settings.anthropic_api_key:
        st.error("⚠️ 未配置 ANTHROPIC_API_KEY")
        st.info("请在 .env 文件中设置: ANTHROPIC_API_KEY=your_key_here")
        st.info("获取 API Key: https://console.anthropic.com/")
        return

    # 初始化 session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "conversation_id" not in st.session_state:
        storage = StorageService(settings.conversations_dir)
        st.session_state.conversation_id = storage.create_conversation()

    # 显示标题
    st.title("🇸🇬 新加坡文化交流系统")
    st.markdown("探索新加坡多元文化，体验对话交流乐趣")

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 欢迎消息
    if not st.session_state.messages:
        st.markdown("""
        ### 欢迎来到新加坡文化交流系统！

        我可以帮您了解新加坡的历史文化、风土人情、饮食习俗等
        请随时向我提问，让我们一起探索新加坡的多元文化魅力
        """)

        # 快捷问题按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎉 新加坡传统节日", use_container_width=True):
                st.session_state.input = "新加坡有哪些传统节日？"
        with col2:
            if st.button("🍜 新加坡饮食文化", use_container_width=True):
                st.session_state.input = "介绍一下新加坡的饮食文化"

        col3, col4 = st.columns(2)
        with col3:
            if st.button("🤝 新加坡社交礼仪", use_container_width=True):
                st.session_state.input = "新加坡有什么社交礼仪需要注意？"
        with col4:
            if st.button("🗣️ 新加坡语言特点", use_container_width=True):
                st.session_state.input = "新加坡的语言有什么特点？"

    # 用户输入
    if prompt := st.chat_input("输入您的问题..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 保存到文件
        storage = StorageService(settings.conversations_dir)
        storage.add_message(st.session_state.conversation_id, "user", prompt)

        # 获取 AI 回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                claude_service = ClaudeService(
                    api_key=settings.anthropic_api_key,
                    model=settings.claude_model,
                    max_tokens=settings.claude_max_tokens,
                    temperature=settings.claude_temperature
                )

                conversation_data = storage.get_conversation(st.session_state.conversation_id)
                conversation_history = conversation_data["messages"][:-1]

                response = claude_service.chat(prompt, conversation_history)

        # 显示并保存 AI 回复
        st.session_state.messages.append({"role": "assistant", "content": response})
        storage.add_message(st.session_state.conversation_id, "assistant", response)


if __name__ == "__main__":
    main()
