"""
测试脚本 - 用于测试单个项目的 API 请求
快速验证 API 是否正常工作
"""

import json
import requests


def test_single_request():
    """测试单个项目的请求"""

    # 配置
    API_URL = "https://merico.idc.hexun.com/buffet/re/quality/listFunctions"
    TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTg0ODc5NDEtNTYyMi00ODMxLWE5ZjItODJhZGUwNjhmZTQ4IiwiZGF0ZSI6MTc2NDcyNDc0ODUxNywiaWF0IjoxNzY0NzI0NzQ4LCJleHAiOjE4NjQ3MjQ3NDd9.xNfbWcVwWH1B4nc3XJ8nHjIKI0cUScR8VlYIpHnSitPQeV8iw2YYLtalpgoRSQZBK9ds9Nn9f8-y8NkcTXEc1-lfH8l1Bj0F8I2Nh_qrL3GG2EU1hggGUwoHVG5-wsJqpGX1sWB5ia22GDzo-xKpCfka8-8sQMXrcF3rJVNdr08"

    # 从文件读取第一个项目 ID
    with open("repoIds_simple.json", 'r') as f:
        repo_ids = json.load(f)

    test_repo_id = repo_ids[0]
    print(f"测试项目 ID: {test_repo_id}")
    print("-" * 80)

    # 构建请求
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "params": [
            test_repo_id,
            {
                "page": 1,
                "pageSize": 10,
                "sortField": "cyclomatic",
                "sortOrder": "descend",
                "location": "",
                "frequentAuthors": [
                    "liuyang2020@staff.hexun.com"
                ],
                "cyclomatic": {
                    "min": 0,
                    "max": None
                },
                "isDocCovered": False
            }
        ]
    }

    print("发送请求...")
    print(f"URL: {API_URL}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 80)

    try:
        # 发送请求
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"状态码: {response.status_code}")
        print("-" * 80)

        # 检查响应
        response.raise_for_status()

        # 解析 JSON
        data = response.json()

        print("请求成功!")
        print("响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 保存响应用于分析
        with open("test_response.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("-" * 80)
        print("响应已保存到 test_response.json")

        # 简单分析响应结构
        print("-" * 80)
        print("响应结构分析:")
        analyze_structure(data)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP 错误: {e}")
        print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


def analyze_structure(data, prefix=""):
    """递归分析数据结构"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}: {type(value).__name__}")
                analyze_structure(value, prefix + "  ")
            else:
                print(f"{prefix}{key}: {type(value).__name__} = {value}")
    elif isinstance(data, list):
        print(f"{prefix}[列表, 长度: {len(data)}]")
        if data and len(data) > 0:
            print(f"{prefix}第一个元素:")
            analyze_structure(data[0], prefix + "  ")


if __name__ == "__main__":
    test_single_request()
