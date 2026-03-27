from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path

from .config import get_settings
from .services.claude_service import ClaudeService
from .services.storage import StorageService

# 创建FastAPI应用
settings = get_settings()
app = FastAPI(title=settings.app_title, version=settings.app_version)

# 初始化服务
claude_service = ClaudeService(
    api_key=settings.anthropic_api_key,
    model=settings.claude_model,
    max_tokens=settings.claude_max_tokens,
    temperature=settings.claude_temperature
)
storage_service = StorageService(conversations_dir=settings.conversations_dir)

# 读取HTML模板
BASE_DIR = Path(__file__).resolve().parent.parent
HTML_TEMPLATE = (BASE_DIR / "app" / "templates" / "index.html").read_text(encoding="utf-8")


# Pydantic模型
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class ConversationListResponse(BaseModel):
    conversations: List[Dict]


# 路由
@app.get("/", response_class=HTMLResponse)
async def index():
    """主页"""
    return HTMLResponse(content=HTML_TEMPLATE.replace("{{ app_title }}", settings.app_title))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与AI进行对话

    - message: 用户消息
    - conversation_id: 可选的对话ID，用于继续已有对话
    """
    try:
        # 如果没有提供conversation_id，创建新对话
        if not request.conversation_id:
            conversation_id = storage_service.create_conversation()
        else:
            conversation_id = request.conversation_id
            # 验证对话是否存在
            if not storage_service.get_conversation(conversation_id):
                raise HTTPException(status_code=404, detail="对话不存在")

        # 保存用户消息
        storage_service.add_message(conversation_id, "user", request.message)

        # 获取对话历史
        conversation_data = storage_service.get_conversation(conversation_id)
        conversation_history = conversation_data["messages"][:-1]  # 排除刚添加的消息

        # 调用Claude API
        ai_response = claude_service.chat(request.message, conversation_history)

        # 保存AI回复
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


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_title}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
