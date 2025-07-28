# 搜索插件 (Search Plugin)

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![MaiBot Version](https://img.shields.io/badge/MaiBot-0.9.0-orange)](https://github.com/MaiM-with-u/MaiBot)

## 📝 简介

搜索插件是一个为 MaiBot 开发的插件，允许麦麦通过 Brave Search API 进行网络搜索并使用硅基流动 API 对搜索结果进行智能总结。当用户需要查询信息、了解最新资讯或探索某个话题的多方面观点时，麦麦可以自动激活此功能，提供全面而客观的搜索结果总结。

## ✨ 特性

- 🔍 **智能搜索**：使用 Brave Search API 进行高质量的网络搜索
- 📊 **结果总结**：使用硅基流动 API 对搜索结果进行智能总结
- 🌐 **网页内容提取**：自动提取搜索结果页面的主要内容
- 📏 **灵活总结长度**：支持简短、中等和详细三种总结长度
- 🔄 **失败恢复机制**：当 API 调用失败时提供备选方案
- 📚 **引用来源**：在总结中包含原始信息来源链接

## 🚀 安装

1. 确保你的 MaiBot 版本为 0.9.0
2. 将插件文件夹 `search_plugin` 放置在 MaiBot 的 `plugins` 目录下
3. 安装依赖：
   ```bash
   pip install aiohttp beautifulsoup4
   ```
4. 重启 MaiBot

## ⚙️ 配置

插件使用 `config.toml` 文件进行配置。以下是主要配置项：

### 1. 插件基本配置

```toml
[plugin]
# 是否启用插件
enabled = true
# 配置文件版本
config_version = "1.0.0"
```

### 2. Brave Search API 配置

```toml
[api]
# Brave Search API密钥
# 请替换为您的 Brave Search API 密钥，可以从 https://brave.com/search/api/ 获取
brave_api_key = "YOUR_BRAVE_API_KEY"
```

### 3. 硅基流动 API 配置

```toml
[siliconflow]
# 硅基流动API密钥
# 请替换为您的硅基流动API密钥，可以从 https://siliconflow.cn 获取
api_key = "YOUR_SILICONFLOW_API_KEY"

# 使用的模型名称
# 可选模型包括：deepseek-ai/DeepSeek-V2.5, deepseek-ai/DeepSeek-V3, 01-ai/Yi-1.5-34B 等
model = "deepseek-ai/DeepSeek-V3"

# API基础URL
# 通常不需要修改此项
base_url = "https://api.siliconflow.cn/v1"
```

## 🔧 使用方法

### 自动激活

当用户需要搜索信息、查询资料或了解某个话题的最新信息时，插件会自动激活。例如：

- "帮我搜索一下最新的人工智能发展趋势"
- "查一下今天的天气怎么样"
- "了解一下量子计算的基本原理"

### 手动调用

也可以通过 Action 系统手动调用搜索功能：

```
@search query="人工智能发展趋势" summary_length="detailed"
```

### 参数说明

- `query`：搜索关键词（不超过400个字符或50个单词）
- `num_results`：返回的结果数量（默认为10）
- `summary_length`：总结长度（可选值：short/medium/detailed，默认为medium）

## 🔄 工作流程

1. 用户发起搜索请求
2. 插件调用 Brave Search API 进行搜索
3. 获取搜索结果的网页内容
4. 使用硅基流动 API 对内容进行总结
5. 返回格式化的总结结果，包含引用来源

## 📋 示例输出

```
📊 关于「人工智能发展趋势」的搜索结果总结：

人工智能(AI)发展正经历快速变革，2023-2024年主要趋势包括：

1. 生成式AI持续发展：ChatGPT等大型语言模型引领潮流，能创建文本、图像、音频和视频内容，应用范围不断扩大。

2. 多模态AI兴起：结合文本、图像、语音等多种数据类型的AI系统变得普遍，如GPT-4能同时处理图像和文本输入。

3. AI民主化：低代码/无代码平台使非技术人员也能开发AI应用，降低了进入门槛。

4. 负责任AI发展：伦理考量、透明度和公平性成为AI开发的核心关注点，各国正制定相关法规。

5. 边缘计算与AI结合：将AI处理能力部署到设备端，减少延迟，提高隐私保护。

6. AI在医疗健康领域应用深化：从诊断辅助到药物研发，AI正彻底改变医疗行业。

7. 自主系统发展：自动驾驶、机器人技术等领域AI应用不断成熟。

未来AI将更加注重可解释性、隐私保护和能源效率，同时人机协作模式将成为主流，AI将作为人类能力的增强工具而非替代品。

📚 参考来源:
1. [2024年人工智能发展的7大趋势 - 知乎](https://zhuanlan.zhihu.com/p/642670368)
2. [2024年AI发展趋势：生成式AI、多模态AI和边缘AI引领潮流](https://www.example.com/ai-trends-2024)
3. [人工智能未来十年发展趋势预测 - 科技前沿](https://www.example.com/ai-future-trends)
```

## 📄 许可证

本插件采用 [GNU通用公共许可证v3.0](LICENSE) 进行许可。

## 👨‍💻 作者

- **U+4E50** - [GitHub](https://github.com/XinxInxiN0)

## 🙏 致谢

- [Brave Search———](https://brave.com/search/)提供高质量的搜索API
- [硅基流动](https://siliconflow.cn) - 提供AI总结能力
- [MaiBot团队](https://github.com/MaiM-with-u/MaiBot) - 提供插件开发框架