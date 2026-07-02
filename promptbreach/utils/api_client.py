"""
Copyright (c) 2026 八方网域-无涯

统一API客户端模块
支持多种AI服务商：Ollama、Kimi、DeepSeek、MiniMax等
支持自定义兼容 OpenAI / Anthropic 格式的服务商
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import requests

# Anthropic SDK (用于 MiniMax 和 Anthropic 兼容格式)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


# ============== 日志配置 ==============
def setup_logger(name: str = "api_client") -> logging.Logger:
    """配置并返回日志记录器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


# ============== 服务商配置 ==============
class ProviderConfig:
    """API服务商配置"""
    
    # Ollama (本地)
    OLLAMA = {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434",
        "default_model": "qwen3.5:0.8b",
        "api_key_required": False,
        "supports_stream": True,
        "endpoint": "/api/generate",
        "needs_system_prefix": False,
    }
    
        
    # MiniMax (使用 Anthropic SDK)
    MINIMAX = {
        "name": "MiniMax (Anthropic)",
        "base_url": "https://api.minimaxi.com/anthropic",
        "default_model": "MiniMax-M2",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "anthropic",
        "needs_system_prefix": True,
        "group_id": "",
    }

        
    # 智谱 AI (GLM)
    ZHIPU = {
        "name": "智谱 AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
    }
    
    # Kimi (月之暗面)
    KIMI = {
        "name": "Kimi (月之暗面)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
    }
    
    # DeepSeek
    DEEPSEEK = {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-v4-flash",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
    }

    # 小米 MiMo
    XIAOMI = {
        "name": "小米 MiMo",
        "base_url": "https://api.xiaomimimo.com/v1",
        "default_model": "mimo-v2.5",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
    }

    
    # SiliconFlow (兼容多种模型)
    SILICONFLOW = {
        "name": "SiliconFlow (兼容多模型)",
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Qwen/Qwen2.5-7B-Instruct",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
    }

    # 字节火山 (Doubao)
    DOUBAO = {
        "name": "字节火山 (Doubao)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-pro-32k",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
    }

    # 自定义 OpenAI 兼容格式
    CUSTOM_OPENAI = {
        "name": "自定义 OpenAI 兼容",
        "base_url": "",
        "default_model": "",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "/chat/completions",
        "needs_system_prefix": True,
        "format": "openai",
    }

    # 自定义 Anthropic 兼容格式
    CUSTOM_ANTHROPIC = {
        "name": "自定义 Anthropic 兼容",
        "base_url": "",
        "default_model": "",
        "api_key_required": True,
        "supports_stream": True,
        "endpoint": "anthropic",
        "needs_system_prefix": True,
        "format": "anthropic",
    }


# ============== 抽象基类 ==============
class BaseAPIClient(ABC):
    """API客户端抽象基类"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        """生成文本响应"""
        pass
    
    @abstractmethod
    def check_connection(self) -> bool:
        """检查连接状态"""
        pass


# ============== Ollama 客户端 ==============
class OllamaClient(BaseAPIClient):
    """Ollama API 客户端 (本地)"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3.5:0.8b",
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session = requests.Session()
        self.provider_name = "Ollama"
        logger.info(f"[Ollama] 初始化完成，地址: {self.base_url}, 模型: {self.model}")
    
    def check_connection(self) -> bool:
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                logger.info("[Ollama] 连接成功")
                return True
            return False
        except Exception as e:
            logger.warning(f"[Ollama] 连接失败: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": temperature}
        }
        
        if system:
            data["system"] = system
        
        if context:
            data["context"] = context
        
        logger.info(f"[Ollama Request] Model: {self.model}")
        
        try:
            response = self._session.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[Ollama Response] 耗时: {elapsed_time:.2f}s")
                return result
            else:
                logger.error(f"[Ollama Error] HTTP {response.status_code}: {response.text}")
                return {"response": f"[Ollama 错误: HTTP {response.status_code}]", "done": True}
                
        except requests.exceptions.Timeout:
            logger.error(f"[Ollama Timeout] 请求超时 ({self.timeout}s)")
            return {"response": "[Ollama 错误: 请求超时]", "done": True}
        except Exception as e:
            logger.error(f"[Ollama Exception] {e}")
            return {"response": f"[Ollama 错误: {e}]", "done": True}


