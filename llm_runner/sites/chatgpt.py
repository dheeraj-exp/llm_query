from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from llm_runner.selenium_utils import stable_text, wait_for_present
from llm_runner.sites.base import SiteResult


@dataclass
class ChatGPTAdapter:
    driver: object  # selenium webdriver
    name: str = "chatgpt"

    URL: str = "https://chatgpt.com/"

    def open(self) -> None:
        self.driver.get(self.URL)

        # Wait until prompt textarea exists (user may need to login first).
        # Prefer stable id selector; fallback to contenteditable textbox.
        try:
            wait_for_present(self.driver, "#prompt-textarea", timeout_s=180)
        except Exception:
            wait_for_present(
                self.driver,
                'div[contenteditable="true"][role="textbox"]',
                timeout_s=180,
            )

    def _prompt_el(self):
        els = self.driver.find_elements(By.CSS_SELECTOR, "#prompt-textarea")
        if els:
            return els[0]
        # fallback
        els = self.driver.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"][role="textbox"]')
        if not els:
            raise RuntimeError("Could not find ChatGPT prompt textbox.")
        return els[0]

    def _latest_assistant_markdown_el(self):
        # Most stable: assistant message blocks
        blocks = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-message-author-role="assistant"]')
        if not blocks:
            return None
        last = blocks[-1]
        md = last.find_elements(By.CSS_SELECTOR, ".markdown")
        return md[-1] if md else last

    def _is_generating(self) -> bool:
        # Try multiple signals: "Stop generating" button or streaming indicators.
        stop_btn = self.driver.find_elements(By.XPATH, "//button[.//span[contains(., 'Stop')]] | //button[contains(., 'Stop generating')]")
        if stop_btn:
            return True
        # Sometimes there's an aria-label
        stop_btn2 = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label*="Stop"]')
        return bool(stop_btn2)

    def submit_and_get_response(self, query: str) -> SiteResult:
        prompt = self._prompt_el()
        prompt.click()

        # Clear existing text if any (contenteditable varies); use Ctrl+A then Backspace.
        prompt.send_keys(Keys.CONTROL, "a")
        prompt.send_keys(Keys.BACKSPACE)
        prompt.send_keys(query)
        prompt.send_keys(Keys.ENTER)

        # Wait until an assistant message appears after submission.
        WebDriverWait(self.driver, 60).until(
            lambda d: self._latest_assistant_markdown_el() is not None
        )

        def get_latest_text() -> str:
            el = self._latest_assistant_markdown_el()
            return (el.text if el is not None else "").strip()

        # If generation is streaming, wait for stability; otherwise still stabilize briefly.
        # We also guard against the "echo" of previous response by waiting for text to change
        # after submit, when possible.
        first = get_latest_text()

        # Give the UI a moment to start streaming
        time.sleep(0.75)

        response = stable_text(get_latest_text, stable_for_s=2.0, timeout_s=120.0)

        # Sometimes stable_text returns the previous message if the new one failed to render.
        # If it didn't change at all, try a longer stabilization once.
        if response and response == first:
            time.sleep(1.0)
            response = stable_text(get_latest_text, stable_for_s=2.0, timeout_s=60.0)

        return SiteResult(response_text=response)

