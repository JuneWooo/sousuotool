import asyncio
import html2text
import random
from typing import Any, Iterator, List, Optional, AsyncIterator
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from loguru import logger
from lxml import etree
from readability.readability import Document as rDocument  # type:ignore
from app.config.config import settings
from app.utils.cleanup_html import cleanup_html
from app.utils.utils import dynamic_import

filter_str = [
    "播报",
    "暂停",
    " 快捷键说明",
    " 空格",
    ": 播放 / 暂停",
    "Esc",
    ": 退出全屏",
    " ↑",
    ": 音量提高10%",
    " ↓",
    ": 音量降低10%",
    " →",
    ": 单次快进5秒",
    " ←",
    ": 单次快退5秒",
    "按住此处可拖拽",
    " 不再出现",
    " 可在播放器设置中重新打开小窗播放",
    "\ue610",
    "\ue66a",
    "\ue734",
    "\n" "详情",
    "人物经历",
    "个人履历",
    "职务任免",
    "成长历程",
    "成功经历",
    "出诊时间",
    "百度百科",
]

converter = html2text.HTML2Text()

class ChromiumLoader(BaseLoader):
    def __init__(
        self,
        urls: Optional[List[str]] = None,
        keywords: Optional[List[str]]= None,
        *,
        backend: str = "playwright",
        headless: bool = True,
        **kwargs: Any,
    ):
        message = (
            f"{backend} is required for ChromiumLoader. "
            f"Please install it with `pip install {backend}`."
        )

        dynamic_import(backend, message)

        self.backend = backend
        self.browser_config = kwargs
        self.headless = headless
        self.urls = urls
        self.keywords = keywords

    async def ascrape_url_playwright(self, url: str) -> str:
        """
        Asynchronously scrape the content of a given URL using Playwright's async API.

        Args:
            url (str): The URL to scrape.
        Returns:
            str: The scraped HTML content or an error message if an exception occurs.

        """
        from playwright.async_api import async_playwright  # type:ignore
        from undetected_playwright import Malenia  # type:ignore

        logger.info("Starting scraping...")
        results = ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless, **self.browser_config
            )
            try:
                context = await browser.new_context()
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                await page.goto(url)
                # 等待页面完成
                await page.wait_for_load_state(
                    "domcontentloaded", timeout=30000
                )
                results = await page.content()  # Simply get the HTML content
                logger.info("Content scraped")
            except Exception as e:
                results = f"Error: {e}"
            await browser.close()
        return results

    async def ascrape_keyword_playwright(self, keyword: str) -> List[str]:
        """
        Asynchronously scrape the content of a given URL using Playwright's async API.

        Args:
            keyword (str): use keyword to search data by baidu or bing.
        Returns:
            str: The scraped HTML content or an error message if an exception occurs.

        """
        from playwright.async_api import async_playwright
        from undetected_playwright import Malenia

        logger.info("Starting scraping Page 1")
        results = []
        result = ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless, **self.browser_config
            )
            try:
                context = await browser.new_context()
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                # 访问 baidu
                await page.goto(settings.BAIDU_URL)
                # 如果下面的代码无法输入，则使用 page.locator('input[name=\"wd\"]').type(keyword) 模拟键盘输入
                await page.locator('input[name="wd"]').fill(keyword)
                await page.locator("#su").click()  # 点击搜索
                await page.wait_for_load_state(
                    "domcontentloaded"
                )  # 等待页面搜索完成
                await page.wait_for_selector(
                    "#content_left", state="attached", timeout=random.randint(6000, 10000)
                )
                result = await page.content()  # Simply get the HTML content
                logger.warning("Page 1 content scraped")
                results.append(await page.content())
                try:
                    logger.info("Starting scraping Page 2")
                    next_page_result = ""
                    # 假设".pn-next"是下一页的链接选择器，这需要根据实际页面结构调整
                    next_page_button = await page.query_selector("a.n")
                    if next_page_button:
                        await next_page_button.click()
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_selector("#content_left", state="attached", timeout=random.randint(10000, 15000))
                        # await page.screenshot(path='screenshot_after_next_page_click.png')
                        # 收集第二页内容
                        next_page_result = await page.content()
                        results.append(next_page_result)
                        logger.warning("Page 2 content scraped")
                    else:
                        logger.warning("No 'Next Page' button found.")
                except Exception as e:
                    logger.error(f"next page error:{e}")
                    results.append(result)

            except Exception as e:
                result = f"Error: {e}"
                results.append(result)
            finally:
                await browser.close()
        return results

    def parse_url_content(self, html_str: str) -> str:
        # 转换为 markdown
        markdown_content = "parse url content error!"

        try:
            rdoc = rDocument(html_str)
            article = rdoc.summary()
        except Exception as e:
            logger.error(f"error:{e}")
            article = "not found html content"
        else:
            # 转换为 markdown
            markdown_content = converter.handle(article)

        return markdown_content

    def parse_content(
        self, url_document: Document, metadata_list: List[dict]
    ) -> Document:
        # 初步解析网页
        metadata = {"title": "", "source": url_document.metadata["source"]}
        for item in metadata_list:
            if url_document.metadata["source"] == item["source"]:
                metadata = item

        try:
            minimized_body = cleanup_html(
                str(url_document.page_content), url_document.metadata["source"]
            )[1]
        except Exception as e:
            logger.error(f"error:{e}")

            return Document(page_content="not found", metadata=metadata)
        else:
            # 抽取网页主要内容
            rdoc = rDocument(str(minimized_body))
            article = rdoc.summary()

            # 转换为 markdown
            markdown_content = converter.handle(article)

            parse_doc = Document(page_content=markdown_content, metadata=metadata)

            return parse_doc

    def parse_keyword_html(self, html_content: str) -> List[Document]:
        docs:list[Document] = []
        filter_list:list = []
        
        try:
            html_tree = etree.HTML(html_content)
            all_divs = html_tree.xpath("//*[@id='content_left']//div")  # type:ignore
            # if isinstance(all_divs, list):
            for div in all_divs:  # type:ignore
                tpl = div.attrib.get("tpl")  # type:ignore
                if tpl in ["sg_kg_entity_san", "bk_polysemy", "se_com_default"]:
                    title_strings = [str(element) for element in div.xpath(".//h3/a//text()")]  # type:ignore
                    title = "".join(title_strings)
                    link_strings = [str(element) for element in div.xpath(".//h3/a//@href")]  # type:ignore
                    link = "".join(link_strings)
                    content_tag: list[str] = div.xpath(".//h3/following-sibling::div/div//text()")  # type:ignore
                
                    # 过滤并拼接内容
                    filter_content = list(filter(lambda x: x not in filter_str, content_tag))
                    filter_content = [item for item in filter_content if "\n" not in item]
                    doc_content = "".join(filter_content)
                    
                    # 构建Document对象
                    metadata = {"title": title, "source": link}
                    doc = Document(page_content=doc_content, metadata=metadata)
                    
                    # 去重
                    if (doc_content, metadata) not in filter_list:
                        docs.append(doc)
                        filter_list.append((doc_content, metadata))

                elif tpl == "news-realtime":
                    pass
        except etree.HTMLParseError as e:
            print(f"HTML解析错误: {e}")
            return [Document(page_content="html 解析错误")]
        else:        
            return docs


    def lazy_load(self) -> Iterator[Document]:
        """
        Lazily load text content from the provided URLs.

        This method yields Documents one at a time as they're scraped,
        instead of waiting to scrape all URLs before returning.

        Yields:
            Document: The scraped content encapsulated within a Document object.

        """
        
        if self.urls:
            scraping_fn = getattr(self, f"ascrape_url_{self.backend}")

            for url in self.urls:
                html_content = asyncio.run(scraping_fn(url))
                metadata = {"source": url}
                yield Document(page_content=html_content, metadata=metadata)
        
        elif self.keywords:
            documents = []
            scraping_fn = getattr(self, f"ascrape_keyword_{self.backend}")
            
            for keyword in self.keywords:
                html_contents = asyncio.run(scraping_fn(keyword))
                
                for html in html_contents:
                    docs = self.parse_keyword_html(html)
                    documents.extend(docs)
                
            for doc in documents:
                yield doc

    
    async def alazy_load(self) -> AsyncIterator[Document]:
        """
        Asynchronously load text content from the provided URLs.

        This method leverages asyncio to initiate the scraping of all provided URLs
        simultaneously. It improves performance by utilizing concurrent asynchronous
        requests. Each Document is yielded as soon as its content is available,
        encapsulating the scraped content.

        Yields:
            Document: A Document object containing the scraped content, along with its
            source URL as metadata.
        """

        if self.urls:
            scraping_fn = getattr(self, f"ascrape_{self.backend}")

            tasks = [scraping_fn(url) for url in self.urls]
            results = await asyncio.gather(*tasks)
            for url, content in zip(self.urls, results):
                metadata = {"source": url}
                yield Document(page_content=content, metadata=metadata)

        elif self.keywords:
            scraping_fn = getattr(self, f"ascrape_keyword_{self.backend}")

            for keyword in self.keywords:
                html_content = asyncio.run(scraping_fn(keyword))

                metadata = {"title": keyword}
                yield Document(page_content=html_content, metadata=metadata)
