from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


@dataclass(frozen=True)
class DriverConfig:
    headless: bool
    profile_dir: Path
    window_width: int = 1280
    window_height: int = 900
    implicit_wait_s: float = 0.0


def build_chrome_driver(cfg: DriverConfig) -> webdriver.Chrome:
    cfg.profile_dir.mkdir(parents=True, exist_ok=True)

    opts = ChromeOptions()
    if cfg.headless:
        # new headless is closer to real mode
        opts.add_argument("--headless=new")
    opts.add_argument(f"--window-size={cfg.window_width},{cfg.window_height}")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--lang=en-US")
    opts.add_argument(f"--user-data-dir={str(cfg.profile_dir)}")

    # reduce automation flags (doesn't bypass auth; just stabilizes UI)
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    if cfg.implicit_wait_s:
        driver.implicitly_wait(cfg.implicit_wait_s)
    return driver


def wait_for_visible(driver, css: str, timeout_s: float = 30):
    return WebDriverWait(driver, timeout_s).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, css))
    )


def wait_for_present(driver, css: str, timeout_s: float = 30):
    return WebDriverWait(driver, timeout_s).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


def stable_text(get_text_fn, stable_for_s: float = 2.0, timeout_s: float = 90.0) -> str:
    """
    Poll get_text_fn until the returned text stays unchanged for stable_for_s.
    """
    start = time.time()
    last_text: Optional[str] = None
    last_change = time.time()
    while True:
        txt = (get_text_fn() or "").strip()
        now = time.time()
        if txt != last_text:
            last_text = txt
            last_change = now
        if last_text and (now - last_change) >= stable_for_s:
            return last_text
        if (now - start) >= timeout_s:
            return last_text or ""
        time.sleep(0.25)

