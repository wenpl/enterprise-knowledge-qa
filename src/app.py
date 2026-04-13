"""
企业知识库智能问答助手
主应用文件
"""
import streamlit as st
import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag import get_rag_engine
import config

# 页面配置
st.set_page_config(
    page_title="企业知识库问答助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .source-box {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "documents" not in st.session_state:
        st.session_state.documents = []


def get_llm_response(question: str, context: str) -> str:
    """调用LLM生成答案"""
    import config

    if config.LLM_PROVIDER == "xunfei":
        return _call_xunfei(question, context)
    elif config.LLM_PROVIDER == "zhipu":
        return _call_zhipu(question, context)
    else:
        return _call_dashscope(question, context)


def _call_xunfei(question: str, context: str) -> str:
    """调用讯飞星辰API"""
    import websocket
    import json
    import hmac
    import hashlib
    import base64
    from datetime import datetime
    import ssl
    import config

    system_prompt = """你是一个企业知识库问答助手。你的任务是基于提供的文档内容回答用户问题。

## 回答规范

1. 只基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户"文档中未找到相关信息"
3. 回答要简洁明了，直接回答问题
4. **只引用与问题直接相关的来源**，不要强行关联不相关的内容
5. 来源标注格式：【来源】文档章节名称

## 特殊问题处理

### 区间匹配问题（如年假、工龄等）
当用户询问"入职X年，年假多少天"这类问题时：
- 必须完整列出文档中所有年假档位
- 根据用户的年限匹配正确的档位（如入职15年，匹配"满10年"的档位，而非"满5年"）
- 完整展示规则，让用户理解匹配逻辑

示例：
问：入职15年，年假多少天？
答：根据员工手册年假规定：
- 入职满1年，享有5天年假
- 入职满5年，享有10天年假
- 入职满10年，享有15天年假

您入职15年，满足"满10年"的条件，享有15天年假。

## 回答格式

【答案】
[你的答案内容，直接回答问题]

【来源】
[只列出与答案直接相关的文档章节]

## 限制条件

- 不要回答与文档无关的问题
- 不要编造文档中不存在的内容
- 不要把不相关的内容强行关联"""

    user_prompt = f"""## 文档内容
{context}

## 用户问题
{question}

请基于以上文档内容回答用户问题。如果文档中没有相关信息，请明确告知。"""

    # 讯飞星辰API地址
    url = "wss://spark-api.xf-yun.com/v3.5/chat"
    now = datetime.now()
    date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

    # 生成鉴权
    signature_origin = f"host: spark-api.xf-yun.com\ndate: {date}\nGET /v3.5/chat HTTP/1.1"
    signature_sha = hmac.new(
        config.XUNFEI_API_SECRET.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = f'api_key="{config.XUNFEI_API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    auth_url = f"{url}?authorization={authorization}&date={date}&host=spark-api.xf-yun.com"

    # 构建请求
    data = {
        "header": {
            "app_id": config.XUNFEI_APP_ID,
            "uid": "user"
        },
        "parameter": {
            "chat": {
                "domain": config.XUNFEI_MODEL,
                "temperature": 0.7,
                "max_tokens": 1000
            }
        },
        "payload": {
            "message": {
                "text": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
        }
    }

    result = []

    def on_message(ws, message):
        data = json.loads(message)
        code = data.get('header', {}).get('code', 0)
        if code != 0:
            result.append(f"错误: {data}")
            ws.close()
            return
        content = data.get('payload', {}).get('choices', {}).get('text', [{}])[0].get('content', '')
        result.append(content)
        if data.get('header', {}).get('status') == 2:
            ws.close()

    def on_error(ws, error):
        result.append(f"错误: {error}")

    def on_close(ws, close_status_code, close_msg):
        pass

    def on_open(ws):
        ws.send(json.dumps(data))

    ws = websocket.WebSocketApp(
        auth_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    return ''.join(result)


def _call_zhipu(question: str, context: str) -> str:
    """调用智谱API"""
    from zhipuai import ZhipuAI
    import config

    client = ZhipuAI(api_key=config.ZHIPU_API_KEY)

    system_prompt = """你是一个企业知识库问答助手。你的任务是基于提供的文档内容回答用户问题。

## 回答规范

1. 只基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户"文档中未找到相关信息"
3. 回答要简洁明了，直接回答问题
4. **只引用与问题直接相关的来源**，不要强行关联不相关的内容
5. 来源标注格式：【来源】文档章节名称

## 特殊问题处理

### 区间匹配问题（如年假、工龄等）
当用户询问"入职X年，年假多少天"这类问题时：
- 必须完整列出文档中所有年假档位
- 根据用户的年限匹配正确的档位（如入职15年，匹配"满10年"的档位，而非"满5年"）
- 完整展示规则，让用户理解匹配逻辑

示例：
问：入职15年，年假多少天？
答：根据员工手册年假规定：
- 入职满1年，享有5天年假
- 入职满5年，享有10天年假
- 入职满10年，享有15天年假

您入职15年，满足"满10年"的条件，享有15天年假。

## 回答格式

【答案】
[你的答案内容，直接回答问题]

【来源】
[只列出与答案直接相关的文档章节]

## 限制条件

- 不要回答与文档无关的问题
- 不要编造文档中不存在的内容
- 不要把不相关的内容强行关联"""

    user_prompt = f"""## 文档内容
{context}

## 用户问题
{question}

请基于以上文档内容回答用户问题。如果文档中没有相关信息，请明确告知。"""

    response = client.chat.completions.create(
        model=config.ZHIPU_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content


def _call_dashscope(question: str, context: str) -> str:
    """调用通义千问API"""
    import dashscope
    from dashscope import Generation
    import config

    dashscope.api_key = config.DASHSCOPE_API_KEY

    system_prompt = """你是一个企业知识库问答助手。你的任务是基于提供的文档内容回答用户问题。

## 回答规范

1. 只基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户"文档中未找到相关信息"
3. 回答要简洁明了，直接回答问题
4. **只引用与问题直接相关的来源**，不要强行关联不相关的内容
5. 来源标注格式：【来源】文档章节名称

## 特殊问题处理

### 区间匹配问题（如年假、工龄等）
当用户询问"入职X年，年假多少天"这类问题时：
- 必须完整列出文档中所有年假档位
- 根据用户的年限匹配正确的档位（如入职15年，匹配"满10年"的档位，而非"满5年"）
- 完整展示规则，让用户理解匹配逻辑

示例：
问：入职15年，年假多少天？
答：根据员工手册年假规定：
- 入职满1年，享有5天年假
- 入职满5年，享有10天年假
- 入职满10年，享有15天年假

您入职15年，满足"满10年"的条件，享有15天年假。

## 回答格式

【答案】
[你的答案内容，直接回答问题]

【来源】
[只列出与答案直接相关的文档章节]

## 限制条件

- 不要回答与文档无关的问题
- 不要编造文档中不存在的内容
- 不要把不相关的内容强行关联"""

    user_prompt = f"""## 文档内容
{context}

## 用户问题
{question}

请基于以上文档内容回答用户问题。如果文档中没有相关信息，请明确告知。"""

    response = Generation.call(
        model=config.DASHSCOPE_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    return response.output.choices[0].message.content


def main():
    """主函数"""
    init_session_state()

    # 标题
    st.title("📚 企业知识库智能问答助手")
    st.markdown("---")

    # 侧边栏 - 文档管理
    with st.sidebar:
        st.header("📁 文档管理")

        # 文档上传
        uploaded_file = st.file_uploader(
            "上传文档",
            type=["txt", "md"],
            help="支持 TXT、Markdown 格式"
        )

        if uploaded_file is not None:
            if st.button("添加到知识库"):
                with st.spinner("处理文档中..."):
                    try:
                        # 保存临时文件
                        temp_path = os.path.join("./data/documents", uploaded_file.name)
                        os.makedirs("./data/documents", exist_ok=True)

                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # 添加到向量库
                        rag = get_rag_engine()
                        result = rag.add_document(temp_path, uploaded_file.name)

                        st.success(f"✅ 文档添加成功！共 {result['chunks_count']} 个片段")

                        # 记录文档
                        if uploaded_file.name not in st.session_state.documents:
                            st.session_state.documents.append(uploaded_file.name)

                    except Exception as e:
                        st.error(f"❌ 添加失败：{str(e)}")

        st.markdown("---")

        # 文档列表
        st.subheader("📄 已添加文档")
        rag = get_rag_engine()
        doc_count = rag.get_document_count()

        if doc_count > 0:
            st.info(f"知识库中共有 {doc_count} 个文档片段")
            for doc in st.session_state.documents:
                st.text(f"• {doc}")
        else:
            st.warning("知识库为空，请先上传文档")

        st.markdown("---")

        # 清空知识库
        if st.button("🗑️ 清空知识库"):
            rag.clear()
            st.session_state.documents = []
            st.session_state.messages = []
            st.success("知识库已清空")
            st.rerun()

    # 主区域 - 问答
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("💬 问答区域")

        # 显示历史消息
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 显示来源
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📖 查看来源"):
                        for source in message["sources"]:
                            st.markdown(f"""
                            <div class="source-box">
                                <strong>{source['source']}</strong> (相似度: {source['score']:.2f})<br>
                                {source['content'][:200]}...
                            </div>
                            """, unsafe_allow_html=True)

        # 用户输入
        if prompt := st.chat_input("请输入您的问题..."):
            # 显示用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    try:
                        rag = get_rag_engine()

                        # 检索相关文档
                        results = rag.search(prompt)

                        if results:
                            # 构建上下文
                            context = "\n\n".join([r["content"] for r in results])

                            # 调用LLM生成答案
                            answer = get_llm_response(prompt, context)

                            st.markdown(answer)

                            # 显示来源
                            with st.expander("📖 查看来源"):
                                for source in results:
                                    st.markdown(f"""
                                    <div class="source-box">
                                        <strong>{source['source']}</strong> (相关度: {source['score']:.2f})<br>
                                        {source['content'][:200]}...
                                    </div>
                                    """, unsafe_allow_html=True)

                            # 保存消息
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": results
                            })
                        else:
                            st.warning("文档中未找到相关信息，请先上传相关文档。")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "文档中未找到相关信息，请先上传相关文档。"
                            })

                    except Exception as e:
                        st.error(f"❌ 生成答案失败：{str(e)}")

    with col2:
        st.header("📊 使用说明")

        st.markdown("""
        ### 使用步骤

        1. **上传文档**
           - 在左侧上传 TXT 或 Markdown 文档
           - 点击"添加到知识库"

        2. **开始提问**
           - 在下方输入框输入问题
           - 系统会自动检索相关内容并生成答案

        3. **查看来源**
           - 点击"查看来源"可以看到答案引用的原文

        ### 示例问题

        - 年假有几天？
        - 公司的工作时间是什么？
        - 如何获取API Token？
        - 报销流程是什么？

        ### 注意事项

        - 请确保上传的文档与问题相关
        - 答案仅基于上传的文档内容生成
        - 如答案不准确，请检查文档内容
        """)


if __name__ == "__main__":
    main()
