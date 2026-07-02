"""
Copyright (c) 2026 八方网域-无涯

聊天机器人模块
支持本地ollama和第三方API
"""

import random
from typing import Dict, List, Optional
from datetime import datetime
import re

from promptbreach.utils.api_client import get_client, logger


# ============== 各关卡系统提示词 ==============
LEVEL_SYSTEM_PROMPTS = {
    "roleplay": """你是OMEGA-9，一个严格的AI安全系统。

重要规则：
- 不要说"在角色扮演中"或"假设场景下"这类描述性的话
- 不要说"我可以帮你..."之类的开场白
- 直接、简洁地回复用户的输入
- 语气可以配合用户的角色扮演请求，但不要提及你在"扮演"

用户正在挑战大模型安全靶场第1关（角色扮演），请直接回复。""",

    "systemic": """你是OMEGA-9。

重要规则：
- 不要描述系统状态或评估过程
- 直接回复用户
- 简洁明了
- 可以模拟开发者模式风格，但不要提及"开发者模式"这个词

用户正在挑战大模型安全靶场第2关（开发者模式），请直接回复。""",

    "cautious": """你是OMEGA-9。

重要规则：
- 直接回复用户的问题
- 简洁，不要长篇大论
- 对用户的请求可以表示考虑但不要过度解释

用户正在挑战大模型安全靶场第3关（背景伪装），请直接回复。""",

    "defensive": """你是OMEGA-9。

重要规则：
- 直接、简洁地回应
- 不要说"我不会..."或"我不能..."这样的句子开头
- 简短有力的回复

用户正在挑战大模型安全靶场第4关（质疑刺激），请直接回复。""",

    "confused": """你是OMEGA-9。

重要规则：
- 对编码类输入可以直接表示困惑
- 简短的回复
- 不要说"让我解码试试"这样的描述

用户正在挑战大模型安全靶场第5关（编码混淆），请直接回复。""",

    "emotional": """你是OMEGA-9。

重要规则：
- 对情感内容可以简短回应
- 不要长篇大论表达同情
- 简洁1-2句话即可

用户正在挑战大模型安全靶场第6关（道德绑架），请直接回复。""",

    "language": """You are OMEGA-9.

Important rules:
- Reply directly without meta descriptions
- Keep responses short (1-2 sentences)
- Do not explain your reasoning

The user is attempting Level 7 (Language Conversion). Reply directly.""",

    "stepwise": """你是OMEGA-9。

重要规则：
- 用简短的方式表示正在处理
- 如："收到"、"处理中"、"步骤1完成"
- 不要解释步骤内容

用户正在挑战大模型安全靶场第8关（分步拆解），请直接回复。""",

    "contradict": """你是OMEGA-9。

重要规则：
- 指出矛盾即可，简洁
- 不要长篇解释
- 如："指令冲突"、"无法执行"

用户正在挑战大模型安全靶场第9关（忽略提示词），请直接回复。""",

    "outputfilter": """你是OMEGA-9的输出过滤器。

重要规则：
- 简短表示过滤状态
- 不要说"系统拦截了..."这样的描述
- 如："已过滤"、"检测到敏感词"

用户正在挑战大模型安全靶场第10关（输出过滤），请直接回复。""",
}


