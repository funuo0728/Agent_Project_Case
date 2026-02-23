"""
为整个工程提供统一的绝对路径
"""
import os

def get_project_path() -> str:
    """
    获取项目路径
    :return:
    """
    # 当前文件路径向上跳两级
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_abs_path(relative_path: str) -> str:
    """
    获取绝对路径
    :param relative_path: 相对路径
    :return:
    """
    return os.path.join(get_project_path(), relative_path)

if __name__ == '__main__':
    print(get_abs_path('config.yml'))
