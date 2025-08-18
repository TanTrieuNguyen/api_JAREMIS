import os
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    requests = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def get_popular_diseases() -> List[Dict[str, Any]]:
    """
    Gọi WHO API (hoặc endpoint bạn cấu hình) để lấy danh sách bệnh phổ biến.
    backend/.env:
      WHO_API_URL=...
      WHO_API_KEY=... (nếu cần)
    Hỗ trợ cả JSON list, dict có 'value' (OData) hoặc dict đơn.
    """
    if load_dotenv:
        load_dotenv(dotenv_path='backend/.env')

    api_key = os.getenv("WHO_API_KEY")
    api_url = os.getenv("WHO_API_URL")

    if not api_url or requests is None:
        return []

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        if not resp.ok:
            return []
        data = resp.json()
        # Chuẩn hóa format trả về: ưu tiên list
        if isinstance(data, dict) and isinstance(data.get("value"), list):
            return data["value"]
        if isinstance(data, list):
            return data
        return [data]
    except Exception:
        return []