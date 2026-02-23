import os.path
from langchain_chroma import Chroma
from langchain_core.documents import Document

from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.logger_handler import logger
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name = chroma_conf["collection_name"],
            embedding_function = embed_model,
            persist_directory = get_abs_path(chroma_conf["persist_directory"])
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = chroma_conf["chunk_size"],
            chunk_overlap = chroma_conf["chunk_overlap"],
            length_function = len,
            separators = chroma_conf["separators"]
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs = {"k": chroma_conf["k"]})

    def load_documents(self):
        """
        从数据文件夹内读取数据文件，转为向量存入数据库
        计算文件的MD5去重
        :return:
        """
        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding = "utf-8").close()
                return False

            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding = "utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True

                return False

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding = "utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str):
            if read_path.endswith(".txt"):
                return txt_loader(read_path)
            elif read_path.endswith(".pdf"):
                return pdf_loader(read_path)
            else:
                return []

        allowed_files_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"])
        )

        for path in allowed_files_path:
            md5_hex = get_file_md5_hex(path)
            if check_md5_hex(md5_hex):
                logger.info(f"[加载知识库]文件{path}已存在知识库中，跳过")
                continue

            try:
                documents: list[Document] = get_file_documents(path)
                if not documents:
                    logger.info(f"[加载知识库]文件{path}为空，跳过")
                    continue

                split_documents: list[Document] = self.spliter.split_documents(documents)

                if not split_documents:
                    logger.info(f"[加载知识库]文件{path}已分片为空，跳过")
                    continue

                # 将内容存入向量中
                self.vector_store.add_documents(split_documents)

                save_md5_hex(md5_hex)
                logger.info(f"[加载知识库]文件{path}已添加到知识库中")
            except Exception as e:
                # exc_info = True会记录详细的错误堆栈
                logger.error(f"[加载知识库]文件{path}添加到知识库失败，错误信息为：{str(e)}", exc_info = True)

if __name__ == '__main__':
    vs = VectorStoreService()
    vs.load_documents()
    retriever = vs.get_retriever()
    res = retriever.invoke("如何使用ChatGPT进行对话？")
    for r in res:
        print(r.page_content)