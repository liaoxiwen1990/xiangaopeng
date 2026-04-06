#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇸🇬 新加坡文化交流系统 - 单文件版本

一个专业且亲切的新加坡文化交流Web应用，基于 FastAPI 和 Claude API 构建。

运行方式：
    python3 singapore_culture_exchange.py

依赖安装：
    pip install fastapi uvicorn anthropic python-dotenv jinja2 pydantic-settings
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from anthropic import Anthropic

# ============= 配置管理 =============
class Settings(BaseSettings):
    """应用配置"""
    app_title: str = "新加坡文化交流系统"
    app_version: str = "1.0.0"
    anthropic_api_key: str = ""
    data_dir: str = "data"
    conversations_dir: str = "data/conversations"
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 2000
    claude_temperature: float = 0.8

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_settings():
    """加载配置"""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠️  警告: 未找到 ANTHROPIC_API_KEY 环境变量")
        print("请在 .env 文件中设置: ANTHROPIC_API_KEY=your_key_here")
    return Settings(
        anthropic_api_key=api_key,
        app_title=os.getenv("APP_TITLE", "新加坡文化交流系统"),
        app_version=os.getenv("APP_VERSION", "1.0.0")
    )


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

    def list_conversations(self, limit: int = 50) -> List[Dict]:
        """列出最近的对话"""
        conversations = []

        for file_path in sorted(self.conversations_dir.glob("*.json"), reverse=True)[:limit]:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                conversations.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "message_count": len(data["messages"])
                })

        return conversations


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


# ============= HTML 模板 =============
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }

        .header p {
            font-size: 14px;
            opacity: 0.9;
        }

        .chat-container {
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 20px;
            display: flex;
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.assistant {
            justify-content: flex-start;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.6;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
        }

        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .input-wrapper {
            display: flex;
            gap: 10px;
        }

        #userInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 24px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }

        #userInput:focus {
            border-color: #667eea;
        }

        #sendBtn {
            padding: 12px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 24px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        #sendBtn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        #sendBtn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
            width: fit-content;
        }

        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }

        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        .welcome-message {
            text-align: center;
            color: #666;
            padding: 40px 20px;
        }

        .welcome-message h2 {
            font-size: 20px;
            margin-bottom: 12px;
            color: #333;
        }

        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
        }

        .suggestion-btn {
            padding: 8px 16px;
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s;
        }

        .suggestion-btn:hover {
            background: #667eea;
            color: white;
        }

        @media (max-width: 600px) {
            .container {
                border-radius: 0;
            }

            .message-content {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇸🇬 新加坡文化交流系统</h1>
            <p>探索新加坡多元文化，体验对话交流乐趣</p>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="welcome-message" id="welcomeMessage">
                <h2>欢迎来到新加坡文化交流系统！</h2>
                <p>我可以帮您了解新加坡的历史文化、风土人情、饮食习俗等<br>请随时向我提问，让我们一起探索新加坡的多元文化魅力</p>
                <div class="suggestions">
                    <button class="suggestion-btn" onclick="askQuestion('新加坡有哪些传统节日？')">新加坡有哪些传统节日？</button>
                    <button class="suggestion-btn" onclick="askQuestion('介绍一下新加坡的饮食文化')">介绍新加坡饮食文化</button>
                    <button class="suggestion-btn" onclick="askQuestion('新加坡有什么社交礼仪需要注意？')">新加坡社交礼仪</button>
                    <button class="suggestion-btn" onclick="askQuestion('新加坡的语言有什么特点？')">新加坡语言特点</button>
                </div>
            </div>
        </div>

        <div class="input-container">
            <div class="input-wrapper">
                <input type="text" id="userInput" placeholder="输入您的问题..." onkeypress="handleKeyPress(event)">
                <button id="sendBtn" onclick="sendMessage()">发送</button>
            </div>
        </div>
    </div>

    <script>
        let conversationId = null;
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const welcomeMessage = document.getElementById('welcomeMessage');

        function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = content.replace(/\\n/g, '<br>');

            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typingIndicator';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'typing-indicator';
            contentDiv.style.display = 'block';
            contentDiv.innerHTML = '<span></span><span></span><span></span>';

            typingDiv.appendChild(contentDiv);
            chatContainer.appendChild(typingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function hideTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) typing.remove();
        }

        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }

            addMessage(message, true);
            userInput.value = '';
            sendBtn.disabled = true;

            showTyping();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId
                    })
                });

                if (!response.ok) {
                    throw new Error('请求失败');
                }

                const data = await response.json();
                conversationId = data.conversation_id;

                hideTyping();
                addMessage(data.response, false);

            } catch (error) {
                hideTyping();
                addMessage('抱歉，发生了错误，请稍后再试。', false);
                console.error('Error:', error);
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        function askQuestion(question) {
            userInput.value = question;
            sendMessage();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        userInput.focus();
    </script>
</body>
</html>'''


# ============= Pydantic 模型 =============
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class ConversationListResponse(BaseModel):
    conversations: List[Dict]


# ============= FastAPI 应用 =============
def create_app():
    """创建FastAPI应用"""
    settings = load_settings()
    app = FastAPI(title=settings.app_title, version=settings.app_version)

    # 初始化服务
    claude_service = ClaudeService(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
        temperature=settings.claude_temperature
    )
    storage_service = StorageService(conversations_dir=settings.conversations_dir)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """主页"""
        return HTMLResponse(content=HTML_TEMPLATE.replace("{{ app_title }}", settings.app_title))

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """与AI进行对话"""
        try:
            if not request.conversation_id:
                conversation_id = storage_service.create_conversation()
            else:
                conversation_id = request.conversation_id
                if not storage_service.get_conversation(conversation_id):
                    raise HTTPException(status_code=404, detail="对话不存在")

            storage_service.add_message(conversation_id, "user", request.message)

            conversation_data = storage_service.get_conversation(conversation_id)
            conversation_history = conversation_data["messages"][:-1]

            ai_response = claude_service.chat(request.message, conversation_history)

            storage_service.add_message(conversation_id, "assistant", ai_response)

            return ChatResponse(response=ai_response, conversation_id=conversation_id)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/conversations/{conversation_id}")
    async def get_conversation(conversation_id: str):
        """获取对话历史"""
        conversation = storage_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        return JSONResponse(content=conversation)

    @app.get("/api/conversations", response_model=ConversationListResponse)
    async def list_conversations(limit: int = 50):
        """列出所有对话"""
        conversations = storage_service.list_conversations(limit=limit)
        return ConversationListResponse(conversations=conversations)

    @app.post("/api/conversations/new")
    async def create_conversation():
        """创建新对话"""
        conversation_id = storage_service.create_conversation()
        return {"conversation_id": conversation_id}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": settings.app_title}

    return app


# ============= 主程序入口 =============
if __name__ == "__main__":
    import uvicorn

    print("🇸🇬 新加坡文化交流系统启动中...")
    print("=" * 50)

    # 检查环境变量
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠️  警告: 未找到 ANTHROPIC_API_KEY")
        print("请创建 .env 文件并添加以下内容:")
        print("   ANTHROPIC_API_KEY=your_actual_api_key_here")
        print()
        print("获取 API Key: https://console.anthropic.com/")
        print("=" * 50)
    else:
        print("✅ API Key 已配置")

    print()
    print("🚀 启动服务器...")
    print("📍 本地访问: http://localhost:8000")
    print("📍 局域网访问: http://0.0.0.0:8000")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    print()

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
