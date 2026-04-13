# 企业知识库智能问答助手

一个基于RAG技术的企业知识库问答系统，支持上传文档并进行智能问答。

## 功能特点

- 📄 支持TXT、Markdown格式文档
- 🔍 基于向量检索的语义搜索
- 💬 自然语言问答交互
- 📖 答案来源追溯
- 🎯 简洁易用的Web界面

## 技术栈

- **前端**: Streamlit
- **RAG框架**: LangChain
- **LLM**: 智谱GLM-4 / 通义千问
- **向量数据库**: Chroma

## 快速开始

### 1. 安装依赖

```bash
cd ai_pm_project
pip install -r requirements.txt
```

### 2. 配置API Key

创建 `.env` 文件：

```env
# 使用智谱AI
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=your_zhipu_api_key

# 或使用通义千问
# LLM_PROVIDER=dashscope
# DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 3. 启动应用

```bash
streamlit run src/app.py
```

### 4. 使用步骤

1. 在左侧上传文档（TXT或Markdown格式）
2. 点击"添加到知识库"
3. 在右侧输入问题进行问答

## 项目结构

```
ai_pm_project/
├── docs/                      # 产品文档
│   ├── PRD.md                 # 产品需求文档
│   ├── 技术方案.md            # 技术架构设计
│   ├── Prompt设计.md          # Prompt设计文档
│   └── 评估体系.md            # 效果评估体系
├── data/                      # 数据文件
│   ├── documents/             # 示例文档
│   └── test_cases/            # 测试用例
├── src/                       # 源代码
│   ├── app.py                 # 主应用
│   ├── rag.py                 # RAG引擎
│   └── config.py              # 配置文件
├── tests/                     # 测试
└── README.md                  # 项目说明
```

## API Key获取

### 智谱AI
1. 访问 https://open.bigmodel.cn/
2. 注册账号并登录
3. 在控制台获取API Key

### 通义千问
1. 访问 https://dashscope.aliyun.com/
2. 注册账号并登录
3. 开通服务并获取API Key

## 成本估算

- 智谱GLM-4-flash: 约0.001元/千token
- Embedding: 约0.0005元/千token
- 月均成本: 约50元（中等使用量）

## 作者

[你的名字] - AI产品经理面试项目
