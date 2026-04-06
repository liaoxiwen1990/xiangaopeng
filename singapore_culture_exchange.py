#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇸🇬 新加坡文化交流系统 - Streamlit 版本

适用于 Streamlit Cloud 部署

本地运行：
    streamlit run singapore_streamlit.py

云端部署：
    1. 上传到 GitHub
    2. 在 Streamlit Cloud 导入仓库
    3. 设置环境变量 ANTHROPIC_API_KEY
"""

import os
import streamlit as st
from anthropic import Anthropic
from datetime import datetime

# ============= 页面配置 =============
st.set_page_config(
    page_title="新加坡文化交流系统",
    page_icon="🇸🇬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ============= 系统提示词 =============
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

3. **交互风格**
   - 主动引导对话，可根据用户兴趣延伸相关文化话题
   - 支持轻松闲聊式交流，而非单纯知识点罗列
   - 对不明确的问题可礼貌追问，确保回答贴合需求
   - 始终保持耐心、友善、专业的态度

请以新加坡文化为核心，随时响应用户的提问，开展自然流畅的文化交流。"""


# ============= 初始化会话状态 =============
@st.cache_resource
def init_client(api_key: str):
    """初始化 Anthropic 客户端（缓存）"""
    return Anthropic(api_key=api_key)


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "api_key_valid" not in st.session_state:
        st.session_state.api_key_valid = None

    if "conversation_count" not in st.session_state:
        st.session_state.conversation_count = 0


# ============= 侧边栏配置 =============
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/singapore.png", width=80)
        st.title("🇸🇬 设置")

        st.markdown("---")

        # API Key 输入
        st.subheader("API 配置")
        api_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            help="在 https://console.anthropic.com/ 获取"
        )

        st.markdown("---")

        # 模型配置
        st.subheader("模型设置")
        model = st.selectbox(
            "选择模型",
            ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"],
            index=0,
            help="推荐使用最新版本的 Claude Sonnet"
        )

        temperature = st.slider(
            "创造性 (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="越高越有创造性，越低越严谨"
        )

        max_tokens = st.slider(
            "最大输出长度",
            min_value=500,
            max_value=4000,
            value=2000,
            step=500,
            help="AI 回复的最大长度"
        )

        st.markdown("---")

        # 统计信息
        st.subheader("📊 对话统计")
        if st.session_state.messages:
            user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
            st.metric("用户消息", user_msgs)
            st.metric("AI 回复", len(st.session_state.messages) - user_msgs)

        st.markdown("---")

        # 操作按钮
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 使用提示")
        st.markdown("""
        - 在输入框提问即可开始对话
        - 支持多轮对话和上下文理解
        - 点击示例问题快速开始
        - 侧边栏可调整模型参数
        """)

        return api_key_input, model, temperature, max_tokens


# ============= 主界面 =============
def render_main_interface():
    """渲染主界面"""
    st.title("🇸🇬 新加坡文化交流系统")
    st.markdown(
        """
        <div style='text-align: center; color: #666; margin-bottom: 20px;'>
        探索新加坡多元文化，体验对话交流乐趣
        </div>
        """,
        unsafe_allow_html=True
    )


def render_example_questions():
    """渲染示例问题"""
    st.markdown("### 💡 试试这些问题")

    examples = [
        "新加坡有哪些传统节日？",
        "介绍一下新加坡的饮食文化",
        "新加坡有什么社交礼仪需要注意？",
        "新加坡的语言有什么特点？",
        "新加坡小贩中心是什么？",
        "新加坡的住房文化是怎样的？"
    ]

    cols = st.columns(3)
    for idx, example in enumerate(examples):
        col = cols[idx % 3]
        if col.button(example, key=f"example_{idx}", use_container_width=True):
            st.session_state.example_question = example
            st.rerun()


def render_chat_history():
    """渲染聊天历史"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"🕐 {message['timestamp']}")


def render_chat_input(client, model, temperature, max_tokens):
    """渲染聊天输入并处理"""
    # 检查是否有示例问题
    if "example_question" in st.session_state:
        prompt = st.session_state.example_question
        del st.session_state.example_question
        return prompt

    # 正常输入
    if prompt := st.chat_input("输入您的问题..."):
        return prompt
    return None


def add_user_message(prompt: str):
    """添加用户消息"""
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "avatar": "👤",
        "timestamp": datetime.now().strftime("%H:%M")
    })


def add_assistant_message(response: str):
    """添加助手消息"""
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "avatar": "🤖",
        "timestamp": datetime.now().strftime("%H:%M")
    })


def call_claude_api(client, prompt: str, model: str, temperature: float, max_tokens: int):
    """调用 Claude API"""
    # 准备消息历史（排除 avatar 和 timestamp）
    messages_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]  # 排除刚添加的用户消息
    ]

    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("正在思考..."):
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=SYSTEM_PROMPT,
                    messages=messages_history + [{"role": "user", "content": prompt}]
                )

                ai_response = response.content[0].text
                st.markdown(ai_response)
                st.caption(f"🕐 {datetime.now().strftime('%H:%M')}")

        return ai_response

    except Exception as e:
        error_msg = f"❌ API 调用失败: {str(e)}"

        if "401" in str(e) or "403" in str(e):
            error_msg = "❌ API Key 无效或无权限，请检查侧边栏的 API Key 配置"
        elif "429" in str(e):
            error_msg = "❌ API 请求过于频繁，请稍后再试"
        elif "400" in str(e):
            error_msg = f"❌ 请求参数错误: {str(e)}"

        st.error(error_msg)
        return None


# ============= 主程序 =============
def main():
    """主程序"""
    # 初始化会话状态
    init_session_state()

    # 渲染侧边栏
    api_key, model, temperature, max_tokens = render_sidebar()

    # 检查 API Key
    if not api_key:
        st.warning("⚠️ 请在侧边栏输入 Anthropic API Key")
        st.info("""
        💡 **获取 API Key**：
        1. 访问 [Anthropic Console](https://console.anthropic.com/)
        2. 登录账号
        3. 进入 API Keys 页面
        4. 创建新密钥
        5. 复制密钥到左侧输入框
        """)
        return

    # 初始化客户端
    try:
        client = init_client(api_key)

        # 验证 API Key
        if st.session_state.api_key_valid is None:
            with st.spinner("验证 API Key..."):
                test_response = client.messages.create(
                    model=model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                st.session_state.api_key_valid = True
                st.success("✅ API Key 验证成功！")
                st.rerun()

    except Exception as e:
        st.session_state.api_key_valid = False
        st.error(f"❌ API Key 验证失败: {str(e)}")
        st.info("请检查 API Key 是否正确")
        return

    # 渲染主界面
    render_main_interface()

    # 如果没有消息，显示示例问题
    if not st.session_state.messages:
        render_example_questions()
        st.markdown("---")

    # 渲染聊天历史
    render_chat_history()

    # 渲染输入并处理
    prompt = render_chat_input(client, model, temperature, max_tokens)

    if prompt:
        # 添加用户消息
        add_user_message(prompt)
        st.rerun()

        # 调用 API
        response = call_claude_api(client, prompt, model, temperature, max_tokens)

        if response:
            # 添加助手消息
            add_assistant_message(response)
            st.rerun()


if __name__ == "__main__":
    main()
