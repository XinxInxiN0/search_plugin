import asyncio
import re
from typing import List, Tuple, Type
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup

from src.plugin_system import BasePlugin, register_plugin, ComponentInfo, ConfigField, ActionActivationType, ChatMode


# ===== 插件注册 =====

@register_plugin
class BraveSearchPlugin(BasePlugin):
    """Brave搜索插件 - 使用Brave API进行搜索并总结结果"""

    # 插件基本信息（必须填写）
    plugin_name = "search_plugin" # 内部标识符
    plugin_description = "使用Brave Search API进行搜索并总结结果的插件"
    plugin_version = "1.0.0"
    plugin_author = "U+4E50"
    enable_plugin = True  # 启用插件
    dependencies: list[str] = []  # 插件依赖列表
    python_dependencies: list[str] = ["aiohttp", "beautifulsoup4"]  # Python包依赖列表
    config_file_name: str = "config.toml"
    from src.plugin_system import BaseAction
    from typing import Tuple

    class SearchAction(BaseAction):
        """搜索Action - 使用Brave API搜索并总结结果"""

        # === 激活控制 ===
        focus_activation_type = ActionActivationType.LLM_JUDGE
        normal_activation_type = ActionActivationType.LLM_JUDGE
        mode_enable = ChatMode.ALL
        parallel_action = True

        # LLM判断提示词
        llm_judge_prompt = "当用户需要搜索信息、查询资料、了解某个话题的最新信息时激活"

        # === 基本信息 ===
        action_name = "search"
        action_description = "使用Brave搜索引擎查询信息并总结结果"

        # === 功能定义 ===
        action_parameters = {
            "query": "搜索关键词（不超过400个字符或50个单词）",
            "num_results": "返回的结果数量（默认为10）",
            "summary_length": "总结长度（简短/中等/详细，默认为中等）"
        }

        action_require = [
            "用户需要搜索网络信息时使用",
            "需要查询最新资讯或事实信息时使用",
            "用户想了解某个话题的多方面观点时使用"
        ]

        associated_types = ["text"]

        async def execute(self) -> Tuple[bool, str]:
            """执行搜索Action"""
            try:
                # 获取API密钥
                api_key = self.get_config("api.brave_api_key", "")
                if api_key == "" or api_key == "YOUR_BRAVE_API_KEY":
                    await self.send_text("❌ Brave Search API密钥未配置，请在配置文件中设置有效的API密钥。")
                    return False, "Brave Search API密钥未配置，请在配置文件中设置。"

                # 获取Action参数
                query = self.action_data.get("query", "")
                if not query:
                    await self.send_text("❌ 搜索关键词不能为空")
                    return False, "搜索关键词不能为空"
                
                num_results = "10"
                summary_length = self.action_data.get("summary_length", "medium")
                
                # 发送正在搜索的提示
                await self.send_text(f"🔍 正在搜索: {query}")
                
                # 调用Brave API进行搜索
                await self.send_text("📡 正在调用搜索API...")
                search_results = await asyncio.wait_for(
                    self._search_brave(api_key, query, num_results), 
                    timeout=30.0
                )
                
                if not search_results:
                    await self.send_text("❌ 未找到相关搜索结果")
                    return False, "未找到相关搜索结果"
                
                await self.send_text(f"✅ 找到 {len(search_results)} 个搜索结果，正在获取详细内容...")
                
                # 获取网页内容
                content_results = await asyncio.wait_for(
                    self._fetch_page_contents(search_results), 
                    timeout=60.0
                )
                
                await self.send_text("🤖 正在生成总结...")
                
                # 生成总结
                summary = await asyncio.wait_for(
                    self._generate_summary(query, content_results, summary_length), 
                    timeout=120.0
                )
                
                # 发送总结结果
                await self.send_text(f"📊 关于「{query}」的搜索结果总结：\n\n{summary}")
                
                # 记录动作信息
                await self.store_action_info(
                    action_build_into_prompt=True,
                    action_prompt_display=f"搜索了「{query}」并总结了结果",
                    action_done=True
                )
                
                return True, f"成功搜索并总结了「{query}」的结果"
                
            except asyncio.TimeoutError:
                await self.send_text("⏰ 搜索超时，请稍后重试")
                return False, "搜索操作超时"
            except Exception as e:
                error_msg = str(e)
                await self.send_text(f"❌ 搜索失败: {error_msg}")
                if "API请求失败" in error_msg or "401" in error_msg or "403" in error_msg:
                    return False, f"API密钥可能无效，请检查配置文件中的brave_api_key设置。错误详情：{error_msg}"
                return False, f"搜索执行失败：{error_msg}"
                
        async def _search_brave(self, api_key: str, query: str, num_results: int) -> list:
            """调用Brave Search API进行搜索"""
            try:
                encoded_query = quote(query)
                url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}&count={num_results}"
                
                timeout = aiohttp.ClientTimeout(total=20)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": api_key
                    }
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 401:
                            raise Exception("API密钥无效或已过期")
                        elif response.status == 403:
                            raise Exception("API访问被拒绝，请检查密钥权限")
                        elif response.status == 429:
                            raise Exception("API请求频率超限，请稍后重试")
                        elif response.status != 200:
                            response_text = await response.text()
                            raise Exception(f"API请求失败，状态码: {response.status}, 响应: {response_text[:200]}")
                        
                        data = await response.json()
                        
                        # 提取搜索结果
                        results = []
                        if "web" in data and "results" in data["web"]:
                            for result in data["web"]["results"]:
                                if "url" in result and "title" in result:
                                    results.append({
                                        "url": result["url"],
                                        "title": result["title"],
                                        "description": result.get("description", "")
                                    })
                        
                        return results
                        
            except aiohttp.ClientError as e:
                raise Exception(f"网络连接错误: {str(e)}")
            except asyncio.TimeoutError:
                raise Exception("API请求超时，请检查网络连接")
            except Exception as e:
                if "API" in str(e):
                    raise e
                raise Exception(f"搜索API调用失败: {str(e)}")
        
        async def _fetch_page_contents(self, search_results: list) -> list:
            """获取搜索结果页面的内容"""
            content_results = []
            
            # 限制并发数量，避免过多请求
            semaphore = asyncio.Semaphore(3)
            
            async def fetch_single_page(result):
                async with semaphore:
                    try:
                        url = result["url"]
                        timeout = aiohttp.ClientTimeout(total=8)
                        
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                            
                            async with session.get(url, headers=headers) as response:
                                if response.status == 200:
                                    # 限制响应大小，避免下载过大文件
                                    content = await response.read()
                                    if len(content) > 10240 * 10240:  # 10MB限制
                                        raise Exception("页面内容过大")
                                    
                                    html = content.decode('utf-8', errors='ignore')
                                    
                                    # 使用BeautifulSoup解析HTML
                                    soup = BeautifulSoup(html, "html.parser")
                                    
                                    # 移除脚本和样式元素
                                    for script in soup(["script", "style", "nav", "footer", "header"]):
                                        script.extract()
                                    
                                    # 获取文本内容
                                    text = soup.get_text(separator=' ', strip=True)
                                    
                                    # 清理文本（移除多余空格、换行等）
                                    text = re.sub(r'\s+', ' ', text).strip()
                                    
                                    # 截取合理长度的内容（前1500个字符）
                                    text = text[:3000]
                                    
                                    if len(text) > 100:  # 只保留有足够内容的页面
                                        return {
                                            "url": url,
                                            "title": result["title"],
                                            "content": text
                                        }
                                
                                # 如果状态码不是200或内容太少，使用描述
                                return {
                                    "url": url,
                                    "title": result["title"],
                                    "content": result.get("description", "无法获取页面内容")
                                }
                                
                    except Exception as e:
                        # 如果获取内容失败，添加原始描述
                        return {
                            "url": result["url"],
                            "title": result["title"],
                            "content": result.get("description", f"获取失败: {str(e)[:50]}")
                        }
            
            # 并发获取所有页面内容
            try:
                tasks = [fetch_single_page(result) for result in search_results]
                content_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 过滤掉异常结果
                valid_results = []
                for result in content_results:
                    if isinstance(result, dict):
                        valid_results.append(result)
                    elif isinstance(result, Exception):
                        # 记录异常但继续处理其他结果
                        continue
                
                return valid_results if valid_results else [{
                    "url": "fallback",
                    "title": "搜索结果",
                    "content": "无法获取详细内容，请直接查看搜索结果"
                }]
                
            except Exception as e:
                # 如果并发获取失败，返回基本信息
                return [{
                    "url": result["url"],
                    "title": result["title"],
                    "content": result.get("description", "内容获取失败")
                } for result in search_results]
                
        async def _call_siliconflow_api(self, prompt: str, max_tokens: int = 800, temperature: float = 0.7) -> str:
            """调用硅基流动API生成内容
            
            Args:
                prompt: 提示词
                max_tokens: 最大生成长度
                temperature: 温度参数，控制生成的随机性
                
            Returns:
                生成的内容
            """
            try:
                # 获取API配置
                api_key = self.get_config("siliconflow.api_key", "")
                model = self.get_config("siliconflow.model", "deepseek-ai/DeepSeek-V2.5")
                base_url = self.get_config("siliconflow.base_url", "https://api.siliconflow.cn/v1")
                
                # 检查API密钥
                if not api_key or api_key == "YOUR_SILICONFLOW_API_KEY":
                    raise Exception("硅基流动API密钥未配置，请在配置文件中设置有效的API密钥")
                
                # 构建请求URL和请求体
                url = f"{base_url}/chat/completions"
                
                # 构建请求体，使用OpenAI格式
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的搜索助手，负责总结网络搜索结果。请提供客观、全面的总结。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # 设置请求头
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                # 发送请求
                timeout = aiohttp.ClientTimeout(total=60)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        # 处理响应
                        if response.status == 200:
                            response_json = await response.json()
                            
                            # 提取生成的内容
                            if "choices" in response_json and len(response_json["choices"]) > 0:
                                content = response_json["choices"][0].get("message", {}).get("content", "")
                                if content:
                                    return content
                                else:
                                    raise Exception("API返回的内容为空")
                            else:
                                raise Exception("API返回格式不正确，未找到生成内容")
                        
                        elif response.status == 401:
                            raise Exception("API密钥无效或已过期")
                        elif response.status == 403:
                            raise Exception("API访问被拒绝，请检查密钥权限")
                        elif response.status == 429:
                            raise Exception("API请求频率超限，请稍后重试")
                        else:
                            response_text = await response.text()
                            raise Exception(f"API请求失败，状态码: {response.status}, 响应: {response_text[:200]}")
                            
            except aiohttp.ClientError as e:
                raise Exception(f"网络连接错误: {str(e)}")
            except asyncio.TimeoutError:
                raise Exception("API请求超时，请检查网络连接")
            except Exception as e:
                # 重新抛出异常，保留原始错误信息
                raise Exception(f"调用硅基流动API失败: {str(e)}")
        
        async def _generate_summary(self, query: str, content_results: list, summary_length: str) -> str:
            """生成搜索结果的总结"""
            try:
                if not content_results:
                    return f"关于「{query}」的搜索未找到有效内容。"
                
                # 构建提示词，限制长度避免token过多
                prompt = f"以下是关于「{query}」的搜索结果，请总结主要信息：\n\n"
                
                for i, result in enumerate(content_results[:5], 1):  # 最多使用5个结果
                    prompt += f"来源 {i}: {result['title']}\n"
                    # 限制每个内容的长度
                    content_preview = result['content'][:400] if result['content'] else "无内容"
                    prompt += f"内容: {content_preview}...\n\n"
                
                length_instruction = ""
                if summary_length == "short":
                    length_instruction = "请提供简短总结（200字以内）"
                elif summary_length == "medium":
                    length_instruction = "请提供中等长度总结（500字左右）"
                elif summary_length == "detailed":
                    length_instruction = "请提供详细总结（800字以上）"
                
                prompt += f"{length_instruction}，确保总结客观、全面，包含不同来源的关键信息。如果信息不足，请说明。"
                
                # 使用硅基流动API生成总结，添加fallback机制
                try:
                    # 调用硅基流动API生成总结
                    summary = await self._call_siliconflow_api(
                        prompt=prompt,
                        temperature=0.7,
                        max_tokens=800
                    )
                    
                    # 验证生成的内容
                    if not summary or len(summary.strip()) < 10:
                        raise Exception("生成的总结内容为空或过短")
                        
                except Exception as llm_error:
                    # LLM生成失败时的fallback
                    summary = f"关于「{query}」的搜索结果总结：\n\n"
                    for i, result in enumerate(content_results[:3], 1):
                        summary += f"{i}. {result['title']}\n"
                        content_preview = result['content'][:200] if result['content'] else result.get('description', '无内容')
                        summary += f"   {content_preview}...\n\n"
                    
                    summary += f"注意：由于硅基流动AI总结服务暂时不可用（{str(llm_error)[:50]}），以上为原始搜索结果摘要。"
                
                # 添加引用来源
                summary += "\n\n📚 参考来源:\n"
                for i, result in enumerate(content_results[:5], 1):
                    summary += f"{i}. [{result['title']}]({result['url']})\n"
                
                return summary
                
            except Exception as e:
                # 完全失败时的最后fallback
                fallback_summary = f"关于「{query}」的搜索遇到问题：{str(e)[:100]}\n\n"
                if content_results:
                    fallback_summary += "找到的相关链接：\n"
                    for i, result in enumerate(content_results[:3], 1):
                        fallback_summary += f"{i}. [{result['title']}]({result['url']})\n"
                else:
                    fallback_summary += "未能获取到有效的搜索结果。"
                
                return fallback_summary
    # 配置节描述
    config_section_descriptions = {
        "plugin": "插件启用配置",
        "api": "API相关配置",
        "siliconflow": "硅基流动AI配置",
    }

    # 配置Schema定义
    config_schema: dict = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="1.0.0", description="配置文件版本"),
        },
        "api": {
            "brave_api_key": ConfigField(type=str, default="YOUR_BRAVE_API_KEY", description="Brave Search API密钥"),
        },
        "siliconflow": {
            "api_key": ConfigField(type=str, default="YOUR_SILICONFLOW_API_KEY", description="硅基流动API密钥"),
            "model": ConfigField(type=str, default="deepseek-ai/DeepSeek-V3", description="使用的模型名称"),
            "base_url": ConfigField(type=str, default="https://api.siliconflow.cn/v1", description="API基础URL（可替换为其他openai格式的api）"),
        }
    }
    
    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """返回插件包含的组件列表"""
        return [
            (self.SearchAction.get_action_info(), self.SearchAction)
        ]