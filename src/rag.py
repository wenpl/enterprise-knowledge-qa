"""
RAG引擎模块
实现文档处理、向量化和检索功能
"""
import os
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_chroma import Chroma
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_core.documents import Document

import config


class RAGEngine:
    """RAG引擎类"""

    def __init__(self):
        """初始化RAG引擎"""
        self.embeddings = self._get_embeddings()
        self.vectorstore = None
        self._init_vectorstore()

    def _get_embeddings(self):
        """获取Embedding模型 - 使用智谱在线API"""
        return ZhipuAIEmbeddings(
            api_key=config.ZHIPU_API_KEY,
            model=config.ZHIPU_EMBEDDING_MODEL
        )

    def _init_vectorstore(self):
        """初始化向量数据库"""
        persist_dir = config.CHROMA_PERSIST_DIR

        if os.path.exists(persist_dir):
            # 加载已有向量库
            self.vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings,
                collection_name=config.CHROMA_COLLECTION_NAME
            )
        else:
            # 创建新的向量库
            os.makedirs(persist_dir, exist_ok=True)
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory=persist_dir,
                collection_name=config.CHROMA_COLLECTION_NAME
            )

    def load_document(self, file_path: str) -> List[Document]:
        """加载文档"""
        _, ext = os.path.splitext(file_path)

        if ext == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        return loader.load()

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """切分文档 - 按Markdown标题切分，保持语义完整性"""
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        all_chunks = []
        for doc in documents:
            # 按Markdown标题切分，每个标题下的内容作为独立块
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[("##", "chapter"), ("###", "section")],
                strip_headers=False
            )
            md_chunks = markdown_splitter.split_text(doc.page_content)

            # 对每个chunk检查是否需要进一步切分
            for chunk in md_chunks:
                chunk.metadata["source"] = doc.metadata.get("source", "未知")

                # 如果chunk过大，按段落进一步切分，但保持列表项完整
                content = chunk.page_content
                if len(content) > 800:
                    # 按双换行切分段落，保持列表项完整
                    paragraphs = []
                    current_para = []
                    lines = content.split('\n')
                    in_list = False

                    for line in lines:
                        # 检测列表项（以 - 或 * 或数字. 开头）
                        is_list_item = line.strip().startswith(('- ', '* ')) or (
                            len(line.strip()) > 0 and
                            line.strip()[0].isdigit() and
                            '. ' in line[:5]
                        )

                        if is_list_item:
                            in_list = True
                            current_para.append(line)
                        elif line.strip() == '' and in_list:
                            # 列表结束
                            in_list = False
                            current_para.append(line)
                        else:
                            current_para.append(line)

                        # 当段落足够大且不在列表中时，切分
                        if len('\n'.join(current_para)) > 600 and not in_list:
                            paragraphs.append('\n'.join(current_para))
                            current_para = []

                    if current_para:
                        paragraphs.append('\n'.join(current_para))

                    # 为每个段落创建新的chunk
                    for i, para in enumerate(paragraphs):
                        if para.strip():
                            new_chunk = Document(
                                page_content=para,
                                metadata={**chunk.metadata, "chunk_index": i}
                            )
                            all_chunks.append(new_chunk)
                else:
                    all_chunks.append(chunk)

        return all_chunks

    def add_document(self, file_path: str, doc_name: str = None) -> Dict[str, Any]:
        """添加文档到向量库"""
        if doc_name is None:
            doc_name = os.path.basename(file_path)

        # 加载文档
        documents = self.load_document(file_path)

        # 添加元数据
        for doc in documents:
            doc.metadata["source"] = doc_name

        # 切分文档
        chunks = self.split_documents(documents)

        # 添加到向量库
        self.vectorstore.add_documents(chunks)

        return {
            "status": "success",
            "document_name": doc_name,
            "chunks_count": len(chunks)
        }

    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """检索相关文档"""
        if top_k is None:
            top_k = config.TOP_K

        results = self.vectorstore.similarity_search_with_score(
            query,
            k=top_k
        )

        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "未知"),
                "score": round(1 / (1 + score), 2)  # 距离转相似度，范围0-1
            }
            for doc, score in results
        ]

    def get_document_count(self) -> int:
        """获取向量库中的文档数量"""
        return self.vectorstore._collection.count()

    def clear(self):
        """清空向量库"""
        self.vectorstore.delete_collection()
        self._init_vectorstore()


# 全局RAG引擎实例
_rag_engine = None


def get_rag_engine() -> RAGEngine:
    """获取RAG引擎实例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
