import time
import os
import json
from datetime import datetime

import streamlit as st
from agent.react_agent import ReactAgent


# ==================== 会话管理工具函数 ====================
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def save_session():
    if "current_session" not in st.session_state:
        return
    try:
        session_data = {
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages,
        }
        os.makedirs("sessions", exist_ok=True)
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="UTF-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.toast(f"💾 保存失败: {e}", icon="⚠️")


def load_sessions():
    if not os.path.exists("sessions"):
        return []
    session_list = []
    for file in os.listdir("sessions"):
        if file.endswith(".json"):
            session_list.append(file[:-5])
    return sorted(session_list, reverse=True)


def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            if st.session_state.messages:
                save_session()
            with open(f"sessions/{session_name}.json", "r", encoding="UTF-8") as f:
                data = json.load(f)
                st.session_state.current_session = session_name
                st.session_state.messages = data.get("messages", [])
    except Exception as e:
        st.error(f"加载会话失败: {e}")


def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if st.session_state.current_session == session_name:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception as e:
        st.error(f"删除会话失败: {e}")


# ==================== 流式输出捕获 ====================
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

# ==================== 初始化 ====================
# Agent 必须在这里初始化（解决 "st.session_state has no attribute 'agent'"）
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()


# ====================== 侧边栏 ======================
with st.sidebar:
    st.subheader("AI控制面板")

    # 新建会话
    if st.button("新建会话", width="stretch", icon="✏️") and st.session_state.messages:
        save_session()
        st.session_state.messages = []
        st.session_state.current_session = generate_session_name()
        save_session()
        st.rerun()

    st.divider()
    st.text("会话历史")

    for session in load_sessions():
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                session,
                key=f"load_{session}",
                icon="📄",
                type="primary" if session == st.session_state.current_session else "secondary",
                use_container_width=True
            ):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", key=f"delete_{session}", icon="❌️", help="删除此会话"):
                delete_session(session)
                st.rerun()

    st.divider()
    st.text(f"会话名称：{st.session_state.current_session}")


# ====================== 主界面 ======================
st.title("扫地机器人智能客服")
st.caption("RAG + ReAct Agent 多工具智能客服系统")

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

    if st.session_state.messages:
        save_session()
        st.rerun()