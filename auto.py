import requests
import json
import re
from typing import List, Dict

class SiteFinderWithHashFields:
    def __init__(self):
        self.results: List[Dict] = []
        self.last_searched_names: List[str] = []
    
    def parse_hash_fields(self, hash_str: str) -> Dict:
        """解析URL中#后面的字符串，提取要添加的字段"""
        fields = {}
        if not hash_str:
            return fields
            
        hash_str = hash_str.replace('"', '').strip()
        pattern = r'(\w+)\s*:\s*(\w+)'
        matches = re.findall(pattern, hash_str)
        
        for key, value in matches:
            fields[key.strip()] = value.strip()
            
        return fields
    
    def get_sites_from_urls(self, urls: List[str], target_names: List[str]) -> List[Dict]:
        """从多个URL读取JSON数据，根据URL中的哈希值添加字段"""
        self.results = []
        self.last_searched_names = target_names.copy()
        found_names = set()
        
        for url in urls:
            headers = {
                "User-Agent": "okhttp/5.0.0-alpha.14",
                "Accept": "application/json, text/javascript, */*; q=0.01"
            }
            
            try:
                if '#' in url:
                    base_url, hash_str = url.split('#', 1)
                    additional_fields = self.parse_hash_fields(hash_str)
                else:
                    base_url = url
                    additional_fields = {}
                
                print(f"正在从 {base_url} 读取数据...")
                response = requests.get(base_url, timeout=10, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if 'sites' in data and isinstance(data['sites'], list):
                    for site in data['sites']:
                        if 'name' in site and site['name'] in target_names:
                            if site['name'] not in found_names:
                                found_names.add(site['name'])
                                site_copy = site.copy()
                                if additional_fields:
                                    site_copy.update(additional_fields)
                                self.results.append(site_copy)
                
            except requests.exceptions.RequestException as e:
                print(f"从 {url} 请求数据时发生错误: {e}")
            except json.JSONDecodeError:
                print(f"无法解析 {url} 返回的JSON数据")
            except Exception as e:
                print(f"处理 {url} 时发生意外错误: {e}")
        
        for name in target_names:
            if name not in found_names:
                print(f"所有URL中均未找到名称为'{name}'的站点")
        
        return self.results
    
    def get_results(self) -> List[Dict]:
        return self.results
    
    def save_results_to_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"结果已成功保存到 {file_path}")
            return True
        except Exception as e:
            print(f"保存结果到文件时发生错误: {e}")
            return False

def download_json_file(url, filename):
    """从指定URL下载JSON文件并保存到本地"""
    headers = {
        "User-Agent": "okhttp/5.0.0-alpha.14",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"文件已成功下载并保存为 {filename}")
    else:
        print(f"无法下载文件，状态码: {response.status_code}")

def read_json_file(filename):
    """读取本地JSON文件并返回数据"""
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def write_json_file(data, filename):
    """将数据写回到本地JSON文件"""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def replace_spider_key(data, new_value):
    """在字典中查找键为'spider'并替换其值"""
    if "spider" in data:
        data["spider"] = new_value

def replace_string_in_dict(d, replacements):
    """递归地在字典中搜索并替换字符串"""
    for key, value in d.items():
        if isinstance(value, dict):
            replace_string_in_dict(value, replacements)
        elif isinstance(value, list):
            for i in range(len(value)):
                if isinstance(value[i], dict):
                    replace_string_in_dict(value[i], replacements)
                elif isinstance(value[i], str):
                    for old_str, new_str in replacements.items():
                        if old_str in value[i]:
                            value[i] = value[i].replace(old_str, new_str)
        elif isinstance(value, str):
            for old_str, new_str in replacements.items():
                if old_str in value:
                    d[key] = d[key].replace(old_str, new_str)

def find_spider_value(emby_spider):
    """在字典中查找键为'spider'并返回其值"""
    return emby_spider.get("spider")

def insert_sites(data, sites_to_insert):
    """在 sites 数组的第二个位置插入新的站点信息"""
    if "sites" in data and isinstance(data["sites"], list):
        data["sites"][1:1] = sites_to_insert
        print(f"已插入 {len(sites_to_insert)} 个站点到sites数组的第二个位置")
    else:
        print("未找到有效的 'sites' 列表")

def main():
    # 配置参数
    pg_url = "https://www.252035.xyz/p/jsm.json"
    filename = "jsm.json"
    emby_url = "http://tvbox.xn--4kq62z5rby2qupq9ub.top/"
    emby_filename = "wex.json"
    new_spider_value = "https://www.252035.xyz/p/pg.jar"
    replacements = {
        "./lib/tokenm.json": "https://bp.banye.tech:7777/pg/lib/tokenm?token=qunyouyouqun",
        "./lib/": "https://www.252035.xyz/p/lib/"
    }
    
    # 用于获取站点的URL和目标名称
    json_urls = [
        "https://bp.banye.tech:7777/sub/qunyouyouqun/pg",
        "http://tvbox.xn--4kq62z5rby2qupq9ub.top/#jar:spider_value"  # 这里的spider_value是占位符
    ]
    site_names = ["🐮通用类型┃配置中心🐮", "🀄️emby┃4K🀄️", "🎠给力┃百度🎠", "AList",
                  "电报豆瓣","电报搜索","电报网页","鱼佬盘搜",
                  "账号更新","TG豆瓣","TG频道搜索","TG群组搜索"]
    
    # 下载JSON文件
    download_json_file(pg_url, filename)
    download_json_file(emby_url, emby_filename)

    # 读取并处理原始数据
    original_data = read_json_file(filename)
    print("原始数据:")
    print(json.dumps(original_data, indent=4, ensure_ascii=False))

    # 替换spider键值和字符串
    replace_spider_key(original_data, new_spider_value)
    replace_string_in_dict(original_data, replacements)

    # 提取emby的spider值（这是实际需要替换的值）
    emby_data = read_json_file(emby_filename)
    actual_spider_value = find_spider_value(emby_data)  # 获取wex.json中的真实spider值
    print("\n从wex.json中获取的实际spider值:")
    print(actual_spider_value)

    # 从URL获取站点信息
    finder = SiteFinderWithHashFields()
    new_sites = finder.get_sites_from_urls(json_urls, site_names)
    
    # 关键修复：将站点中jar字段的"spider_value"替换为实际的spider值
    for site in new_sites:
        if "jar" in site and site["jar"] == "spider_value":
            site["jar"] = actual_spider_value  # 替换占位符为实际值
    
    finder.save_results_to_file("banye.json")  # 保存替换后的站点
    
    # 插入获取到的站点到目标JSON
    insert_sites(original_data, new_sites)

    # 保存修改后的文件
    write_json_file(original_data, filename)
    print("\n修改后的数据:")
    print(json.dumps(original_data, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
