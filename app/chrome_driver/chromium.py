import asyncio
import html2text
from typing import Any, AsyncIterator, Iterator, List, Optional
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from readability.readability import Document as rDocument
from loguru import logger
from app.utils.utils import dynamic_import, Proxy, parse_or_search_proxy
from lxml import etree
from app.utils.cleanup_html import cleanup_html
from app.config.config import settings



logger.info("web-loader unit")
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
    "\n"
    "详情",
    "人物经历",
    "个人履历",
    "职务任免",
    "成长历程",
    "成功经历",
    "出诊时间",
    "百度百科"
]

converter = html2text.HTML2Text()

class ChromiumLoader(BaseLoader):
    def __init__(
        self,
        urls: List[str] = None,
        keywords: List[str] = None,
        search_type: str = None,
        *,
        backend: str = "playwright",
        headless: bool = True,
        proxy: Optional[Proxy] = None,
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
        self.proxy = parse_or_search_proxy(proxy) if proxy else None
        self.urls = urls
        self.keywords = keywords
        self.search_type = search_type

    async def ascrape_url_playwright(self, url: str) -> str:
        """
        Asynchronously scrape the content of a given URL using Playwright's async API.

        Args:
            url (str): The URL to scrape.
        Returns:
            str: The scraped HTML content or an error message if an exception occurs.

        """
        from playwright.async_api import async_playwright
        from undetected_playwright import Malenia

        logger.info("Starting scraping...")
        results = ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless, proxy=self.proxy, **self.browser_config
            )
            try:
                context = await browser.new_context()
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                await page.goto(url)
                # 等待页面完成
                await page.wait_for_load_state("domcontentloaded", timeout=30000)
                results = await page.content()  # Simply get the HTML content
                logger.info("Content scraped")
            except Exception as e:
                results = f"Error: {e}"
            await browser.close()
        return results

    async def ascrape_keyword_playwright(self, keyword: str) -> str:
        """
        Asynchronously scrape the content of a given URL using Playwright's async API.

        Args:
            keyword (str): use keyword to search data by baidu or bing.
        Returns:
            str: The scraped HTML content or an error message if an exception occurs.

        """
        from playwright.async_api import async_playwright
        from undetected_playwright import Malenia

        logger.info("Starting scraping...")
        results = ""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless, proxy=self.proxy, **self.browser_config
            )
            try:
                context = await browser.new_context()
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                # 访问 baidu
                await page.goto(settings.BAIDU_URL)
                # 如果下面的代码无法输入，则使用 page.locator('input[name=\"wd\"]').type(keyword) 模拟键盘输入
                await page.locator("input[name=\"wd\"]").fill(keyword)
                await page.locator("#su").click()  # 点击搜索
                await page.wait_for_load_state("domcontentloaded")   # 等待页面搜索完成
                await page.wait_for_selector("#content_left", state="attached", timeout=5000)
                results = await page.content()  # Simply get the HTML content
                logger.info("Content scraped")
            except Exception as e:
                results = f"Error: {e}"
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

    def parse_content(self, url_document: Document, metadata_list: List[dict]) -> Document:
        # 初步解析网页
        metadata = {
            "title": "",
            "source": url_document.metadata["source"]
        }
        for item in metadata_list:
            if url_document.metadata["source"] == item["source"]:
                metadata = item

        try:
            title, minimized_body, link_urls, image_urls = cleanup_html(
                str(url_document.page_content), url_document.metadata["source"]
            )
        except Exception as e:
            logger.error(f"error:{e}")

            return Document(
                page_content="not found",
                metadata=metadata
            )
        else:
            # 抽取网页主要内容
            rdoc = rDocument(str(minimized_body))
            article = rdoc.summary()

            # 转换为 markdown
            markdown_content = converter.handle(article)

            parse_doc = Document(
                page_content=markdown_content,
                metadata=metadata
            )

            return parse_doc

    def parse_keyword_html(self, html_content: str) -> List[Document]:
        doc_content = ""
        result = []
        docs = []
        html_tree = etree.HTML(html_content)
        # divs = html_tree.xpath(
        #     "//*[@id='content_left']//div[@tpl='se_com_default']")
        divs = html_tree.xpath("//*[@id='content_left']//div")

        for div in divs:
            # tpl (sg_kg_entity_san（有视频）、 bk_polysemy):百度百科 、se_com_default 普通网页
            if div.attrib.get("tpl") in ["sg_kg_entity_san", "bk_polysemy", "se_com_default"]:
                metadata = {
                    "title": "",
                    "source": ""
                }
                title = "".join(div.xpath(".//h3/a//text()"))
                link = "".join(div.xpath(".//h3/a//@href"))
                content_tag = div.xpath('.//h3/following-sibling::div/div//text()')  # noqa

                if content_tag:
                    filter_content = list(
                        filter(lambda x: x not in filter_str, content_tag))
                    filter_content = [
                        item for item in filter_content if '\n' not in item]
                    doc_content = "".join(filter_content)
                else:
                    continue

                metadata["title"] = title
                metadata["source"] = link

                # doc_content = re.sub(r'[^\u4e00-\u9fff]+', ',', doc_content)
                # doc_content = re.sub(r'\s+', '', doc_content)
                print(f"title: {title}, link: {link}, doc_content: {doc_content}")  # noqa

                if (doc_content, metadata) not in result:
                    result.append((doc_content, metadata))
                    doc = Document(page_content=doc_content, metadata=metadata)
                    docs.append(doc)

            elif div.attrib.get("tpl") == "news-realtime":
                pass

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
            scraping_fn = getattr(self, f"ascrape_keyword_{self.backend}")
            for keyword in self.keywords:
                html_content = asyncio.run(scraping_fn(keyword))
                docs = self.parse_keyword_html(html_content)
                for doc in docs:
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
