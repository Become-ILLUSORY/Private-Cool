import os
import requests
import json
import re
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class HttpUtils:
    """网络请求工具类，负责所有HTTP相关操作"""
    DEFAULT_HEADERS = {
        "User-Agent": "okhttp/5.0.0-alpha.14",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    DEFAULT_TIMEOUT = 10

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    def get(self, url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[requests.Response]:
        """发送GET请求并返回响应"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"请求 {url} 失败: {str(e)}")
            return None

    def post(self, url: str, data: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> Optional[requests.Response]:
        """发送POST请求并返回响应"""
        try:
            headers = self.DEFAULT_HEADERS.copy()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"POST请求 {url} 失败: {str(e)}")
            return None

    def download_file(self, url: str, filename: str) -> bool:
        """下载文件并保存到本地"""
        response = self.get(url)
        if response:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"文件已保存至 {filename}")
                return True
            except IOError as e:
                print(f"保存文件 {filename} 失败: {str(e)}")
        return False


class WechatPusher:
    """微信消息推送工具类，基于ShowDoc推送服务"""
    def __init__(self, push_url: str):
        self.push_url = push_url
        self.http_utils = HttpUtils()

    def send_text(self, content: str, title: str = "系统通知") -> bool:
        """发送文本消息到微信"""
        if not self.push_url:
            print("未配置ShowDoc推送地址")
            return False
        if not title or not content:
            print("标题和内容不能为空")
            return False

        payload = {
            "title": title,
            "content": content
        }

        response = self.http_utils.post(self.push_url, payload)
        if not response:
            print("尝试使用GET方式推送...")
            response = self.http_utils.get(self.push_url, params=payload)

        if response:
            try:
                result = response.json()
                if result.get("error_code") == 0:
                    print("微信消息推送成功")
                    return True
                else:
                    print(f"微信消息推送失败: 错误码 {result.get('error_code')}, 原因: {result.get('error_message', '未知错误')}")
            except json.JSONDecodeError:
                print("解析推送响应失败，响应内容:", response.text)
        return False


class FileUtils:
    """文件操作工具类，负责JSON文件的读写"""

    @staticmethod
    def read_json(filename: str) -> Optional[Dict[str, Any]]:
        """读取JSON文件并返回字典"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"读取JSON文件 {filename} 失败: {str(e)}")
            return None

    @staticmethod
    def write_json(data: Dict[str, Any], filename: str) -> bool:
        """将字典写入JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"数据已写入 {filename}")
            return True
        except IOError as e:
            print(f"写入JSON文件 {filename} 失败: {str(e)}")
            return False


class SiteProcessor:
    """站点处理器，负责站点信息的解析、查找和处理"""

    @staticmethod
    def parse_hash_fields(hash_str: str) -> Dict[str, str]:
        """解析URL中#后面的字符串，提取要添加的字段"""
        if not hash_str:
            return {}
            
        hash_str = hash_str.replace('"', '').strip()
        pattern = r'(\w+)\s*:\s*(\w+)'
        matches = re.findall(pattern, hash_str)
        
        return {key.strip(): value.strip() for key, value in matches}

    @staticmethod
    def replace_spider_key(data: Dict[str, Any], new_value: str) -> None:
        """在字典中查找键为'spider'并替换其值"""
        if "spider" in data:
            data["spider"] = new_value

    @staticmethod
    def replace_string_in_dict(d: Dict[str, Any], replacements: Dict[str, str]) -> None:
        """递归地在字典中搜索并替换字符串"""
        for key, value in d.items():
            if isinstance(value, dict):
                SiteProcessor.replace_string_in_dict(value, replacements)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        SiteProcessor.replace_string_in_dict(item, replacements)
                    elif isinstance(item, str):
                        for old_str, new_str in replacements.items():
                            if old_str in item:
                                item = item.replace(old_str, new_str)
            elif isinstance(value, str):
                for old_str, new_str in replacements.items():
                    if old_str in value:
                        d[key] = d[key].replace(old_str, new_str)

    @staticmethod
    def insert_sites(data: Dict[str, Any], sites_to_insert: List[Dict[str, Any]]) -> None:
        """在 sites 数组的第二个位置插入新的站点信息"""
        if "sites" in data and isinstance(data["sites"], list):
            data["sites"][1:1] = sites_to_insert
            print(f"已插入 {len(sites_to_insert)} 个站点到sites数组的第二个位置")
        else:
            print("未找到有效的 'sites' 列表")

    @staticmethod
    def insert_single_site(
        data: Dict[str, Any],
        single_site: Dict[str, Any],
        insert_pos: int = 1
    ) -> bool:
        """
        单独插入一个站点到 sites 数组的指定位置
        :param data: 包含 sites 列表的原始数据字典
        :param single_site: 要插入的单个站点字典
        :param insert_pos: 插入位置（默认1，即第二个位置）
        :return: 是否插入成功
        """
        if "sites" not in data or not isinstance(data["sites"], list):
            print("未找到有效的 'sites' 列表，无法插入单个站点")
            return False
        
        if not isinstance(single_site, dict):
            print(f"插入失败：站点数据必须是字典，当前类型为 {type(single_site)}")
            return False
        
        data["sites"].insert(insert_pos, single_site)
        print(f"单个站点 '{single_site.get('name', '未知名称')}' 已插入到 sites 数组的第 {insert_pos + 1} 个位置")
        return True


class SiteFinder:
    """站点查找器，负责从URL列表中获取指定站点信息"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []  # 仅保留有用的结果存储属性
        self.http_utils = HttpUtils()

    def _process_single_url(self, url: str, target_names: List[str]) -> List[Dict[str, Any]]:
        """处理单个URL，提取符合条件的站点信息"""
        results = []
        
        if '#' in url:
            base_url, hash_str = url.split('#', 1)
            additional_fields = SiteProcessor.parse_hash_fields(hash_str)
        else:
            base_url = url
            additional_fields = {}
        
        print(f"正在从 {base_url} 读取数据...")
        response = self.http_utils.get(base_url)
        if not response:
            return results
            
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"无法解析 {base_url} 返回的JSON数据")
            return results
            
        if 'sites' in data and isinstance(data['sites'], list):
            for site in data['sites']:
                if 'name' in site and site['name'] in target_names:
                    site_copy = site.copy()
                    if additional_fields:
                        site_copy.update(additional_fields)
                    results.append(site_copy)
                    
        return results

    def get_sites_from_urls(self, urls: List[str], target_names: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
        """从多个URL并行读取JSON数据，根据URL中的哈希值添加字段"""
        self.results = []
        found_names = set()  # 用于去重，避免重复添加相同名称的站点
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self._process_single_url, url, target_names): url
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    sites = future.result()
                    for site in sites:
                        if site['name'] not in found_names:
                            found_names.add(site['name'])
                            self.results.append(site)
                except Exception as e:
                    print(f"处理 {url} 时发生意外错误: {str(e)}")
        
        for name in target_names:
            if name not in found_names:
                print(f"所有URL中均未找到名称为'{name}'的站点")
        
        return self.results

    def get_results(self) -> List[Dict[str, Any]]:
        return self.results
    
    def save_results_to_file(self, file_path: str) -> bool:
        return FileUtils.write_json(self.results, file_path)


def main():
    # 配置参数
    config = {
        "showdoc_push_url": os.getenv("SHOWDOC_PUSH_URL"),
        "pg_url": "https://www.252035.xyz/p/jsm.json",
        "filename": "jsm.json",
        "new_spider_value": "https://www.252035.xyz/p/pg.jar",
        "replacements": {
            "./lib/tokenm.json": "https://bp.banye.tech:7777/pg/lib/tokenm?token=qunyouyouqun",
            "./lib/": "https://www.252035.xyz/p/lib/"
        },
        "json_urls": [
            "https://bp.banye.tech:7777/sub/qunyouyouqun/pg"
        ],
        "site_names": [
            "AList",
            "TG123网盘","电报豆瓣", "电报搜索", "电报网页", 
            "账号更新", "TG豆瓣", "TG频道搜索", 
            "TG群组搜索"
        ]
    }

    # 初始化微信推送器并发送开始通知
    pusher = WechatPusher(config["showdoc_push_url"])
    pusher.send_text(
        content="程序已开始执行，正在下载必要文件",
        title="任务启动通知"
    )

    # 下载JSON文件
    http_utils = HttpUtils()
    download_success = http_utils.download_file(config["pg_url"], config["filename"])
    if not download_success:
        error_msg = "部分文件下载失败，请检查网络连接"
        print(error_msg)
        pusher.send_text(content=error_msg, title="下载错误通知")
        return

    # 读取并处理原始数据（替换spider值、字符串替换）
    original_data = FileUtils.read_json(config["filename"])
    if not original_data:
        error_msg = "无法继续处理，原始数据读取失败"
        print(error_msg)
        pusher.send_text(content=error_msg, title="数据处理错误")
        return
    print("原始数据加载完成")

    SiteProcessor.replace_spider_key(original_data, config["new_spider_value"])
    SiteProcessor.replace_string_in_dict(original_data, config["replacements"])

    # 从URL获取站点信息并保存中间结果
    finder = SiteFinder()
    new_sites = finder.get_sites_from_urls(config["json_urls"], config["site_names"])
    finder.save_results_to_file("banye.json")

    # 插入站点（批量插入+单独插入自定义站点）
    SiteProcessor.insert_sites(original_data, new_sites)
    emby_feiniu_site = {
        "ext": "eyJzZXJ2ZXIiOiAiaHR0cDovL215Z2Nucy5tb2JhaWVtYnkuc2l0ZTo3MDY5IiwidXNlcm5hbWUiOiAi6ZWc6Iqx5rC05pyIIiwicGFzc3dvcmQiOiAiMjA0MjE5ODE2Ny4uLiIsInVhIjogIllhbWJ5LzEuMC4yKEFuZHJvaWQpIiwiY29tbW9uQ29uZmlnIjogIiJ9",
        "filterable": 1,
        "quickSearch": 1,
        "name": "Emby墨云阁",
        "changeable": 0,
        "jar": "https://www.252035.xyz/z/custom_spider.jar",
        "api": "csp_Emby",
        "type": 3,
        "key": "墨云阁",
        "searchable": 1
    }
    
    
    
    SiteProcessor.insert_single_site(original_data, emby_feiniu_site, insert_pos=1)

    # 保存最终结果并发送通知
    save_success = FileUtils.write_json(original_data, config["filename"])
    if save_success:
        success_msg = (f"所有操作完成\n"
                      f"找到 {len(new_sites)} 个站点\n"
                      f"已保存到 {config['filename']}")
        pusher.send_text(content=success_msg, title="任务完成通知")
    else:
        error_msg = "保存文件失败，任务未完全完成"
        pusher.send_text(content=error_msg, title="任务失败通知")

    print("\n所有操作完成")


if __name__ == "__main__":
    main()

