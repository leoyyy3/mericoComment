"""
测试重复函数列表 API
用于验证 API 格式和响应
"""

import json
import requests


def test_duplicate_functions_api():
    """测试重复函数列表 API"""

    # API 配置
    API_URL = "https://merico.idc.hexun.com/buffet/re/quality/listFunctions"
    TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTg0ODc5NDEtNTYyMi00ODMxLWE5ZjItODJhZGUwNjhmZTQ4IiwiZGF0ZSI6MTc2NDcyNDc0ODUxNywiaWF0IjoxNzY0NzI0NzQ4LCJleHAiOjE4NjQ3MjQ3NDd9.xNfbWcVwWH1B4nc3XJ8nHjIKI0cUScR8VlYIpHnSitPQeV8iw2YYLtalpgoRSQZBK9ds9Nn9f8-y8NkcTXEc1-lfH8l1Bj0F8I2Nh_qrL3GG2EU1hggGUwoHVG5-wsJqpGX1sWB5ia22GDzo-xKpCfka8-8sQMXrcF3rJVNdr08"

    # 读取测试项目 ID
    with open("repoIds_simple.json", 'r') as f:
        repo_ids = json.load(f)

    test_repo_id = repo_ids[0]  # 使用第一个项目 ID 进行测试

    print("=" * 80)
    print("测试重复函数列表 API")
    print("=" * 80)
    print(f"\n测试项目 ID: {test_repo_id}")

    # 构建请求头
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    # 按照正确的格式构建请求体
    # params 数组第一个元素是 repo_id，第二个元素是参数对象
    payload = {
        "params": [
            test_repo_id,
            {
                "page": 1,
                "pageSize": 10,
                "sortField": "numFunctions",
                "sortOrder": "descend",
                "filter": {
                    "search": "",
                    "emails": [
                        "liuyang2020@staff.hexun.com"
                    ]
                }
            }
        ]
    }

    print("\n" + "-" * 80)
    print("请求信息:")
    print(f"URL: {API_URL}")
    print(f"请求体:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        print("\n" + "-" * 80)
        print("发送请求...")

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"响应状态码: {response.status_code}")

        response.raise_for_status()

        # 解析响应
        data = response.json()

        print("\n" + "-" * 80)
        print("请求成功!")
        print("\n响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 保存响应
        with open("test_duplicate_functions_response.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("\n" + "-" * 80)
        print("响应已保存到: test_duplicate_functions_response.json")

        # 分析响应结构
        print("\n" + "-" * 80)
        print("响应结构分析:")
        analyze_response(data)

        return True

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP 错误: {e}")
        print(f"响应内容: {response.text}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"\n请求错误: {e}")
        return False

    except Exception as e:
        print(f"\n未知错误: {e}")
        return False


def analyze_response(data, prefix=""):
    """分析响应数据结构"""
    if isinstance(data, dict):
        print(f"{prefix}类型: dict")
        print(f"{prefix}字段:")
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}  {key}: {type(value).__name__}")
                if isinstance(value, list) and len(value) > 0:
                    print(f"{prefix}    长度: {len(value)}")
                    print(f"{prefix}    第一个元素类型: {type(value[0]).__name__}")
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:50] + "..."
                print(f"{prefix}  {key}: {type(value).__name__} = {value_str}")

    elif isinstance(data, list):
        print(f"{prefix}类型: list")
        print(f"{prefix}长度: {len(data)}")
        if data:
            print(f"{prefix}第一个元素:")
            analyze_response(data[0], prefix + "  ")


if __name__ == "__main__":
    success = test_duplicate_functions_api()

    print("\n" + "=" * 80)
    if success:
        print("测试成功! 可以运行 fetch_duplicate_functions.py 获取所有项目数据")
    else:
        print("测试失败，请检查 API 配置和请求格式")
    print("=" * 80)
