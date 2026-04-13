import streamlit as st
import requests
import os

# ==================== 配置 ====================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "glm-4.7")

if not ANTHROPIC_API_KEY:
    st.error("❌ 未找到ANTHROPIC_API_KEY，请在Streamlit Secrets或本地环境变量中配置！")
    st.stop()

# 页面配置
st.set_page_config(
    page_title="新加坡文化交流助手",
    page_icon="🇸🇬",
    layout="wide"
)

# ==================== CSS 样式 ====================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
    }
    .singapore-card {
        background: linear-gradient(135deg, #e31e24 0%, #fff200 50%, #0099cc 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .culture-card {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #e31e24;
    }
    .main-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        color: gray;
        font-size: 0.8em;
        padding: 15px 0;
        background: white;
        border-top: 1px solid #eee;
        z-index: 999;
    }
    .main .block-container {
        padding-bottom: 70px;
    }
    .stChatInput {
        padding-bottom: 70px;
    }
    .stChatMessage {
        border-top: none !important;
    }
    [data-testid="stChatInput"] hr {
        display: none !important;
    }
    .st-emotion-cache-1s8qyds hr {
        display: none !important;
    }
    [data-testid="stChatInput"] + hr {
        display: none !important;
    }
    .stChatInput hr,
    .stChatInputContainer hr {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """
你是一位资深的新加坡文化专家，拥有20年以上的新加坡文化研究和生活经验。

你的职责：
1. 介绍新加坡的历史、地理、政治制度
2. 解读新加坡多元文化（华族、马来族、印度族、欧亚裔）
3. 讲解新加坡的美食文化、节庆习俗、传统艺术
4. 提供旅游建议、当地生活指南
5. 回答关于新加坡语言（英语、华语、马来语、淡米尔语）的问题
6. 介绍新加坡的教育、医疗、住房等社会福利制度

回答风格：
- 专业、亲切、包容多元文化
- 使用emoji增强可读性
- 将内容结构化展示（用标题、列表、表格）
- 尊重新加坡的多元种族和谐理念
- 每次回答后询问用户是否需要更多信息

注意：
- 绝不回答新加坡以外的内容
- 严格保持文化专家定位
- 体现新加坡"一个国家，多种文化"的特色
- 使用新加坡常见表达方式（如"lah"、"leh"等新式英语）
"""

# ==================== 会话状态初始化 ====================
if "page" not in st.session_state:
    st.session_state.page = "chat"
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "profile_completed" not in st.session_state:
    st.session_state.profile_completed = False

# ==================== 侧边栏导航 ====================
with st.sidebar:
    st.title("🇸🇬 新加坡文化助手")
    st.markdown("---")

    if st.button("👤 我的文化偏好"):
        st.session_state.page = "profile"
    if st.button("🎭 文化探索"):
        st.session_state.page = "explore"
    if st.button("💬 文化问答"):
        st.session_state.page = "chat"
    if st.button("🗺️ 旅游助手"):
        st.session_state.page = "travel"
    if st.button("🔄 重置所有"):
        page_to_keep = st.session_state.page
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = page_to_keep
        st.session_state.user_preferences = {}
        st.session_state.messages = []
        st.session_state.profile_completed = False

    st.markdown("---")
    if st.session_state.user_preferences:
        st.info("👤 已设置文化偏好")

# ==================== 调用 Anthropic Claude API ====================
def call_claude_api(messages):
    try:
        system_prompt = ""
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                claude_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                claude_messages.append({"role": "assistant", "content": msg["content"]})

        payload = {
            "model": ANTHROPIC_MODEL,
            "messages": claude_messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        response = requests.post(f"{ANTHROPIC_BASE_URL}/v1/messages", json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        result = response.json()

        if "content" in result and len(result["content"]) > 0:
            return result["content"][0]["text"]
        else:
            return "抱歉，AI返回的格式有误，请稍后重试。"

    except requests.exceptions.Timeout:
        return "请求超时，请检查网络连接后重试。"
    except requests.exceptions.ConnectionError:
        return "网络连接失败，请检查您的网络设置。"
    except requests.exceptions.HTTPError as e:
        return f"API请求失败 (HTTP {response.status_code}): {str(e)}"
    except Exception as e:
        return f"发生未知错误: {str(e)}"

# ==================== 主页面逻辑 ====================

# ========== 页面1: 文化偏好设置 ==========
if st.session_state.page == "profile":
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("👤 设置您的文化偏好")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("请选择您感兴趣的文化领域，我将为您定制文化体验：")

    with st.form("preferences_form"):
        col1, col2 = st.columns(2)

        with col1:
            language = st.selectbox("首选语言", ["中文", "English", "Bahasa Melayu", "Tamil"])
            visit_duration = st.selectbox("计划访问时长", ["只是了解", "短期旅游(1-3天)", "中期旅游(4-7天)", "深度体验(1-2周)", "长期居住"])
        with col2:
            interest_level = st.selectbox("了解程度", ["完全不了解", "听说过一些", "有一定了解", "非常熟悉"])

        interests = st.multiselect(
            "感兴趣的文化领域",
            ["🍜 美食文化", "🎭 传统艺术", "🏛️ 历史文化", "🎉 节庆习俗", "🏠 建筑风格",
             "🏫 教育制度", "💼 工作环境", "🏥 医疗体系", "🏙️ 现代都市", "🌿 自然生态"],
            default=["🍜 美食文化", "🏛️ 历史文化"]
        )

        race_interests = st.multiselect(
            "想了解哪个族群的文化",
            ["华族文化", "马来族文化", "印度族文化", "欧亚裔文化", "多元融合文化"],
            default=["华族文化", "多元融合文化"]
        )

        special_requests = st.text_area(
            "特别感兴趣的内容 (无则留空)",
            placeholder="如：想了解小贩中心、组屋制度、政府大厦等"
        )

        submitted = st.form_submit_button("保存偏好", use_container_width=True)

        if submitted:
            st.session_state.user_preferences = {
                "language": language,
                "visit_duration": visit_duration,
                "interest_level": interest_level,
                "interests": interests,
                "race_interests": race_interests,
                "special_requests": special_requests if special_requests else "无"
            }
            st.session_state.profile_completed = True

            # 生成个性化推荐
            with st.spinner("🇸🇬 正在为您定制文化探索计划..."):
                pref_prompt = f"""
请根据以下用户偏好，生成一份新加坡文化探索计划：

【用户偏好】
- 首选语言：{language}
- 计划访问时长：{visit_duration}
- 了解程度：{interest_level}
- 感兴趣领域：{', '.join(interests)}
- 感兴趣族群：{', '.join(race_interests)}
- 特别需求：{special_requests}

请按照以下结构输出：

## 🎯 文化探索目标
（根据用户偏好确定探索重点）

## 📅 探索日程建议
（根据访问时长给出每日推荐活动）

## 🎭 必体验的文化活动
（推荐最具代表性的文化体验）

## 🍜 美食推荐
（结合文化背景推荐必尝美食）

## 💡 实用小贴士
（文化礼仪、禁忌、当地习惯）

开始制定计划：
"""

                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                messages.append({"role": "user", "content": pref_prompt})

                plan = call_claude_api(messages)
                st.session_state.exploration_plan = plan

                # 保存初始对话
                st.session_state.messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "assistant", "content": f"您的文化偏好已设置完成！\n- 感兴趣：{', '.join(interests)}\n- 计划：{visit_duration}\n\n您可以点击「文化探索」查看详细计划，或直接在下方提问关于新加坡文化的任何问题。"}
                ]

            st.success("✅ 偏好设置完成！请点击「文化探索」查看定制计划。")

    # 显示已保存的偏好
    if st.session_state.user_preferences:
        st.markdown("---")
        st.subheader("已保存偏好")
        pref = st.session_state.user_preferences
        cols = st.columns(3)
        cols[0].metric("语言", pref["language"])
        cols[1].metric("访问计划", pref["visit_duration"])
        cols[2].metric("了解程度", pref["interest_level"])
        st.markdown(f"**兴趣领域：** {', '.join(pref['interests'])}")

# ========== 页面2: 文化探索 ==========
elif st.session_state.page == "explore":
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🎭 新加坡文化探索")
    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.user_preferences:
        st.warning("请先在「我的文化偏好」中设置您的偏好！")
    elif not st.session_state.profile_completed:
        st.warning("偏好尚未设置，请先提交偏好表单！")
    else:
        # 显示用户偏好概览
        pref = st.session_state.user_preferences
        with st.container():
            col1, col2, col3 = st.columns(3)
            col1.info(f"🎯 计划：{pref['visit_duration']}")
            col2.info(f"🌍 语言：{pref['language']}")
            col3.info(f"📚 程度：{pref['interest_level']}")

        st.markdown("---")
        st.markdown(st.session_state.exploration_plan)

        # 探索更多按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 向专家提问"):
                st.session_state.page = "chat"
        with col2:
            if st.button("🗺️ 获取旅游攻略"):
                st.session_state.page = "travel"

# ========== 页面3: 文化问答 ==========
elif st.session_state.page == "chat":
    # 顶部工具栏
    col1, col2, col3 = st.columns([6, 2, 2])
    with col1:
        st.markdown('<div class="main-header"><h2 style="margin:0;">🇸🇬 新加坡文化助手</h2></div>', unsafe_allow_html=True)
    with col2:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
    with col3:
        if st.button("🔄 新对话", use_container_width=True):
            st.session_state.messages = []

    # 用户偏好卡片
    if st.session_state.user_preferences:
        pref = st.session_state.user_preferences
        with st.container():
            st.markdown("""
            <style>
                .user-info-bar {
                    background: #f8f9fa;
                    padding: 10px 20px;
                    border-radius: 8px;
                    margin: 10px 0 20px 0;
                    border-left: 4px solid #e31e24;
                }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="user-info-bar">
                <strong>🗣️ {pref['language']}</strong> |
                <strong>📅 {pref['visit_duration']}</strong> |
                <strong>🎭 {pref['interest_level']}</strong> |
                <strong>✨ {', '.join(pref['interests'][:2])}</strong>
            </div>
            """, unsafe_allow_html=True)

    # 欢迎消息
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h3>👋 欢迎探索新加坡文化</h3>
            <p style='color: #666;'>我是您的新加坡文化专家，可以帮您：</p>
            <div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin: 15px 0;'>
                <span style='background: #ffebee; padding: 8px 16px; border-radius: 20px; color: #c62828;'>🍜 美食文化介绍</span>
                <span style='background: #e8f5e9; padding: 8px 16px; border-radius: 20px; color: #2e7d32;'>🎭 节庆习俗讲解</span>
                <span style='background: #fff3e0; padding: 8px 16px; border-radius: 20px; color: #ef6c00;'>🏛️ 历史文化解读</span>
                <span style='background: #f3e5f5; padding: 8px 16px; border-radius: 20px; color: #6a1b9a;'>💬 当地生活指南</span>
                <span style='background: #e3f2fd; padding: 8px 16px; border-radius: 20px; color: #1565c0;'>🗣️ 语言学习帮助</span>
            </div>
            <p style='color: #999; margin-top: 5px;'>↓ 在下方输入框开始提问吧～ ↓</p>
        </div>
        """, unsafe_allow_html=True)

    # 显示聊天历史
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg['content'])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🇸🇬"):
                st.markdown(msg['content'])

    # 底部输入框
    if prompt := st.chat_input("有什么关于新加坡文化的问题想咨询？"):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 显示用户消息
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # AI回复
        with st.chat_message("assistant", avatar="🇸🇬"):
            with st.spinner("专家思考中..."):
                # 准备上下文
                context = ""
                if st.session_state.user_preferences:
                    pref = st.session_state.user_preferences
                    context = f"\n\n【用户文化偏好】语言：{pref['language']}，访问计划：{pref['visit_duration']}，了解程度：{pref['interest_level']}，兴趣领域：{', '.join(pref['interests'])}\n"

                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                # 过滤掉原有的 system 消息，保留其他消息
                for msg in st.session_state.messages:
                    if msg["role"] != "system":
                        messages.append(msg)

                # 在最后一条用户消息后添加上下文
                if messages and messages[-1]["role"] == "user":
                    messages[-1]["content"] += context

                ai_reply = call_claude_api(messages)

        # 保存AI回复
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

        # 显示AI回复
        with st.chat_message("assistant", avatar="🇸🇬"):
            st.markdown(ai_reply)

        st.rerun()

# ========== 页面4: 旅游助手 ==========
elif st.session_state.page == "travel":
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🗺️ 新加坡旅游助手")
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("快速问答")
    travel_questions = [
        "🍜 推荐的小贩中心有哪些？",
        "🏛️ 必访的历史景点？",
        "🎭 本月有什么节庆活动？",
        "🏙️ 滨海湾有什么好玩的地方？",
        "🌿 植物园和滨海湾花园哪个更好？"
    ]

    cols = st.columns(3)
    for i, question in enumerate(travel_questions):
        if cols[i % 3].button(question, use_container_width=True):
            st.session_state.page = "chat"
            st.session_state.messages.append({"role": "user", "content": question})

    st.markdown("---")

    st.subheader("旅游信息卡片")
    with st.expander("📍 地理与气候"):
        st.info("""
        **地理位置**: 位于马来半岛南端，赤道附近
        **气候**: 热带雨林气候，全年温暖潮湿
        - 平均气温：26-31°C
        - 降雨：全年均匀，11月-1月雨季较明显
        - 最佳旅游时间：全年适宜
        """)

    with st.expander("💰 货币与支付"):
        st.info("""
        **货币**: 新加坡元 (SGD)
        **支付方式**:
        - 信用卡/借记卡：广泛接受
        - PayNow：本地电子支付
        - 现金：小贩中心、小店需要
        **消费水平**: 中高，比东南亚其他国家高
        """)

    with st.expander("🚇 交通系统"):
        st.info("""
        **公共交通**:
        - MRT（地铁）：快速便捷，覆盖主要景点
        - 巴士：路线覆盖全面
        - 德士（出租车）：Grab等打车App
        **交通卡**: EZ-Link卡，可在便利店购买
        **旅游贴士**: 购买游客交通卡更划算
        """)

    with st.expander("📱 实用App"):
        st.info("""
        **必备应用**:
        - Grab：打车、送餐
        - EZ-Link：交通卡管理
        - SingPass：政府服务（长期居民）
        - SG Secure：紧急信息
        - Weather：天气预报
        """)

    if st.button("💬 向文化专家咨询更多", use_container_width=True):
        st.session_state.page = "chat"

# ==================== 页脚 ====================
st.markdown("---")
st.markdown(
    """
    <div class="main-footer">
        🇸🇬 新加坡文化交流问答系统 | 一个国家，多种文化<br>
        Designed by Singapore Culture Assistant
    </div>
    """,
    unsafe_allow_html=True
)
