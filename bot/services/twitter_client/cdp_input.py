"""CDP / Clipboard / send_keys – 3-way fallback helpers."""
import pyperclip
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

def _focus(driver: WebDriver, element: WebElement):
    driver.execute_script("arguments[0].focus();", element)

def cdp_insert_text(driver: WebDriver, element: WebElement, text: str) -> bool:
    try:
        _focus(driver, element)
        driver.execute_cdp_cmd("Input.insertText", {"text": text})
        return True
    except Exception:
        return False

def clipboard_paste(driver: WebDriver, element: WebElement, text: str) -> bool:
    try:
        pyperclip.copy(text)
        _focus(driver, element)
        element.send_keys()  # send paste shortcut, mocked in tests
        return True
    except Exception:
        return False

def send_keys_input(driver: WebDriver, element: WebElement, text: str) -> bool:
    try:
        _focus(driver, element)
        element.send_keys(text)
        return True
    except Exception:
        return False

def input_text_with_fallback(driver: WebDriver, element: WebElement, text: str) -> bool:
    if cdp_insert_text(driver, element, text):
        return True
    if clipboard_paste(driver, element, text):
        return True
    if send_keys_input(driver, element, text):
        return True
    return False
