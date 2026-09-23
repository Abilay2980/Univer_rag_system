import asyncio
import re
from typing import List

from bs4 import BeautifulSoup
from langchain_core.documents import Document
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

from app.core.config import settings


def bs4_extractor(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "noscript",
        "form",
    ]):
        element.decompose()

    main = soup.find("main")

    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    return "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )


def is_russian(text: str) -> bool:
    russian_letters = re.findall(r"[а-яА-ЯёЁ]", text)
    kazakh_letters = re.findall(
        r"[әіңғүұқөһӘІҢҒҮҰҚӨҺ]",
        text,
    )

    total = len(russian_letters) + len(kazakh_letters)

    if total == 0:
        return False

    return len(kazakh_letters) / total < 0.05



class PlaywrightKaznuLoader:

    def __init__(self, login_url: str):
        self.login_url = login_url

    async def async_load(self) -> List[Document]:
        documents = []
        seen_urls = set()
        collected_pages = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
    headless=False,slow_mo = 1000
)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # 1. Страница логина
                await page.goto(
                    self.login_url,
                    wait_until="networkidle",
                    timeout=20000,
                )

                # 2. Логин
                await page.locator(
                    'input[type="text"]'
                ).first.fill(
                    settings.UNIVER_LOGIN
                )

                await page.locator(
                    'input[type="password"]'
                ).first.fill(
                    settings.UNIVER_PASSWORD
                )

                try:
                    async with page.expect_navigation(
                        wait_until="networkidle",
                        timeout=15000,
                    ):
                        await page.locator(
                            'button[type="submit"], '
                            'input[type="submit"]'
                        ).first.click()

                except PlaywrightTimeoutError:
                    await page.wait_for_timeout(3000)

                print("AFTER LOGIN:", page.url)

                # 4. Переходим на главную
                await page.goto(
                    "https://univer.kaznu.kz/",
                    wait_until="networkidle",
                    timeout=20000,
                )

                print("CURRENT URL:", page.url)

                # 5. Получаем ссылки
                links = page.locator("a")
                count = await links.count()

                for i in range(count):
                    link = links.nth(i)

                    try:
                        href = await link.get_attribute("href")

                        if not href:
                            continue

                        if href.startswith("#"):
                            continue

                        if href.startswith("javascript:"):
                            continue

                        url = await link.evaluate(
                            "(element) => element.href"
                        )

                        if not url:
                            continue

                        if not url.startswith(
                            "https://univer.kaznu.kz"
                        ):
                            continue

                        if url in seen_urls:
                            continue

                        seen_urls.add(url)

                        print("LINK:", url)

                        new_page = await context.new_page()

                        try:
                            await new_page.goto(
                                url,
                                wait_until="networkidle",
                                timeout=15000,
                            )

                            await new_page.wait_for_selector(
                                "body",
                                timeout=10000,
                            )

                            collected_pages.append({
                                "url": new_page.url,
                                "html": await new_page.content(),
                                "title": await new_page.title(),
                            })

                        except PlaywrightTimeoutError:
                            print(
                                f"Timeout: {url}"
                            )

                        except Exception as e:
                            print(
                                f"Ошибка загрузки {url}: {e}"
                            )

                        finally:
                            await new_page.close()

                    except Exception as e:
                        print(
                            f"Ошибка обработки ссылки: {e}"
                        )

                # 6. Создаём Documents
                for item in collected_pages:
                    clean_text = bs4_extractor(
                        item["html"]
                    )

                    if len(clean_text) < 50:
                        continue

                    if not is_russian(clean_text):
                        continue

                    existing_urls = {
                        doc.metadata.get("source")
                        for doc in documents
                    }

                    if item["url"] in existing_urls:
                        continue

                    documents.append(
                        Document(
                            page_content=clean_text,
                            metadata={
                                "source": item["url"],
                                "title": item["title"],
                                "language": "ru",
                                "type": "student_news",
                            },
                        )
                    )

            finally:
                await browser.close()

        print(f"Documents: {len(documents)}")

        return documents

    def load_documents(self) -> List[Document]:
        return asyncio.run(self.async_load())


def load_documents():
    loader = PlaywrightKaznuLoader(
        login_url="https://univer.kaznu.kz/user/login",
    )

    return loader.load_documents()