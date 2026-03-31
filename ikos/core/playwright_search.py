"""Playwright 搜索引擎实现."""

from typing import Any

from loguru import logger

from .search_provider_base import SearchProvider
from .types import SearchResult, WebContent


class PlaywrightSearchProvider(SearchProvider):
    """基于 Playwright 的搜索引擎提供者."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        default_engine: str = "auto",
    ):
        """初始化 Playwright 搜索提供者.

        Args:
            headless: 是否无头模式
            timeout: 超时时间（毫秒）
            default_engine: 默认搜索引擎
        """
        self.headless = headless
        self.timeout = timeout
        self.default_engine = default_engine
        self._browser = None
        self._playwright = None

        # 搜索引擎 URL 模板
        self.engines = {
            "google": "https://www.google.com/search?q={query}",
            "bing": "https://www.bing.com/search?q={query}",
            "baidu": "https://www.baidu.com/s?wd={query}",
            "duckduckgo": "https://duckduckgo.com/?q={query}",
        }

    def _get_browser(self):
        """懒加载浏览器实例."""
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright

                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(
                    headless=self.headless,
                )
                logger.info("Playwright 浏览器已启动")
            except ImportError:
                logger.warning("playwright 库未安装，请运行：playwright install")
                raise
        return self._browser

    def _detect_engine(self) -> str:
        """自动检测可用的搜索引擎."""
        # 简化实现：默认返回 bing（国内可访问）
        # 实际应该检测网络环境
        return "bing"

    def _get_search_url(self, query: str, engine: str) -> str:
        """获取搜索 URL.

        Args:
            query: 搜索关键词
            engine: 搜索引擎名称

        Returns:
            str: 搜索 URL
        """
        if engine == "auto":
            engine = self._detect_engine()

        if engine not in self.engines:
            logger.warning(f"不支持的搜索引擎：{engine}，使用默认引擎")
            engine = self.default_engine

        return self.engines[engine].format(query=query)

    def search(
        self,
        query: str,
        max_results: int = 10,
        engine: str = "auto",
    ) -> list[SearchResult]:
        """执行搜索.

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            engine: 搜索引擎

        Returns:
            list[SearchResult]: 搜索结果列表
        """
        browser = self._get_browser()
        page = browser.new_page()

        try:
            # 访问搜索引擎
            url = self._get_search_url(query, engine)
            logger.info(f"搜索：{query} ({engine})")
            page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # 解析搜索结果（不同引擎使用不同选择器）
            results = self._parse_results(page, engine, max_results)
            logger.info(f"搜索完成，找到 {len(results)} 个结果")

            return results
        except Exception as e:
            logger.error(f"搜索失败：{e}")
            return []
        finally:
            page.close()

    def _parse_results(
        self,
        page: Any,
        engine: str,
        max_results: int,
    ) -> list[SearchResult]:
        """解析搜索结果页面.

        Args:
            page: Playwright 页面对象
            engine: 搜索引擎
            max_results: 最大结果数

        Returns:
            list[SearchResult]: 搜索结果
        """
        # 根据不同引擎使用不同的选择器
        selectors = {
            "google": {
                "container": "div.g",
                "title": "h3",
                "link": "a",
                "snippet": "div[data-sncf]",
            },
            "bing": {
                "container": "li.b_algo",
                "title": "h2 a",
                "link": "h2 a",
                "snippet": "div.b_caption p",
            },
            "baidu": {
                "container": "div.result",
                "title": "h3 a",
                "link": "h3 a",
                "snippet": "div.c-abstract",
            },
            "duckduckgo": {
                "container": "div[data-result]",
                "title": "h2 a",
                "link": "h2 a",
                "snippet": "div[data-result-excerpt]",
            },
        }

        if engine not in selectors:
            engine = "bing"

        selector = selectors[engine]
        results = []

        try:
            # 查找所有结果容器
            containers = page.query_selector_all(selector["container"])

            for i, container in enumerate(containers[:max_results]):
                try:
                    title_el = container.query_selector(selector["title"])
                    link_el = container.query_selector(selector["link"])
                    snippet_el = container.query_selector(selector["snippet"])

                    title = title_el.inner_text() if title_el else ""
                    url = link_el.get_attribute("href") if link_el else ""
                    snippet = snippet_el.inner_text() if snippet_el else ""

                    if title and url:
                        results.append(
                            SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet,
                                source=engine,
                                rank=i + 1,
                            )
                        )
                except Exception as e:
                    logger.debug(f"解析单个结果失败：{e}")
                    continue

        except Exception as e:
            logger.error(f"解析搜索结果失败：{e}")

        return results

    def fetch_content(self, url: str, extract_text: bool = True) -> WebContent:
        """抓取网页内容.

        Args:
            url: 网页 URL
            extract_text: 是否提取纯文本

        Returns:
            WebContent: 网页内容
        """
        browser = self._get_browser()
        page = browser.new_page()

        try:
            logger.info(f"抓取网页：{url}")
            page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # 获取标题
            title = page.title()

            # 获取内容
            if extract_text:
                content = self._extract_text(page)
                html = None
            else:
                content = ""
                html = page.content()

            return WebContent(
                url=url,
                title=title,
                content=content,
                html=html,
            )
        except Exception as e:
            logger.error(f"抓取网页失败：{url} - {e}")
            raise
        finally:
            page.close()

    def _extract_text(self, page: Any) -> str:
        """从网页提取纯文本（去除导航、广告等）.

        Args:
            page: Playwright 页面对象

        Returns:
            str: 纯文本内容
        """
        text = page.evaluate(
            """
            () => {
                // 移除不需要的元素
                const remove = ['nav', 'header', 'footer', 'aside', 'script', 'style', 'ads'];
                remove.forEach(tag => {
                    document.querySelectorAll(tag).forEach(el => el.remove());
                });
                return document.body.innerText;
            }
        """
        )
        return text.strip()

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 5,
        engine: str = "auto",
    ) -> list[WebContent]:
        """搜索并抓取内容.

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            engine: 搜索引擎

        Returns:
            list[WebContent]: 网页内容列表
        """
        # 先搜索
        search_results = self.search(query, max_results, engine)

        # 再抓取每个页面的内容
        contents = []
        for result in search_results:
            try:
                content = self.fetch_content(result.url)
                contents.append(content)
            except Exception as e:
                logger.warning(f"抓取失败 {result.url}: {e}")
                continue

        return contents

    def add_api_provider(self, name: str, config: dict[str, Any]) -> None:
        """添加 API 搜索提供者（预留扩展）.

        Args:
            name: 提供者名称
            config: 提供者配置
        """
        logger.warning(f"PlaywrightSearchProvider 暂不支持添加 API 提供者：{name}")

    def list_engines(self) -> list[str]:
        """列出所有支持的搜索引擎.

        Returns:
            list[str]: 引擎列表
        """
        return list(self.engines.keys()) + ["auto"]

    def __del__(self):
        """析构函数，关闭浏览器."""
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
