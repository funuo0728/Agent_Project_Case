import time
import streamlit as st
from agent.react_agent import ReactAgent
from session_manager import SessionManager   # ← 新增导入


# ==================== 流式输出捕获（保持不变） ====================
def capture(generator, cache_list):
    for chunk in generator:
        cache_list.append(chunk)
        for char in chunk:
            time.sleep(0.01)
            yield char


# ==================== Streamlit 配置 ====================
st.set_page_config(
    page_title="扫地机器人智能客服",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("扫地机器人智能客服")
st.caption("RAG + ReAct Agent 多工具智能客服系统")

# ==================== 初始化 ====================
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

if "current_session" not in st.session_state:
    st.session_state.current_session = st.session_state.session_manager.generate_session_name()


# ====================== 侧边栏（大幅简化） ======================
with st.sidebar:
    st.subheader("AI控制面板")

    # 新建会话
    if st.button("新建会话", width="stretch", icon="✏️") and st.session_state.messages:
        error = st.session_state.session_manager.save_session(
            st.session_state.current_session, st.session_state.messages
        )
        if error:
            st.error(error)
        else:
            st.session_state.messages = []
            st.session_state.current_session = st.session_state.session_manager.generate_session_name()
            st.rerun()

    st.divider()
    st.text("会话历史")

    for session in st.session_state.session_manager.load_sessions():
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                session,
                key=f"load_{session}",
                icon="📄",
                type="primary" if session == st.session_state.current_session else "secondary",
                use_container_width=True
            ):
                new_current, new_messages, error = st.session_state.session_manager.switch_to_session(
                    session,
                    st.session_state.messages,
                    st.session_state.current_session
                )
                if error:
                    st.error(error)
                else:
                    st.session_state.current_session = new_current
                    st.session_state.messages = new_messages
                    st.rerun()

        with col2:
            if st.button("", key=f"delete_{session}", icon="❌️", help="删除此会话"):
                error = st.session_state.session_manager.delete_session(session)
                if error:
                    st.error(error)
                elif st.session_state.current_session == session:
                    st.session_state.messages = []
                    st.session_state.current_session = st.session_state.session_manager.generate_session_name()
                st.rerun()

    st.divider()
    st.text(f"会话名称：{st.session_state.current_session}")


# ====================== 主界面 ======================
for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

prompt = st.chat_input("💬 在这里输入你的问题...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    response_messages = []
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state.agent.execute_steam(prompt)
        st.chat_message("assistant").write(capture(res_stream, response_messages))

    if response_messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_messages[-1]
        })

    # 保存会话（错误也在前端显示）
    error = st.session_state.session_manager.save_session(
        st.session_state.current_session, st.session_state.messages
    )
    if error:
        st.error(error)
    st.rerun()