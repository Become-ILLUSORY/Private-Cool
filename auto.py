import base64
import json
import re
import requests
from typing import Dict, Any, List, Optional

def decode_from_url(url: str, output_json: str) -> Optional[Dict[str, Any]]:
    """
    从 URL 下载内容，尝试提取 Base64 编码的 JSON 并返回解析后的字典。
    同时保存到 output_json 文件。
    """
    try:
        print(f"正在从 {url} 下载数据...")
        response = requests.get(url)
        response.raise_for_status()
        content = response.content
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

    # 尝试整个内容是 Base64
    try:
        decoded = base64.b64decode(content, validate=True)
        data = json.loads(decoded.decode('utf-8'))
        _save_json(data, output_json)
        return data
    except Exception:
        pass

    # 转为字符串，忽略非法字符
    text = content.decode('utf-8', errors='ignore')
    candidates = re.findall(r'[A-Za-z0-9+/]{100,}={0,2}', text)

    # 优先从后往前尝试
    for candidate in reversed(candidates):
        try:
            missing_padding = len(candidate) % 4
            if missing_padding:
                candidate += '=' * (4 - missing_padding)
            decoded_bytes = base64.b64decode(candidate, validate=True)
            data = json.loads(decoded_bytes.decode('utf-8'))
            _save_json(data, output_json)
            return data
        except Exception:
            continue

    # 正向尝试
    for candidate in candidates:
        try:
            missing_padding = len(candidate) % 4
            if missing_padding:
                candidate += '=' * (4 - missing_padding)
            decoded_bytes = base64.b64decode(candidate, validate=True)
            data = json.loads(decoded_bytes.decode('utf-8'))
            _save_json(data, output_json)
            return data
        except Exception:
            continue

    print("❌ 未能找到有效的 Base64 编码的 JSON 数据。")
    return None

def _save_json(data: Dict[str, Any], filename: str) -> None:
    """保存字典为格式化 JSON 文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ 数据已保存到 {filename}")

def insert_single_site_into_data(
    data: Dict[str, Any],
    new_site: Dict[str, Any],
    insert_pos: int = 1
) -> bool:
    """
    向 data['sites'] 的指定位置插入一个新站点
    """
    if "sites" not in data or not isinstance(data["sites"], list):
        print("⚠️ 未找到有效的 'sites' 列表，无法插入")
        return False

    if not isinstance(new_site, dict):
        print("⚠️ 新站点必须是字典")
        return False

    data["sites"].insert(insert_pos, new_site)
    print(f"✅ 已插入站点 '{new_site.get('name', '未知')}' 到位置 {insert_pos + 1}")
    return True

# ======================
# 主程序：下载 → 插入 → 保存
# ======================
if __name__ == "__main__":
    url = "http://ok321.top/tv"
    output_json = "jsm.json"

    # 第一步：下载并解码
    data = decode_from_url(url, output_json)
    if data is None:
        exit(1)

    # 第二步：定义你要插入的新站点（请按需修改）
    new_site = {
      "key": "Emby",
      "name": "Emby",
      "type": 3,
      "api": "csp_Emby",
      "searchable": 1,
      "quickSearch": 1,
      "filterable": 1,
      "ext": {
        "server": "https://www.example.com",
        "username":"admin",
        "password":"password",
        "ua":"Yamby/1.0.2(Android)",
        "client": "Yamby",
        "deviceName": "Xiaomi-Poco-X3",
        "commonConfig": "./json/peizhi.json"
      },
      "changeable": 1,
      "jar": "https://www.252035.xyz/z/custom_spider.jar"
    }

    # 第三步：插入到第2个位置（索引1）
    success = insert_single_site_into_data(data, new_site, insert_pos=2)

    # 第四步：如果插入成功，重新保存文件
    if success:
        _save_json(data, output_json)
        print("🎉 所有操作完成！")

