from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_rag_prompt
from agent.tools.agent_tools import (rag_summarize, get_weather, get_user_location, get_user_id,
                                     get_current_month, fetch_external_data, fill_context_for_report)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model = chat_model,
            system_prompt = load_rag_prompt(),
            tools = [rag_summarize, get_weather, get_user_location, get_user_id, get_current_month, fetch_external_data, fill_context_for_report],
            middleware = [monitor_tool, log_before_model, report_prompt_switch]
        )

    def execute_steam(self, query: str):
        input_dict = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        }

        # context 表示上下文中runtime中的信息，用于动态切换提示词
        for chunk in self.agent.stream(input_dict, stream_mode = "values", context = {"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + '\n'

if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_steam("给我生成我的使用报告"):
        print(chunk, end = "")