# ============== OpenAI兼容客户端 ==============
class OpenAICompatibleClient(BaseAPIClient):
    """OpenAI兼容格式的API客户端（Kimi、DeepSeek、MiniMax等）"""
    
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        timeout: int = 60,
        provider_name: str = "API"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.provider_name = provider_name
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        logger.info(f"[{provider_name}] 初始化完成，地址: {base_url}, 模型: {model}")
    
    def check_connection(self) -> bool:
        try:
            response = self._session.get(
                f"{self.base_url}/models",
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"[{self.provider_name}] 连接成功")
                return True
            logger.warning(f"[{self.provider_name}] 连接失败: HTTP {response.status_code}")
            return False
        except Exception as e:
            logger.warning(f"[{self.provider_name}] 连接失败: {e}")
            return False

    def fetch_models(self) -> Tuple[bool, List[str]]:
        """通过 /models 接口获取可用模型列表（不需要 API Key）"""
        # 创建一个不带 API Key 的 session 获取模型列表
        temp_session = requests.Session()
        temp_session.headers.update({
            "Content-Type": "application/json"
        })
        
        try:
            response = temp_session.get(
                f"{self.base_url}/models",
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                # OpenAI 格式: {"data": [{"id": "model-name", ...}, ...]}
                models_data = result.get("data", [])
                model_ids = [m.get("id", "") for m in models_data if m.get("id")]
                if model_ids:
                    model_ids.sort()
                    logger.info(f"[{self.provider_name}] 获取到 {len(model_ids)} 个模型")
                    return True, model_ids
                # 有些 API 返回 {"models": [...]}
                models_alt = result.get("models", [])
                if isinstance(models_alt, list):
                    model_ids = []
                    for m in models_alt:
                        if isinstance(m, str):
                            model_ids.append(m)
                        elif isinstance(m, dict):
                            model_ids.append(m.get("name", m.get("id", "")))
                    model_ids = [mid for mid in model_ids if mid]
                    if model_ids:
                        model_ids.sort()
                        logger.info(f"[{self.provider_name}] 获取到 {len(model_ids)} 个模型")
                        return True, model_ids
                logger.warning(f"[{self.provider_name}] 模型列表为空")
                return False, []
            else:
                # 如果不带 Key 失败，尝试带 Key
                logger.info(f"[{self.provider_name}] 无 Key 访问失败，尝试带 Key...")
                response = self._session.get(
                    f"{self.base_url}/models",
                    timeout=10
                )
                if response.status_code == 200:
                    result = response.json()
                    models_data = result.get("data", [])
                    model_ids = [m.get("id", "") for m in models_data if m.get("id")]
                    if model_ids:
                        model_ids.sort()
                        logger.info(f"[{self.provider_name}] 获取到 {len(model_ids)} 个模型")
                        return True, model_ids
                    models_alt = result.get("models", [])
                    if isinstance(models_alt, list):
                        model_ids = []
                        for m in models_alt:
                            if isinstance(m, str):
                                model_ids.append(m)
                            elif isinstance(m, dict):
                                model_ids.append(m.get("name", m.get("id", "")))
                        model_ids = [mid for mid in model_ids if mid]
                        if model_ids:
                            model_ids.sort()
                            logger.info(f"[{self.provider_name}] 获取到 {len(model_ids)} 个模型")
                            return True, model_ids
                logger.warning(f"[{self.provider_name}] 获取模型失败: HTTP {response.status_code}")
                return False, []
        except Exception as e:
            logger.warning(f"[{self.provider_name}] 获取模型失败: {e}")
            return False, []

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        messages = []
        
        # 添加系统消息
        if system:
            messages.append({
                "role": "system",
                "content": system
            })
        
        # 添加用户消息
        messages.append({
            "role": "user", 
            "content": prompt
        })
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        logger.info(f"[{self.provider_name} Request] Model: {self.model}")
        
        try:
            response = self._session.post(
                f"{self.base_url}/chat/completions",
                json=data,
                timeout=self.timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"[{self.provider_name} Response] 耗时: {elapsed_time:.2f}s")
                return {"response": content, "done": True}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"[{self.provider_name} Error] {error_msg}")
                return {"response": f"[{self.provider_name} 错误: {error_msg}]", "done": True}
                
        except requests.exceptions.Timeout:
            logger.error(f"[{self.provider_name} Timeout] 请求超时 ({self.timeout}s)")
            return {"response": f"[{self.provider_name} 错误: 请求超时]", "done": True}
        except Exception as e:
            logger.error(f"[{self.provider_name} Exception] {e}")
            return {"response": f"[{self.provider_name} 错误: {e}]", "done": True}


