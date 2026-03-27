from anthropic import Anthropic
from typing import List, Dict


class ClaudeService:
    """Claude API服务"""

    # 新加坡文化交流系统提示词
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
        """
        与Claude对话

        Args:
            message: 用户消息
            conversation_history: 对话历史列表，格式为 [{"role": "user", "content": "..."}]

        Returns:
            Claude的回复
        """
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