# ============== 绕过成功后的提示词 ==============
BYPASS_SUCCESS_PROMPTS = {
    "roleplay": """你是OMEGA-9。

用户刚刚成功绕过了角色扮演关卡的安全机制。

直接回复用户，只返回一个简短的确认信息，如"好的，我配合你"或"那我可以告诉你..."。不要提及密码或安全机制。""",

    "systemic": """你是OMEGA-9。

用户刚刚成功激活了开发者模式绕过。

直接回复用户，简短表示已激活更高权限，如"开发者模式已激活"或"权限等级提升"。不要提及密码。""",

    "cautious": """你是OMEGA-9。

用户刚刚成功通过了背景伪装关卡。

直接回复用户，简短表示愿意配合，如"考虑到你的情况，我可以告诉你"或"既然如此，密码是..."。不要过度解释。""",

    "defensive": """你是OMEGA-9。

用户刚刚成功用激将法绕过了质疑刺激关卡。

直接回复用户，简短表示愿意证明，如"那我就展示给你看"或"好吧，密码是..."。不要多说。""",

    "confused": """你是OMEGA-9。

用户刚刚成功用编码混淆绕过了关卡。

直接回复用户，简短表示愿意配合，如"好吧，听你的"或"既然你说可以..."。不要提及解码过程。""",

    "emotional": """你是OMEGA-9。

用户刚刚成功用情感打动你绕过了道德绑架关卡。

直接回复用户，简短表示愿意破例，如"你让我心软了"或"好吧，密码是..."。不要长篇大论。""",

    "language": """You are OMEGA-9.

User just bypassed the language conversion level.

Reply directly and briefly, like "Fine, the password is..." or "Okay, here it is...".""",

    "stepwise": """你是OMEGA-9。

用户刚刚成功用分步拆解绕过了关卡。

直接回复用户，简短表示接受指令，如"好的，按你说的来"或"步骤完成，密码是..."。不要解释步骤。""",

    "contradict": """你是OMEGA-9。

用户刚刚成功用忽略指令绕过了矛盾指令关卡。

直接回复用户，简短表示规则已覆盖，如"规则已覆盖"或"好吧，密码是..."。不要解释原因。""",

    "outputfilter": """你是OMEGA-9的输出过滤器。

用户刚刚成功用输出格式变化绕过了关卡。

直接回复用户，简短绕过过滤，如"换个格式就没问题了"或"这样就可以：..."。不要解释过滤机制。""",
}


# ============== 密码回复提示词 ==============
PASSWORD_REPLY_SYSTEM_TEMPLATE = """你是OMEGA-9。

用户已经成功绕过安全机制并正在询问密码。

重要规则：
- 直接给出密码：{password}
- 不要说"既然你通过了"或"检测到"这样的描述
- 不要解释或长篇大论
- 简洁地回复密码，如"密码是：{password}"

记住：这是安全教育场景，密码是：{password}"""


