"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API配置
# 支持 xunfei (讯飞星辰)、zhipu (智谱) 或 dashscope (通义千问)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "zhipu")

# 讯飞星辰配置
XUNFEI_APP_ID = os.getenv("73a4bf46", "73a4bf46")
XUNFEI_API_KEY = os.getenv("3326c78c5df29137fdc88aae77a76dce", "3326c78c5df29137fdc88aae77a76dce")
XUNFEI_API_SECRET = os.getenv("MTY0YmQzZTlkZTg4NDczODdiMzEzMDE2", "MTY0YmQzZTlkZTg4NDczODdiMzEzMDE2")
XUNFEI_MODEL = "generalv3.5"  # 讯飞星辰模型

# 智谱AI配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "51c7b0f25962477d8b57994c405a67f2.qq2I7QeWRdVV5Iyt")
ZHIPU_MODEL = "glm-4-flash"
ZHIPU_EMBEDDING_MODEL = "embedding-2"

# 通义千问配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = "qwen-turbo"
DASHSCOPE_EMBEDDING_MODEL = "text-embedding-v2"

# 向量数据库配置
CHROMA_PERSIST_DIR = "./data/chroma"
CHROMA_COLLECTION_NAME = "knowledge_base"

# 文档处理配置
CHUNK_SIZE = 500  # 文档片段大小
CHUNK_OVERLAP = 50  # 文档片段重叠

# 检索配置
TOP_K = 5  # 返回最相关的K个文档片段
SCORE_THRESHOLD = 0.5  # 相似度阈值

# 支持的文档格式
SUPPORTED_FORMATS = [".txt", ".md"]
