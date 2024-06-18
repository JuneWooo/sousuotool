import time
from app.chrome_driver.chromium import ChromiumLoader
from app.utils.cleanup_html import cleanup_html
from loguru import logger
from typing import List
from app.schemas.search_schema import SearchData


class WebSearch:
    
    def delta_search(self, message: str, num:int) -> List[SearchData]:
        """
        func:增量检索
        params:
            message: key words
        return:
            [
                {
                    "content": "缩略信息"
                    "metadata": {
                        "title": "xxx",
                        "source": "http:xxxx"
                    }
                }
                ...
            ]
        """
        data = []
        loader = ChromiumLoader(keywords=[message])
        documents = loader.load()
        for doc in documents:
            data.append(
                SearchData(content=doc.page_content, metadata=doc.metadata)
            )
        
        if len(data) >= num:
            return data[:num]
        else:
            return data

    def full_search(self, message: str, num:int) -> List[SearchData]:
        """
        func: 全量检索
        params:
            message: key words
        return:
            [
                {
                    "title": "xxx",
                    "content": "所有信息"
                    "source": "http:xxxx"
                }
                ...
            ]
        """
        data = []
        url_parsed_docs = []
        loader = ChromiumLoader(keywords=[message])
        documents = loader.load()
        metadata_list = [doc.metadata for doc in documents]
        time.sleep(1)
        url_loader = ChromiumLoader(
            urls=[item["source"] for item in metadata_list])
        url_documents = url_loader.load()
        for url_doc in url_documents:
            if url_doc.page_content:
                doc = url_loader.parse_content(url_doc, metadata_list)
                url_parsed_docs.append(doc)
            else:
                continue

        for doc in url_parsed_docs:
            data.append(
                SearchData(content=doc.page_content, metadata=doc.metadata)
            )
        
        if len(data) >= num:
            return data[:num]
        else:
            return data
    def url_search(self, url: str) -> List[SearchData]:
        """
        func: 请求链接，解析结果
            request url 请求
            :return:
        """
        data = []
        loader = ChromiumLoader(urls=[url])
        document = loader.load()

        try:
            title, minimized_body, link_urls, image_urls = cleanup_html(
                str(document[0].page_content), url
            )
        except Exception as e:
            logger.error(f"error:{e}")
            return [
                SearchData(
                    content="parser content error!", metadata={"source": url}
                )
            ]
        else:
            parsed_content = loader.parse_url_content(minimized_body)
            data = [
                SearchData(content=parsed_content, metadata={"source": url})
            ]
            return data


web_search = WebSearch()