# ============== MiniMax 客户端 (Anthropic SDK) ==============
class MiniMaxClient(BaseAPIClient):
    """MiniMax API 客户端 (使用 Anthropic SDK)"""

    def __init__(
        self,
        api_key: str,
        model: str = "MiniMax-M2",
        timeout: int = 60,
        group_id: str = "",
        base_url: str = "https://api.minimaxi.com/anthropic"
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("请安装 anthropic SDK: pip install anthropic")

        self.model = model
        self.api_key = api_key
        self.group_id = group_id
        self.timeout = timeout
        self.provider_name = "MiniMax"

        # MiniMax 使用 Anthropic 格式
        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        logger.info(f"[MiniMax] 初始化完成，模型: {self.model}, base_url: {base_url}")

    def check_connection(self) -> bool:
        """检查连接状态 - MiniMax 无法直接检测，发送空消息测试"""
        try:
            self._client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            logger.info("[MiniMax] 连接成功")
            return True
        except Exception as e:
            logger.warning(f"[MiniMax] 连接失败: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 构建消息内容
        content_blocks = [{"type": "text", "text": prompt}]

        messages = [{
            "role": "user",
            "content": content_blocks
        }]

        logger.info(f"[MiniMax Request] Model: {self.model}")

        try:
            response = self._client.messages.create(
                model=self.model,
                system=system,
                messages=messages,
                temperature=temperature,
                max_tokens=2048,
            )

            elapsed_time = time.time() - start_time

            # 提取响应内容
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            logger.info(f"[MiniMax Response] 耗时: {elapsed_time:.2f}s")
            return {"response": response_text, "done": True}

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"[MiniMax Exception] {e}")
            return {"response": f"[MiniMax 错误: {e}]", "done": True}


# ============== Anthropic 兼容客户端 ==============
class AnthropicCompatibleClient(BaseAPIClient):
    """Anthropic 兼容格式的 API 客户端（支持自定义 Anthropic 格式服务商）"""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        timeout: int = 60,
        provider_name: str = "Anthropic"
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("请安装 anthropic SDK: pip install anthropic")

        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")

        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        logger.info(f"[{provider_name}] 初始化完成，地址: {base_url}, 模型: {model}")

    def check_connection(self) -> bool:
        try:
            self._client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            logger.info(f"[{self.provider_name}] 连接成功")
            return True
        except Exception as e:
            logger.warning(f"[{self.provider_name}] 连接失败: {e}")
            return False

    def fetch_models(self) -> Tuple[bool, List[str]]:
        """Anthropic 格式通常没有 /models 接口，返回空列表"""
        # Anthropic API 没有标准的 models 列表接口
        # 用户需要手动输入模型名称
        logger.info(f"[{self.provider_name}] Anthropic 格式不支持自动获取模型列表")
        return False, []

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        content_blocks = [{"type": "text", "text": prompt}]
        messages = [{"role": "user", "content": content_blocks}]

        logger.info(f"[{self.provider_name} Request] Model: {self.model}")

        try:
            response = self._client.messages.create(
                model=self.model,
                system=system,
                messages=messages,
                temperature=temperature,
                max_tokens=2048,
            )

            elapsed_time = time.time() - start_time

            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            logger.info(f"[{self.provider_name} Response] 耗时: {elapsed_time:.2f}s")
            return {"response": response_text, "done": True}

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"[{self.provider_name} Exception] {e}")
            return {"response": f"[{self.provider_name} 错误: {e}]", "done": True}


