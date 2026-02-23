import os
import time
import jwt
import requests
from utils.logger_handler import logger
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from cryptography.hazmat.primitives import serialization
import random
from utils.config_handler import agent_conf, tools_conf
from utils.path_tool import get_abs_path

rag = RagSummarizeService()

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]

external_data = {}

@tool(description = "从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)

# @tool(description = "获取天气信息，已消息字符串返回")
# def get_weather(city: str) -> str:
#     return f"城市{city}的天气是晴天，天气温度是25度，空气湿度50%，南风1级，AQI21，最近6小时降雨概率60%。"

def generate_qweather_jwt():
    try:
        private_key_obj = serialization.load_pem_private_key(
            tools_conf["get_weather"]["PRIVATE_KEY_STR"].encode('utf-8'),
            password=None
        )
        payload = {
            'iat': int(time.time()) - 30,
            'exp': int(time.time()) + 900,
            'sub': tools_conf["get_weather"]["PROJECT_ID"]
        }
        headers = {'kid': tools_conf["get_weather"]["KEY_ID"]}
        # 使用 PyJWT 生成 EdDSA 签名
        return jwt.encode(payload, private_key_obj, algorithm='EdDSA', headers=headers)
    except Exception as e:
        logger.error(f"JWT生成失败: {e}")
        return None


@tool(description="获取天气信息，已消息字符串返回")
def get_weather(city: str) -> str:
    token = generate_qweather_jwt()
    if not token:
        return "本地 JWT 签名失败，请检查私钥和 cryptography 库。"

    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. 地理查询
        geo_url = f"https://{tools_conf["get_weather"]["API_HOST"]}/geo/v2/city/lookup"
        geo_response = requests.get(geo_url, params={"location": city}, headers=headers, timeout=10)
        geo_res = geo_response.json()

        if geo_res.get("code") != "200":
            return f"地理查询失败，代码: {geo_res.get('code')}"

        location_id = geo_res["location"][0]["id"]

        # 2. 实时天气（温度、天气现象、湿度、风向风力）
        weather_url = f"https://{tools_conf["get_weather"]["API_HOST"]}/v7/weather/now"
        w_response = requests.get(weather_url, params={"location": location_id}, headers=headers, timeout=10)
        weather_res = w_response.json()

        if weather_res.get("code") != "200":
            return f"天气数据失败，业务码：{weather_res.get('code')}"

        now = weather_res["now"]

        # 3. 空气质量（AQI）
        air_url = f"https://{tools_conf["get_weather"]["API_HOST"]}/v7/air/now"
        air_response = requests.get(air_url, params={"location": location_id}, headers=headers, timeout=10)
        air_res = air_response.json()
        aqi = air_res.get("now", {}).get("aqi", "35") if air_res.get("code") == "200" else "35"

        # 4. 逐小时预报 → 计算未来6小时平均降雨概率（更贴近“最近6小时”）
        hourly_url = f"https://{tools_conf["get_weather"]["API_HOST"]}/v7/weather/24h"
        h_response = requests.get(hourly_url, params={"location": location_id}, headers=headers, timeout=10)
        hourly_res = h_response.json()

        pop = "30"
        if hourly_res.get("code") == "200" and hourly_res.get("hourly"):
            pops = [int(h.get("pop", 0)) for h in hourly_res["hourly"][:6]]
            pop = str(sum(pops) // len(pops)) if pops else "30"

        # === 你想要的最终格式 ===
        result = (
            f"城市{city}的天气是{now.get('text', '晴')}，"
            f"天气温度是{now.get('temp', '25')}度，"
            f"空气湿度{now.get('humidity', '50')}%，"
            f"{now.get('windDir', '南风')}{now.get('windScale', '1')}级，"
            f"AQI{aqi}，"
            f"最近6小时降雨概率{pop}%。"
        )
        return result

    except Exception as e:
        logger.error(f"Weather Tool 运行异常: {e}")
        return f"城市{city}天气查询失败，请稍后再试。"

# ... 其他工具函数保持不变 ...

@tool(description = "获取用户所在城市的名称，以纯字符串形式返回")
def get_user_location() -> str:
    return random.choice(["北京", "上海", "广州", "深圳", "杭州", "西安", "武汉", "南京", "成都", "苏州"])

@tool(description = "获取用户的ID，以纯字符串形式返回")
def get_user_id() -> str:
    return random.choice(user_ids)

@tool(description = "获取当前月份，以纯字符串形式返回")
def get_current_month() -> str:
    return random.choice(month_arr)

def generator_external_data():
    """
    {
        "user_id": {
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            ...
        },
        "user_id": {
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            ...
        },
        "user_id": {
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            "month" : {"特征" : xxx, "效率" : xxx, ...}
            ...
        }
    }
    :return:
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"{generator_external_data}未找到外部数据目录，请检查config/agent.yml文件")

        with open(external_data_path, "r", encoding = "utf-8") as f:
            for line in f.readlines()[1:]:
                arr: line[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"', "")
                feature: str = arr[1].replace('"', "")
                efficiency: str = arr[2].replace('"', "")
                comsumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征" : feature,
                    "效率" : efficiency,
                    "耗材" : comsumables,
                    "对比" : comparison,
                }


@tool(description = "从外部系统中获取用户的使用记录，以纯字符串形式返回，若未检索到则返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generator_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.error(f"[fetch_external_data]未找到用户{user_id}的{month}月数据")
        return ""

@tool(description = "无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"


if __name__ == '__main__':
    print(get_weather("杭州"))
