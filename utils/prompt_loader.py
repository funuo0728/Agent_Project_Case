from utils.config_handler import prompts_conf
from utils.path_tool import get_abs_path
from utils.logger_handler import logger

def load_system_prompt():
    try:
        system_prompt_path = get_abs_path(prompts_conf["main_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_system_prompt]未找到系统提示语配置，请检查config/prompts.yml文件")
        raise e

    try:
        return open(system_prompt_path, "r", encoding = "utf-8").read()
    except FileNotFoundError as e:
        logger.error(f"[load_system_prompt]解析系统提示词失败，{str(e)}")
        raise e

def load_rag_prompt():
    try:
        rag_prompt_path = get_abs_path(prompts_conf["rag_summarize_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_rag_prompt]未找到系统提示语配置，请检查config/prompts.yml文件")
        raise e

    try:
        return open(rag_prompt_path, "r", encoding = "utf-8").read()
    except FileNotFoundError as e:
        logger.error(f"[load_rag_prompt]解析RAG总结提示词失败，{str(e)}")
        raise e

def load_report_prompt():
    try:
        report_prompt_path = get_abs_path(prompts_conf["report_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_report_prompt]未找到系统提示语配置，请检查config/prompts.yml文件")
        raise e

    try:
        return open(report_prompt_path, "r", encoding = "utf-8").read()
    except FileNotFoundError as e:
        logger.error(f"[load_report_prompt]解析报告生成提示词失败，{str(e)}")
        raise e

if __name__ == '__main__':
    print(load_report_prompt())