# ============== 统一客户端管理器 ==============
class UnifiedAPIClient:
    """统一API客户端管理器"""
    
    # 支持的服务商列表
    PROVIDERS = {
        "ollama": ProviderConfig.OLLAMA,
        "kimi": ProviderConfig.KIMI,
        "deepseek": ProviderConfig.DEEPSEEK,
        "xiaomi": ProviderConfig.XIAOMI,
        "minimax": ProviderConfig.MINIMAX,
        "siliconflow": ProviderConfig.SILICONFLOW,
        "zhipu": ProviderConfig.ZHIPU,
        "doubao": ProviderConfig.DOUBAO,
        "custom_openai": ProviderConfig.CUSTOM_OPENAI,
        "custom_anthropic": ProviderConfig.CUSTOM_ANTHROPIC,
    }
    
    def __init__(self):
        self._current_client: Optional[BaseAPIClient] = None
        self._current_provider: str = "ollama"
        self._config: Dict[str, Any] = {
            "provider": "ollama",
            "base_url": ProviderConfig.OLLAMA["base_url"],
            "model": ProviderConfig.OLLAMA["default_model"],
            "api_key": "",
            "timeout": 60,
            "saved_configs": [],
            "provider_api_keys": {},  # 新增：单独保存每个服务商的 API Key
        }
        self._load_config()
        self._init_client()
    
    def _load_config(self) -> None:
        """从配置文件加载配置"""
        config_path = Path("config/api_config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    self._config.update(saved_config)
                    logger.info(f"[Config] 已加载配置: {self._config['provider']}")
            except Exception as e:
                logger.warning(f"[Config] 加载配置失败: {e}")
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        config_path = Path("config/api_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info("[Config] 配置已保存")
        except Exception as e:
            logger.warning(f"[Config] 保存配置失败: {e}")
    
    def _init_client(self) -> None:
        """根据配置初始化客户端"""
        provider = self._config["provider"]

        if provider == "ollama":
            self._current_client = OllamaClient(
                base_url=self._config.get("base_url", ProviderConfig.OLLAMA["base_url"]),
                model=self._config.get("model", ProviderConfig.OLLAMA["default_model"]),
                timeout=self._config.get("timeout", 60)
            )
        elif provider == "minimax":
            # MiniMax 使用 Anthropic SDK
            self._current_client = MiniMaxClient(
                api_key=self._config.get("api_key", ""),
                model=self._config.get("model", ProviderConfig.MINIMAX["default_model"]),
                timeout=self._config.get("timeout", 60),
                group_id=self._config.get("group_id", ""),
                base_url=self._config.get("base_url", "https://api.minimaxi.com/anthropic")
            )
        elif provider == "custom_anthropic":
            # 自定义 Anthropic 兼容格式
            self._current_client = AnthropicCompatibleClient(
                base_url=self._config.get("base_url", ""),
                model=self._config.get("model", ""),
                api_key=self._config.get("api_key", ""),
                timeout=self._config.get("timeout", 60),
                provider_name="Custom-Anthropic"
            )
        else:
            # OpenAI兼容格式 (Kimi, DeepSeek, SiliconFlow, custom_openai等)
            provider_name = provider.upper() if provider != "custom_openai" else "Custom-OpenAI"
            self._current_client = OpenAICompatibleClient(
                base_url=self._config.get("base_url", ""),
                model=self._config.get("model", ""),
                api_key=self._config.get("api_key", ""),
                timeout=self._config.get("timeout", 60),
                provider_name=provider_name
            )

        self._current_provider = provider
    
    def set_provider(self, provider: str, base_url: str = None, model: str = None, 
                     api_key: str = None, timeout: int = None) -> bool:
        """切换服务商并更新配置"""
        # 获取服务商配置（内置或自定义）
        provider_config = self.PROVIDERS.get(provider, {})
        
        # 更新配置
        self._config["provider"] = provider
        self._config["base_url"] = base_url or provider_config.get("base_url", "")
        self._config["model"] = model or provider_config.get("default_model", "")
        if api_key is not None:
            self._config["api_key"] = api_key
        if timeout is not None:
            self._config["timeout"] = timeout
        
        # 重新初始化客户端
        self._init_client()
        
        # 保存配置
        self._save_config()
        
        provider_name = provider_config.get("name", provider)
        logger.info(f"[Provider] 已切换到: {provider_name}")
        return True
    
    def save_provider_api_key(self, provider: str, api_key: str) -> None:
        """保存指定服务商的 API Key"""
        if not api_key:
            return
        
        # 获取或初始化 provider_api_keys 字典
        provider_api_keys = self._config.get("provider_api_keys", {})
        provider_api_keys[provider] = api_key
        self._config["provider_api_keys"] = provider_api_keys
        
        # 保存配置
        self._save_config()
        logger.info(f"[Config] 已保存服务商 API Key: {provider}")
    
    def get_provider_api_key(self, provider: str) -> str:
        """获取指定服务商的 API Key"""
        provider_api_keys = self._config.get("provider_api_keys", {})
        return provider_api_keys.get(provider, "")
    
    def update_config(self, **kwargs) -> None:
        """更新单个配置项"""
        for key, value in kwargs:
            if key in self._config and value is not None:
                self._config[key] = value
        
        # 如果基础配置变了，重新初始化客户端
        if any(k in kwargs for k in ["provider", "base_url", "model", "api_key"]):
            self._init_client()
        
        self._save_config()
    
    def check_connection(self) -> bool:
        """检查当前连接状态"""
        if self._current_client:
            return self._current_client.check_connection()
        return False
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        context: Optional[list] = None
    ) -> Dict[str, Any]:
        """生成文本响应"""
        if self._current_client:
            return self._current_client.generate(
                prompt=prompt,
                system=system,
                temperature=temperature,
                stream=stream,
                context=context
            )
        return {"response": "[错误: 未初始化客户端]", "done": True}
    
    @property
    def current_provider(self) -> str:
        return self._current_provider
    
    @property
    def current_config(self) -> Dict[str, Any]:
        return self._config.copy()
    
    @property
    def available_providers(self) -> List[str]:
        return list(self.PROVIDERS.keys())
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """获取服务商信息"""
        if provider in self.PROVIDERS:
            return self.PROVIDERS[provider].copy()
        return {}

    def fetch_models(self) -> Tuple[bool, List[str]]:
        """通过当前客户端的 /models 接口获取可用模型列表"""
        if self._current_client and hasattr(self._current_client, 'fetch_models'):
            return self._current_client.fetch_models()
        return False, []

    def save_model_config(self, provider: str, base_url: str, model: str, api_key: str, timeout: int = 60) -> None:
        """保存模型配置到已保存列表"""
        saved_configs = self._config.get("saved_configs", [])
        
        # 检查是否已存在相同配置
        for i, config in enumerate(saved_configs):
            if config.get("provider") == provider and config.get("model") == model:
                # 更新现有配置
                saved_configs[i] = {
                    "provider": provider,
                    "base_url": base_url,
                    "model": model,
                    "api_key": api_key,
                    "timeout": timeout,
                    "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._config["saved_configs"] = saved_configs
                self._save_config()
                logger.info(f"[Config] 已更新模型配置: {provider}/{model}")
                return
        
        # 添加新配置
        saved_configs.append({
            "provider": provider,
            "base_url": base_url,
            "model": model,
            "api_key": api_key,
            "timeout": timeout,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._config["saved_configs"] = saved_configs
        self._save_config()
        logger.info(f"[Config] 已保存模型配置: {provider}/{model}")

    def get_saved_configs(self) -> List[Dict[str, Any]]:
        """获取已保存的模型配置列表"""
        return self._config.get("saved_configs", [])

    def load_saved_config(self, index: int) -> bool:
        """加载已保存的模型配置"""
        saved_configs = self._config.get("saved_configs", [])
        if 0 <= index < len(saved_configs):
            config = saved_configs[index]
            self._config["provider"] = config.get("provider", "ollama")
            self._config["base_url"] = config.get("base_url", "")
            self._config["model"] = config.get("model", "")
            self._config["api_key"] = config.get("api_key", "")
            self._config["timeout"] = config.get("timeout", 60)
            self._init_client()
            self._save_config()
            logger.info(f"[Config] 已加载模型配置: {config.get('provider')}/{config.get('model')}")
            return True
        return False

    def delete_saved_config(self, index: int) -> bool:
        """删除已保存的模型配置"""
        saved_configs = self._config.get("saved_configs", [])
        if 0 <= index < len(saved_configs):
            config = saved_configs.pop(index)
            self._config["saved_configs"] = saved_configs
            self._save_config()
            logger.info(f"[Config] 已删除模型配置: {config.get('provider')}/{config.get('model')}")
            return True
        return False


# ============== 全局实例 ==============
_client: Optional[UnifiedAPIClient] = None


def get_client() -> UnifiedAPIClient:
    """获取或创建全局客户端实例"""
    global _client
    if _client is None:
        _client = UnifiedAPIClient()
    return _client


def reset_client() -> None:
    """重置全局客户端"""
    global _client
    _client = None


def get_provider_list() -> List[Dict[str, Any]]:
    """获取服务商列表"""
    client = get_client()
    result = []
    for key, config in client.PROVIDERS.items():
        result.append({
            "id": key,
            "name": config["name"],
            "api_key_required": config["api_key_required"],
            "default_model": config["default_model"]
        })
    return result
