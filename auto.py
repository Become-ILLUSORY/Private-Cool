import requests
import json

def download_json_file(url, filename):
    """从指定URL下载JSON文件并保存到本地"""
    response = requests.get(url)
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

def insert_sites(data, spider_value):
    """在 sites 数组的第二个位置插入新的站点信息"""
    new_sites = [
        {
            "key": "Wexconfig",
            "name": "🐮配置┃中心🐮",
            "type": 3,
            "jar": spider_value,
            "api": "csp_WexconfigGuard"
        },
        {
            "key": "Wexemby",
            "name": "emby",
            "type": 3,
            "jar": spider_value,
            "api": "csp_WexembyGuard",
            "searchable": 1,
            "changeable": 1
        },
        {
            "key": "WexbaidusoGuard",
            "name": "百度",
            "type": 3,
            "jar": spider_value,
            "api": "csp_WexbaidusoGuard",
            "searchable": 1,
            "changeable": 0
        }
    ]
    
    if "sites" in data and isinstance(data["sites"], list):
        # 在索引1的位置插入新的站点信息
        data["sites"][1:1] = new_sites
    else:
        print("未找到有效的 'sites' 列表")

def main():
    pg_url = "https://www.252035.xyz/p/jsm.json"
    filename = "jsm.json"
    
    emby_url = "https://fs-im-kefu.7moor-fs1.com/ly/4d2c3f00-7d4c-11e5-af15-41bf63ae4ea0/1753376903377/wex.json"
    emby_filename = "wex.json"
    
    new_spider_value = "https://www.252035.xyz/p/pg.jar"
    
    replacements = {
        "./lib/tokenm.json": "https://bp.banye.tech:7777/pg/lib/tokenm?token=qunyouyouqun",
        "./lib/": "https://www.252035.xyz/p/lib/"
    }
    

    # 下载并保存JSON文件
    download_json_file(pg_url, filename)
    download_json_file(emby_url, emby_filename)

    # 读取原始数据
    original_data = read_json_file(filename)
    print("原始数据:")
    print(json.dumps(original_data, indent=4))

    # 替换键为'spider'的值
    replace_spider_key(original_data, new_spider_value)

    # 替换字符串
    replace_string_in_dict(original_data, replacements)

    # 提取 wex.json 中的 'spider' 值
    emby_data = read_json_file(emby_filename)
    spider_value = find_spider_value(emby_data)
    print("\n键为 'spider' 的值 (emby JSON):")
    print(spider_value)

    # 在 jsm.json 的 sites 数组的第二个位置插入新的站点信息
    insert_sites(original_data, spider_value)

    # 写回修改后的内容到本地文件
    write_json_file(original_data, filename)

    # 打印修改后的数据
    print("\n修改后的数据:")
    print(json.dumps(original_data, indent=4))

if __name__ == "__main__":
    main()



