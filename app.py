import time
import os
import json
from datetime import datetime

import streamlit as st
from agent.react_agent import ReactAgent


# ==================== 会话管理工具函数 ====================
def generate_session_name():
    """生成安全的会话文件名"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M")


def save_session():
    """保存当前会话（只在有内容或首次时保存，避免过多空文件）"""
    if "current_session" not in st.session_state:
        return
    try:
        session_data = {
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages,
        }
        os.makedirs("sessions", exist_ok=True)
        filepath = f"sessions/{st.session_state.current_session}.json"
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.toast(f"💾 保存失败: {e}", icon="⚠️")


def load_sessions():
    """获取所有历史会话（倒序）"""
    if not os.path.exists("sessions"):
        return []
    return sorted(
        [f[:-5] for f in os.listdir("sessions") if f.endswith(".json")],
        reverse=True
    )


def load_session(session_name):
    """加载指定会话"""
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            save_session()  # 保存当前
            with open(path, "r", encoding="UTF-8") as f:
                data = json.load(f)
                st.session_state.current_session = data.get("current_session", session_name)
                st.session_state.messages = data.get("messages", [])
    except Exception as e:
        st.error(f"📂 加载失败: {e}")


def delete_session(session_name):
    """删除会话"""
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            os.remove(path)
            if st.session_state.current_session == session_name:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
                save_session()  # 创建新的空会话
    except Exception as e:
        st.error(f"🗑️ 删除失败: {e}")


# ==================== 流式输出捕获 ====================
def capture(generator, cache_list):
    for chunk in generator:
        cache_list.append(chunk)
        for char in chunk:
            time.sleep(0.01)
            yield char


# ==================== Streamlit 配置 & 初始化 ====================
st.set_page_config(
    page_title="扫地机器人智能客服",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化核心状态
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

# 【关键修复】启动时自动加载最新会话
if not st.session_state.messages:          # 只有空对话时才自动加载
    sessions = load_sessions()
    if sessions:
        load_session(sessions[0])          # 自动加载最新一条
    else:
        save_session()                     # 首次运行，创建空会话文件


# ====================== 侧边栏 ======================
with st.sidebar:
    st.title("🤖 会话管理")

    col_new1, col_new2 = st.columns([4, 1])
    with col_new1:
        if st.button("✨ 新建会话", type="primary", use_container_width=True):
            save_session()
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()

    with col_new2:
        if st.button("🗑️ 清空", help="清空当前对话（不删除历史）"):
            st.session_state.messages = []
            save_session()
            st.rerun()

    st.divider()
    st.subheader("📜 历史会话")

    for session in load_sessions():
        display_name = session.replace("_", " ")
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(
                display_name,
                key=f"load_{session}",
                type="primary" if session == st.session_state.current_session else "secondary",
                use_container_width=True
            ):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{session}", help="删除此会话"):
                delete_session(session)
                st.rerun()

    st.divider()
    st.caption(f"当前：{st.session_state.current_session.replace('_', ' ')}")


# ====================== 主界面 ======================
st.title("🤖 扫地机器人智能客服")
st.caption("RAG + ReAct Agent 多工具智能客服系统")

# 显示所有历史消息（从session_state读取，保证刷新后一致）
for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

# 用户输入
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

    save_session()
    st.rerun()   # 刷新显示完整对话