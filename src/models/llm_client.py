"""LLM 客户端封装，支持多模型切换"""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from src.config import MODEL_CONFIG, DEFAULT_MODEL


class LLMClient:
    """大模型调用客户端，支持切换不同模型供应商"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_MODEL
        self._client = self._create_client()
        self.total_tokens = 0

    def _create_client(self) -> ChatOpenAI:
        """根据模型名称创建对应的 ChatOpenAI 客户端"""
        config = MODEL_CONFIG.get(self.model_name)
        if not config:
            raise ValueError(f"未知模型: {self.model_name}，可选: {list(MODEL_CONFIG.keys())}")

        return ChatOpenAI(
            model=config["model"],
            base_url=config["base_url"],
            api_key=config["api_key"],
            temperature=0.3,
        )

    def switch_model(self, model_name: str):
        """切换模型"""
        self.model_name = model_name
        self._client = self._create_client()

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """发送对话请求，返回文本结果"""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        kwargs = {}
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self._client.invoke(messages, **kwargs)

        # 统计 Token
        if response.response_metadata and "token_usage" in response.response_metadata:
            usage = response.response_metadata["token_usage"]
            self.total_tokens += usage.get("total_tokens", 0)

        return response.content

    async def achat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """异步发送对话请求"""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        kwargs = {}
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = await self._client.ainvoke(messages, **kwargs)

        if response.response_metadata and "token_usage" in response.response_metadata:
            usage = response.response_metadata["token_usage"]
            self.total_tokens += usage.get("total_tokens", 0)

        return response.content

    def get_token_usage(self) -> int:
        """获取累计 Token 消耗"""
        return self.total_tokens
