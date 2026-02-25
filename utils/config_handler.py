import yaml
import os
import re
from dotenv import load_dotenv
from utils.path_tool import get_abs_path

# ==================== 加载 .env ====================
load_dotenv(override=True)


# ==================== 增强版环境变量解析器 ====================
def resolve_env_vars(obj):
    """递归解析 ${VAR}，并自动把 \n 转成真实换行符"""
    if isinstance(obj, str):
        def replacer(match):
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value:
                # 关键修复：支持字面 \n 转义
                value = value.replace('\\n', '\n')
            if value is None:
                print(f"⚠️ 环境变量未找到: {var_name}")
                return f"${{{var_name}}}"
            return value

        return re.sub(r'\$\{([^}:]+)(?::([^}]*))?\}', replacer, obj)

    elif isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    else:
        return obj


# =================================================================

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


# ==================== 加载配置 ====================
rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()
tools_conf = load_tools_config()

if __name__ == '__main__':
    pk = tools_conf.get("get_weather", {}).get("PRIVATE_KEY_STR", "")
    print("✅ PRIVATE_KEY 加载成功！长度 =", len(pk))
    print("✅ PRIVATE_KEY 前300字符预览（带真实换行）:", repr(pk[:300]))
    print("✅ API_HOST =", tools_conf.get("get_weather", {}).get("API_HOST"))