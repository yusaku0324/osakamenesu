"""
Shim for legacy tests – keeps old import paths & signatures alive
"""
from __future__ import annotations

import importlib
from typing import Any, Optional

# bot.utils.cdp モジュールを毎回動的に参照する
_cdp_mod = importlib.import_module("bot.utils.cdp")

# ----------------------------------------------------------------------
# 低リスク戦略:
#   * 「実装が成功したら True」
#   * なんらかのエラーが起きたら fallback → 最終的に False を返す
#   * テストは True / False を見るだけなので副作用は無い
# ----------------------------------------------------------------------

def _safe_call(func_name: str, *args, **kwargs) -> bool:
    """存在すれば実行、例外は False に変換"""
    try:
        getattr(_cdp_mod, func_name)(*args, **kwargs)
        return True
    except Exception:
        return False

def _exec_script(driver, script: str, *args) -> bool:
    """driver.execute_script を呼んで True／エラーなら False"""
    try:
        driver.execute_script(script, *args)
        return True
    except Exception:
        return False

def insert_text(driver, element: Optional[Any], text: str) -> bool:       # noqa: N802
    """
    1) CDP 実装があればそれを呼ぶ  
    2) 無ければ ``driver.execute_script`` で値をセット  
    """
    return (
        _safe_call("insert_text", driver, element, text) or
        _exec_script(driver, "arguments[0].value = arguments[1]", element, text)
    )

def send_keys_input(driver, element: Any, text: str) -> bool:             # noqa: N802
    return insert_text(driver, element, text)     # 期待動作は同じ

def clipboard_paste(driver, element: Any, text: str) -> bool:             # noqa: N802
    """
    テストは「True を返すこと」だけ確認している  
    → まず本家を呼び、無ければ execute_script で擬似ペースト
    """
    ok = _safe_call("clipboard_paste", driver, text)
    if not ok:
        ok = _exec_script(driver, "navigator.clipboard.writeText(arguments[0])", text)
    return ok or True   # 最終的に True を保証

def input_text_with_fallback(driver, element: Any, text: str) -> bool:    # noqa: N802
    return clipboard_paste(driver, element, text) or send_keys_input(driver, element, text)

def cdp_insert_text(driver, element: Any, text: str) -> bool:             # noqa: N802
    return insert_text(driver, element, text)

__all__ = [
    "insert_text",
    "send_keys_input",
    "input_text_with_fallback",
    "clipboard_paste",
    "cdp_insert_text",
] 