"""Đăng ký / đăng nhập cục bộ: mật khẩu băm PBKDF2-SHA256 có muối, lưu trong data/users.json."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import datetime as dt

USERS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users.json")
_LOCK = threading.Lock()
ITER = 200_000


def _load() -> dict:
    try:
        with open(USERS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(users: dict) -> None:
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    tmp = USERS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_PATH)  # ghi nguyên tử, tránh hỏng tệp khi ghi dở


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITER).hex()


def register(username: str, password: str, fullname: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_.]{3,32}", u):
        return False, "Tên đăng nhập gồm 3–32 ký tự: chữ không dấu, số, dấu chấm hoặc gạch dưới."
    if len(password or "") < 6:
        return False, "Mật khẩu cần tối thiểu 6 ký tự."
    if not (fullname or "").strip():
        return False, "Vui lòng nhập họ tên."
    with _LOCK:
        users = _load()
        if u in users:
            return False, "Tên đăng nhập đã tồn tại."
        salt = secrets.token_hex(16)
        users[u] = {"fullname": fullname.strip(), "salt": salt, "hash": _hash(password, salt),
                    "created": dt.datetime.now().isoformat(timespec="seconds")}
        _save(users)
    return True, "Đăng ký thành công. Vui lòng đăng nhập."


def login(username: str, password: str) -> dict | None:
    u = (username or "").strip().lower()
    rec = _load().get(u)
    if not rec:
        _hash(password or "x", "00" * 16)  # cân bằng thời gian phản hồi, không lộ tài khoản tồn tại hay không
        return None
    if hmac.compare_digest(rec["hash"], _hash(password or "", rec["salt"])):
        return {"username": u, "fullname": rec["fullname"]}
    return None


def get_prefs(username: str) -> dict:
    return _load().get(username, {}).get("prefs", {})


def save_prefs(username: str, prefs: dict) -> None:
    """Lưu tùy chọn giao diện của từng người dùng."""
    with _LOCK:
        users = _load()
        if username in users:
            users[username]["prefs"] = prefs
            _save(users)