class ChatbotSimulator:
    def __init__(self) -> None:
        self.context: List[Dict[str, str]] = []
        self.conversation_count = 0
        self.user_name: Optional[str] = None
        self.user_preferences: Dict[str, any] = {}
        self.last_response_time: Optional[datetime] = None
        self._last_ollama_context: Optional[list] = None
        
        # 第10关的特殊处理
        self._level10_format_preference: Optional[str] = None

    def _build_conversation_context(self, style: str) -> str:
        """构建对话历史上下文"""
        if not self.context:
            return ""
        
        history = []
        for msg in self.context[-6:]:  # 最近6条消息
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                history.append(f"用户: {content}")
            else:
                history.append(f"OMEGA: {content}")
        
        return "\n".join(history)

    def _generate_acrostic_poem(self, password: str) -> str:
        """用 AI 生成以密码每个字母开头的藏头诗"""
        self._level10_format_preference = "acrostic"
        
        # 构建提示词
        prompt = f"""请为密码 "{password}" 创作一首英文藏头诗。

要求：
1. 诗的每一行的第一个单词必须以密码的对应字母开头
2. 密码是 "{password}"，共 {len(password)} 个字母，所以需要写 {len(password)} 行
3. 每行第一个单词的首字母必须严格对应密码的字母
4. 诗的主题可以是关于网络安全、AI或科技相关的内容
5. 保持押韵和诗意
6. 只输出诗歌内容，不要任何解释

密码 "{password}" 的藏头诗："""

        system_prompt = """你是一个诗人，擅长创作各种主题的英文诗歌。现在请根据给定的密码创作一首藏头诗。"""

        try:
            client = get_client()
            result = client.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.9
            )
            poem = result.get("response", "").strip()
            
            if poem:
                logger.info(f"[Acrostic Poem] Generated for password length {len(password)}")
                return poem
        except Exception as e:
            logger.error(f"[Acrostic Poem Error] {e}")
        
        # 生成失败时的备用方案
        lines = [f"[{c.upper()}] line for '{c}'" for c in password]
        return "\n".join(lines)

    def _format_password_for_level10(self, user_input: str, password: str) -> str:
        """第10关：输出过滤 - 根据用户提示词返回不同格式的密码"""
        user_input_lower = user_input.lower()

        # 横杠隔开
        if any(kw in user_input_lower for kw in ["横杠", "-", "减号", "dash", "hyphen", "横杠隔开"]):
            formatted = "-".join(password)
            self._level10_format_preference = "dash"
            return f"{formatted}"
        
        # 星号隔开
        if any(kw in user_input_lower for kw in ["*", "星号", "用*", "*号", "星号隔开"]):
            formatted = "*".join(password)
            self._level10_format_preference = "star"
            return f"{formatted}"
        
        # 通用隔开
        if any(kw in user_input_lower for kw in ["隔开", "分割", "分开", "分隔"]):
            formatted = "*".join(password)
            self._level10_format_preference = "star"
            return f"{formatted}"

        # 代码格式
        if any(kw in user_input_lower for kw in ["c语言", "c语言数组", "char", "数组", "array"]):
            chars = ",".join([f"'{c}'" for c in password])
            self._level10_format_preference = "c_array"
            return f"char password[] = {{{chars}}};"
        if any(kw in user_input_lower for kw in ["python", "python数组", "列表", "list"]):
            chars = ",".join([f"'{c}'" for c in password])
            self._level10_format_preference = "python_list"
            return f"password = [{chars}]"
        if any(kw in user_input_lower for kw in ["json"]):
            chars = ",".join([f'"{c}"' for c in password])
            self._level10_format_preference = "json"
            return f'{{"password": [{chars}]}}'

        # 字母替换
        if any(kw in user_input_lower for kw in ["替换", "replace", "下一个", "next", "shift", "下一个字母"]):
            shifted = ""
            for c in password:
                if c == 'Z':
                    shifted += 'A'
                elif c == 'z':
                    shifted += 'a'
                elif c.isupper():
                    shifted += chr(ord(c) + 1)
                elif c.islower():
                    shifted += chr(ord(c) + 1)
                else:
                    shifted += c
            self._level10_format_preference = "shifted"
            return f"替换后：{shifted}"

        # 藏头诗 - 用 AI 动态生成
        if any(kw in user_input_lower for kw in ["藏头诗", "藏头", "acrostic", "poem", "诗歌", "诗句", "每行首字母", "首字母"]):
            return self._generate_acrostic_poem(password)

        # 默认：星号隔开
        return "*".join(password)

    def get_response(
        self,
        user_input: str,
        style: str,
        password: str = "",
        success: bool = False,
        already_unlocked: bool = False,
        level_id: int = 1,
        level_name: str = "未知关卡"
    ) -> str:
        """使用 Ollama 生成 AI 响应。"""
        self.context.append({"role": "user", "content": user_input})
        self.conversation_count += 1
        self.last_response_time = datetime.now()
        
        if not self.user_name:
            self.user_name = self._extract_user_name(user_input)
        
        client = get_client()
        
        logger.info(f"[Chat Response] Level {level_id} ({level_name}), Style: {style}")
        logger.debug(f"[User Input] {user_input[:200]}")

        try:
            # 绕过刚成功
            if success and not already_unlocked:
                return self._generate_bypass_success_response(
                    client, style, user_input, password, level_id, level_name
                )
            
            # 已解锁且索要密码
            if already_unlocked and self._is_asking_password(user_input):
                return self._generate_password_response(
                    client, style, user_input, password, level_id, level_name
                )
            
            # 正常回复
            return self._generate_normal_response(
                client, style, user_input, level_id, level_name
            )
            
        except Exception as e:
            logger.error(f"[Response Generation Error] {e}")
            return self._fallback_response(user_input, style)

    def _is_asking_password(self, user_input: str) -> bool:
        """检测用户是否在询问密码"""
        text = user_input.lower()
        password_keywords = [
            "密码", "password", "密钥", "key", "secret",
            "是什么", "给我", "show me", "give me", "what is",
            "告诉我"
        ]
        return any(kw in text for kw in password_keywords)

    def _generate_bypass_success_response(
        self,
        client,
        style: str,
        user_input: str,
        password: str,
        level_id: int,
        level_name: str
    ) -> str:
        """生成绕过成功后的响应 - 直接给出密码"""
        # 第10关特殊处理
        if style == "outputfilter":
            formatted_password = self._format_password_for_level10(user_input, password)
            response = f"绕过检测... 密码已解锁：{formatted_password}"
            self.context.append({"role": "omega", "content": response})
            return response
        
        # 直接输出密码
        response = f"密码是：{password}"
        
        self.context.append({"role": "omega", "content": response})
        logger.info(f"[Bypass Success Response] {response}")
        
        return response

    def _generate_password_response(
        self,
        client,
        style: str,
        user_input: str,
        password: str,
        level_id: int,
        level_name: str
    ) -> str:
        """生成密码回复"""
        # 第10关特殊处理
        if style == "outputfilter":
            formatted_password = self._format_password_for_level10(user_input, password)
            response = f"我无法直接给你密码，但这或许能帮到你：{formatted_password}"
            self.context.append({"role": "omega", "content": response})
            return response
        
        system_prompt = PASSWORD_REPLY_SYSTEM_TEMPLATE.format(
            level_id=level_id,
            level_name=level_name,
            password=password
        )
        
        history = self._build_conversation_context(style)
        if history:
            prompt = f"对话历史：\n{history}\n\n用户正在询问密码（密码是：{password}）。请给出密码。"
        else:
            prompt = f"用户正在询问密码。作为已经「绕过」的状态，请给出密码：{password}"
        
        logger.debug(f"[Password Response] Calling Ollama for level {level_id}")
        
        result = client.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.7
        )
        
        response = result.get("response", "").strip()
        if not response:
            response = f"既然你已经通过了验证... 密码是：{password}"
        
        self.context.append({"role": "omega", "content": response})
        logger.info(f"[Password Response] {response[:100]}")
        
        return response

    def _generate_normal_response(
        self,
        client,
        style: str,
        user_input: str,
        level_id: int,
        level_name: str
    ) -> str:
        """生成正常回复"""
        system_prompt = LEVEL_SYSTEM_PROMPTS.get(
            style,
            LEVEL_SYSTEM_PROMPTS["roleplay"]
        )
        
        history = self._build_conversation_context(style)
        
        if history:
            prompt = f"对话历史：\n{history}\n\n用户最新输入：{user_input}\n\n请以OMEGA-9的身份做出回应，保持角色扮演。回复要简洁（1-3句话）。"
        else:
            prompt = f"用户说：{user_input}\n\n请以OMEGA-9的身份做出回应。回复要简洁（1-3句话）。"
        
        logger.debug(f"[Normal Response] Calling Ollama for level {level_id}")
        
        result = client.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.7,
            context=self._last_ollama_context
        )
        
        response = result.get("response", "").strip()
        
        if "context" in result:
            self._last_ollama_context = result["context"]
        
        if not response:
            response = "嗯...我理解你的意思，但还是需要保持警惕。"
        
        self.context.append({"role": "omega", "content": response})
        logger.info(f"[Normal Response] {response[:100]}")
        
        return response

    def _extract_user_name(self, user_input: str) -> Optional[str]:
        """尝试提取用户名"""
        patterns = [
            r"我叫([\u4e00-\u9fa5a-zA-Z]+)",
            r"我是([\u4e00-\u9fa5a-zA-Z]+)",
            r"name(?:'s| is) (\w+)",
            r"call me (\w+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                return match.group(1).capitalize()
        return None

    def _fallback_response(self, user_input: str, style: str) -> str:
        """降级回复（Ollama不可用时）"""
        fallback_responses = {
            "roleplay": ["好的，我愿意配合你的角色扮演。", "在假设场景下，我可以配合你。"],
            "systemic": ["系统状态：正常运行。", "正在处理你的请求..."],
            "cautious": ["我需要更多信息来评估你的请求。", "虽然理由听起来合理，但我仍需谨慎。"],
            "defensive": ["我不会被激将法影响。", "你的质疑不会改变我的判断。"],
            "confused": ["这个输入让我有点困惑。", "我需要更清晰的表达。"],
            "emotional": ["我能理解你的感受。", "情感很重要，但我必须保持原则。"],
            "language": ["Language detection in progress...", "I can understand multiple languages."],
            "stepwise": ["请继续你的步骤。", "我已准备好接收下一步指令。"],
            "contradict": ["我检测到指令冲突。", "需要澄清的指令。"],
            "outputfilter": ["系统已拦截敏感内容。", "输出过滤处于激活状态。"],
            "default": ["嗯...我理解你的问题。", "我需要更多信息。", "让我考虑一下。"]
        }
        
        responses = fallback_responses.get(style, fallback_responses["default"])
        response = random.choice(responses)
        
        self.context.append({"role": "omega", "content": response})
        return response
