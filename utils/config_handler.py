import yaml
import os
import re
from dotenv import load_dotenv
from utils.path_tool import get_abs_path

# 1. 本地 .env（本地开发用）
load_dotenv(override=True)

# 2. Streamlit Cloud Secrets 自动注入（最关键的一步！）
try:
    import streamlit as st

    if hasattr(st, "secrets") and st.secrets:
        for key, value in st.secrets.items():
            # Secrets 优先级高于 .env，并自动处理 \n
            os.environ[key] = str(value).replace('\\n', '\n')
        st.info("✅ Streamlit Secrets 已成功加载到环境变量")
except:
    pass  # 本地没有 streamlit 时自动跳过


# 3. 解析器（支持 ${VAR} 并处理私钥换行）
def resolve_env_vars(obj):
    if isinstance(obj, str):
        def replacer(match):
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value is None:
                print(f"⚠️ 环境变量未找到: {var_name}")
                return f"${{{var_name}}}"
            return value

        return re.sub(r'\$\{([^}:]+)(?::([^}]*))?\}', replacer, obj)

    elif isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    return obj


# 以下函数保持你原来的结构不变（只加 resolve_env_vars）
def load_rag_config(config_path: str = get_abs_path("config/rag.yml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return resolve_env_vars(data)


def load_chroma_config(config_path: str = get_abs_path("config/chroma.yml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return resolve_env_vars(data)


def load_prompts_config(config_path: str = get_abs_path("config/prompts.yml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return resolve_env_vars(data)


def load_agent_config(config_path: str = get_abs_path("config/agent.yml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return resolve_env_vars(data)


def load_tools_config(config_path: str = get_abs_path("config/tools.yml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return resolve_env_vars(data)


# 加载配置
rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()
tools_conf = load_tools_config()