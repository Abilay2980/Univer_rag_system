import asyncio
from collections import deque
from typing import List, Set

from bs4 import BeautifulSoup
from langchain_core.documents import Document
from playwright.async_api import async_playwright

from app.core.config import settings


def bs4_extractor(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


class PlaywrightKaznuLoader:

    def __init__(self, login_url: str, max_pages: int = 200):
        self.login_url = login_url
        self.max_pages = max_pages

    async def async_load(self) -> List[Document]:
        documents = []
        visited_urls: Set[str] = set()
        queue = deque()

        async with async_playwright() as p:
            # Запускаем Chromium с эмуляцией реального браузера
            browser = await p.chromium.launch(
                headless=False, # Поставь False, чтобы один раз увидеть, что происходит
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                print("Переходим на страницу авторизации...")
                await page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1000)

                # Ввод логина и пароля с имитацией нажатия клавиш
                username_input = page.locator('input[type="text"]').first
                password_input = page.locator('input[type="password"]').first

                await username_input.click()
                await username_input.fill(settings.UNIVER_LOGIN)
                await page.wait_for_timeout(300)

                await password_input.click()
                await password_input.fill(settings.UNIVER_PASSWORD)
                await page.wait_for_timeout(300)

                # Нажимаем Enter для отправки формы (надежнее клика по кнопке в ASP.NET)
                print("Отправка формы...")
                await password_input.press("Enter")

                # Ждем успешного перехода с формы
                await page.wait_for_load_state("domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)

                print(f"Текущий URL после входа: {page.url}")

                if "error" in page.url or "login" in page.url:
                    print(" Ошибка авторизации: проверь UNIVER_LOGIN и UNIVER_PASSWORD в .env!")
                    return []

                # Стартуем сбор с главной страницы после входа
                start_url = page.url
                queue.append(start_url)

                # Обход страниц
                while queue and len(documents) < self.max_pages:
                    url = queue.popleft()

                    if url in visited_urls:
                        continue
                    visited_urls.add(url)

                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                        await page.wait_for_timeout(500)

                        if "login" in page.url:
                            print(f"[Пропуск - редирект на логин]: {url}")
                            continue

                        html = await page.content()
                        clean_text = bs4_extractor(html)

                        if len(clean_text) >= 40:
                            documents.append(
                                Document(
                                    page_content=clean_text,
                                    metadata={"source": page.url, "title": await page.title()},
                                )
                            )
                            print(f"[{len(documents)}] Сохранено: {page.url}")

                        # Поиск новых ссылок
                        hrefs = await page.eval_on_selector_all(
                            "a[href]",
                            "elements => elements.map(e => e.href)"
                        )

                        for href in hrefs:
                            if (
                                href.startswith("https://univer.kaznu.kz")
                                and href not in visited_urls
                                and "logout" not in href
                                and "change_language" not in href
                                and "error" not in href
                            ):
                                queue.append(href)

                    except Exception as e:
                        print(f"[Ошибка загрузки] {url}: {e}")

            finally:
                await browser.close()

        print(f"\nИтого собрано документов: {len(documents)}")
        return documents

    def load_documents(self) -> List[Document]:
        return asyncio.run(self.async_load())
def load_documents() -> List[Document]:
    loader = PlaywrightKaznuLoader(
        login_url="https://univer.kaznu.kz/user/login"
    )
    return loader.load_documents()