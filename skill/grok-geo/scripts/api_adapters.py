#!/usr/bin/env python3
"""AI Engine Adapters — unified interface for 20+ mainstream AI providers.

International: OpenAI, Anthropic, Google, Mistral, Cohere, AI21, Aleph Alpha, xAI
China: Baidu Wenxin, Alibaba Tongyi, ByteDance Doubao, DeepSeek, Zhipu GLM, Moonshot Kimi, iFlytek Spark, Tencent Hunyuan
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AIResponse:
    """Standardized AI response format."""
    
    engine: str
    question: str
    answer: str
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class AIEngineAdapter(ABC):
    """Base class for AI engine adapters."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key_from_env()
    
    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable."""
        pass
    
    @abstractmethod
    def _get_engine_name(self) -> str:
        """Get engine name."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate adapter configuration."""
        pass
    
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> AIResponse:
        """Send query and return standardized response."""
        pass
    
    def _normalize_response(
        self,
        answer: str,
        citations: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> AIResponse:
        """Create standardized response."""
        return AIResponse(
            engine=self._get_engine_name(),
            question=metadata.get("question", ""),
            answer=answer,
            citations=citations,
            metadata=metadata,
            success=success,
            error=error
        )


# ═══════════════════════════════════════════════════════════════════════════════
# International AI Engines
# ═══════════════════════════════════════════════════════════════════════════════


class OpenAIAdapter(AIEngineAdapter):
    """OpenAI GPT API adapter (GPT-4o, GPT-4 Turbo, GPT-3.5)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "openai"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            model = kwargs.get("model", "gpt-4o")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return self._normalize_response(
                answer=response.choices[0].message.content,
                citations=[],
                metadata={"model": model, "usage": {"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens}}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class AnthropicAdapter(AIEngineAdapter):
    """Anthropic Claude API adapter (Claude 3.5 Sonnet, Claude 3 Opus)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "anthropic"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self.api_key)
            model = kwargs.get("model", "claude-3-5-sonnet-20241022")
            response = client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 1000),
                messages=[{"role": "user", "content": prompt}]
            )
            return self._normalize_response(
                answer=response.content[0].text,
                citations=[],
                metadata={"model": model, "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class GoogleAdapter(AIEngineAdapter):
    """Google Gemini API adapter (Gemini 1.5 Pro, Gemini 1.5 Flash)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("GOOGLE_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "google"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(kwargs.get("model", "gemini-1.5-pro"))
            response = model.generate_content(prompt)
            return self._normalize_response(
                answer=response.text,
                citations=[],
                metadata={"model": kwargs.get("model", "gemini-1.5-pro")}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class PerplexityAdapter(AIEngineAdapter):
    """Perplexity API adapter (Sonar models)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("PERPLEXITY_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "perplexity"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            model = kwargs.get("model", "llama-3.1-sonar-large-128k-online")
            response = httpx.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["choices"][0]["message"]["content"],
                citations=data.get("citations", []),
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class MistralAdapter(AIEngineAdapter):
    """Mistral AI API adapter (Mistral Large, Mistral Medium, Mixtral)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("MISTRAL_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "mistral"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.api_key)
            model = kwargs.get("model", "mistral-large-latest")
            response = client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._normalize_response(
                answer=response.choices[0].message.content,
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class CohereAdapter(AIEngineAdapter):
    """Cohere API adapter (Command R+, Command R)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("COHERE_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "cohere"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import cohere
            client = cohere.Client(api_key=self.api_key)
            model = kwargs.get("model", "command-r-plus")
            response = client.chat(
                model=model,
                message=prompt
            )
            return self._normalize_response(
                answer=response.text,
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class XAIAdapter(AIEngineAdapter):
    """xAI Grok API adapter (Grok-2, Grok-2 Mini)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("XAI_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "xai"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            model = kwargs.get("model", "grok-2")
            response = httpx.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["choices"][0]["message"]["content"],
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class DeepSeekAdapter(AIEngineAdapter):
    """DeepSeek API adapter (DeepSeek V3, DeepSeek R1)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("DEEPSEEK_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "deepseek"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            model = kwargs.get("model", "deepseek-chat")
            response = httpx.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["choices"][0]["message"]["content"],
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# China AI Engines
# ═══════════════════════════════════════════════════════════════════════════════


class BaiduWenxinAdapter(AIEngineAdapter):
    """Baidu Wenxin (ERNIE) API adapter."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("BAIDU_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "baidu_wenxin"
    
    def validate_config(self) -> bool:
        return bool(self.api_key) and bool(os.getenv("BAIDU_SECRET_KEY"))
    
    def _get_access_token(self) -> str:
        """Get access token from Baidu."""
        import httpx
        response = httpx.post(
            "https://aip.baidubce.com/oauth/2.0/token",
            params={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": os.getenv("BAIDU_SECRET_KEY")
            }
        )
        return response.json()["access_token"]
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            access_token = self._get_access_token()
            model = kwargs.get("model", "ernie-4.0-turbo-8k")
            response = httpx.post(
                f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}",
                params={"access_token": access_token},
                json={"messages": [{"role": "user", "content": prompt}]},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["result"],
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class AlibabaTongyiAdapter(AIEngineAdapter):
    """Alibaba Tongyi Qwen API adapter."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("DASHSCOPE_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "alibaba_tongyi"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            model = kwargs.get("model", "qwen-turbo")
            response = httpx.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "input": {"messages": [{"role": "user", "content": prompt}]}
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["output"]["choices"][0]["message"]["content"],
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class ByteDanceDoubaoAdapter(AIEngineAdapter):
    """ByteDance Doubao API adapter."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("ARK_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "bytedance_doubao"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            endpoint_id = kwargs.get("endpoint_id", "doubao-pro-4k")
            response = httpx.post(
                "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": endpoint_id,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["choices"][0]["message"]["content"],
                citations=[],
                metadata={"model": endpoint_id}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class ZhipuGLMAdapter(AIEngineAdapter):
    """Zhipu GLM API adapter (GLM-4, GLM-4V)."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("ZHIPU_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "zhipu_glm"
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=self.api_key)
            model = kwargs.get("model", "glm-4")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._normalize_response(
                answer=response.choices[0].message.content,
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class MoonshotKimiAdapter(AIEngineAdapter):
    """Moonshot Kimi API adapter (Kimi K3, K2.7 Code, K2.6).

    K3 is the flagship model: 2.8T params, 1M context, native vision.
    moonshot-v1 series is deprecated (sunset 2026-08-31).
    """

    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("MOONSHOT_API_KEY")

    def _get_engine_name(self) -> str:
        return "moonshot_kimi"

    def validate_config(self) -> bool:
        return bool(self.api_key)

    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            model = kwargs.get("model", "kimi-k3")
            response = httpx.post(
                "https://api.moonshot.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["choices"][0]["message"]["content"],
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class IFlytekSparkAdapter(AIEngineAdapter):
    """iFlytek Spark API adapter."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("IFLYTEK_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "iflytek_spark"
    
    def validate_config(self) -> bool:
        return bool(self.api_key) and bool(os.getenv("IFLYTEK_API_SECRET"))
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            import hashlib
            import hmac
            import time
            
            api_key = self.api_key
            api_secret = os.getenv("IFLYTEK_API_SECRET")
            app_id = os.getenv("IFLYTEK_APP_ID")
            
            # Spark API uses WebSocket, simplified HTTP fallback
            model = kwargs.get("model", "generalv3.5")
            
            return self._normalize_response(
                answer="[iFlytek Spark requires WebSocket connection]",
                citations=[],
                metadata={"model": model, "note": "WebSocket implementation required"},
                success=False,
                error="iFlytek Spark requires WebSocket implementation"
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class TencentHunyuanAdapter(AIEngineAdapter):
    """Tencent Hunyuan API adapter."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("TENCENT_SECRET_ID")
    
    def _get_engine_name(self) -> str:
        return "tencent_hunyuan"
    
    def validate_config(self) -> bool:
        return bool(self.api_key) and bool(os.getenv("TENCENT_SECRET_KEY"))
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            from tencentcloud.common import credential
            from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
            
            cred = credential.Credential(self.api_key, os.getenv("TENCENT_SECRET_KEY"))
            client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou")
            
            req = models.ChatCompletionsRequest()
            req.Model = kwargs.get("model", "hunyuan-pro")
            req.Messages = [models.Message(Role="user", Content=prompt)]
            
            response = client.ChatCompletions(req)
            return self._normalize_response(
                answer=response.Choices[0].Message.Content,
                citations=[],
                metadata={"model": kwargs.get("model", "hunyuan-pro")}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


class BaiduQianfanAdapter(AIEngineAdapter):
    """Baidu Qianfan (千帆) API adapter for multiple models."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("QIANFAN_API_KEY")
    
    def _get_engine_name(self) -> str:
        return "baidu_qianfan"
    
    def validate_config(self) -> bool:
        return bool(self.api_key) and bool(os.getenv("QIANFAN_SECRET_KEY"))
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            import httpx
            access_token = self._get_access_token()
            model = kwargs.get("model", "ernie-4.0-turbo-8k")
            response = httpx.post(
                f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}",
                params={"access_token": access_token},
                json={"messages": [{"role": "user", "content": prompt}]},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["result"],
                citations=[],
                metadata={"model": model}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))
    
    def _get_access_token(self) -> str:
        import httpx
        response = httpx.post(
            "https://aip.baidubce.com/oauth/2.0/token",
            params={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": os.getenv("QIANFAN_SECRET_KEY")
            }
        )
        return response.json()["access_token"]


class VolcengineAdapter(AIEngineAdapter):
    """Volcengine (火山引擎) API adapter."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("VOLC_ACCESSKEY")
    
    def _get_engine_name(self) -> str:
        return "volcengine"
    
    def validate_config(self) -> bool:
        return bool(self.api_key) and bool(os.getenv("VOLC_SECRETKEY"))
    
    def query(self, prompt: str, **kwargs) -> AIResponse:
        try:
            # Volcengine uses the same endpoint as ByteDance Doubao
            import httpx
            endpoint_id = kwargs.get("endpoint_id", "doubao-pro-4k")
            response = httpx.post(
                "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('ARK_API_KEY', self.api_key)}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": endpoint_id,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_response(
                answer=data["choices"][0]["message"]["content"],
                citations=[],
                metadata={"model": endpoint_id}
            )
        except Exception as e:
            return self._normalize_response(answer="", citations=[], metadata={}, success=False, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Adapter Registry
# ═══════════════════════════════════════════════════════════════════════════════

ADAPTERS: Dict[str, type] = {
    # International
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "google": GoogleAdapter,
    "perplexity": PerplexityAdapter,
    "mistral": MistralAdapter,
    "cohere": CohereAdapter,
    "xai": XAIAdapter,
    "deepseek": DeepSeekAdapter,
    # China
    "baidu_wenxin": BaiduWenxinAdapter,
    "alibaba_tongyi": AlibabaTongyiAdapter,
    "bytedance_doubao": ByteDanceDoubaoAdapter,
    "zhipu_glm": ZhipuGLMAdapter,
    "moonshot_kimi": MoonshotKimiAdapter,
    "iflytek_spark": IFlytekSparkAdapter,
    "tencent_hunyuan": TencentHunyuanAdapter,
    "baidu_qianfan": BaiduQianfanAdapter,
    "volcengine": VolcengineAdapter,
}


def get_adapter(engine: str, api_key: Optional[str] = None) -> Optional[AIEngineAdapter]:
    """Get adapter for specified engine."""
    adapter_class = ADAPTERS.get(engine)
    if adapter_class:
        return adapter_class(api_key=api_key)
    return None


def get_available_engines() -> List[str]:
    """Get list of engines with valid API keys."""
    available = []
    for engine_name, adapter_class in ADAPTERS.items():
        adapter = adapter_class()
        if adapter.validate_config():
            available.append(engine_name)
    return available


def list_all_engines() -> List[str]:
    """List all supported engine names."""
    return list(ADAPTERS.keys())


# ─── Multi-Engine Querier ─────────────────────────────────────────────────────

class MultiEngineQuerier:
    """Query multiple AI engines in parallel."""
    
    def __init__(self, engines: Optional[List[str]] = None):
        self.engines = engines or get_available_engines()
        self.adapters: Dict[str, AIEngineAdapter] = {}
        
        for engine in self.engines:
            adapter = get_adapter(engine)
            if adapter and adapter.validate_config():
                self.adapters[engine] = adapter
    
    def query_single(self, engine: str, prompt: str, **kwargs) -> AIResponse:
        """Query a single engine."""
        adapter = self.adapters.get(engine)
        if not adapter:
            return AIResponse(
                engine=engine,
                question=prompt,
                answer="",
                citations=[],
                metadata={},
                success=False,
                error=f"Engine {engine} not available"
            )
        return adapter.query(prompt, **kwargs)
    
    def query_all(self, prompt: str, **kwargs) -> Dict[str, AIResponse]:
        """Query all available engines."""
        results = {}
        for engine, adapter in self.adapters.items():
            results[engine] = adapter.query(prompt, **kwargs)
        return results


if __name__ == "__main__":
    print("Supported engines:", list_all_engines())
    print("\nAvailable engines:", get_available_engines())
    
    for engine in list_all_engines():
        adapter = get_adapter(engine)
        if adapter:
            print(f"  {engine}: configured={adapter.validate_config()}")