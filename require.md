# Merico 项目重复函数列表获取需求

## 需求概述

根据 [repoIds_simple.json](file:///Users/leoyang/Documents/langchainAgents/mericoComment/repoIds_simple.json) 文件中的项目 ID，请求获取各项目的重复函数列表。

## API 接口详情

- **接口地址**: https://merico.idc.hexun.com/buffet/re/quality/listFunctions
- **请求方法**: POST
- **认证方式**: Bearer Token

## 请求参数

```json
{
  "id": "7e4dd753-ca72-4b51-a297-214c0f1b817c",
  "page": 1,
  "pageSize": 10,
  "filter": {
    "search": "",
    "emails": [
      "liuyang2020@staff.hexun.com"
    ]
  },
  "sort": {
    "field": "numFunctions",
    "direction": "desc"
  }
}
```

## 认证信息

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTg0ODc5NDEtNTYyMi00ODMxLWE5ZjItODJhZGUwNjhmZTQ4IiwiZGF0ZSI6MTc2NDcyNDc0ODUxNywiaWF0IjoxNzY0NzI0NzQ4LCJleHAiOjE4NjQ3MjQ3NDd9.xNfbWcVwWH1B4nc3XJ8nHjIKI0cUScR8VlYIpHnSitPQeV8iw2YYLtalpgoRSQZBK9ds9Nn9f8-y8NkcTXEc1-lfH8l1Bj0F8I2Nh_qrL3GG2EU1hggGUwoHVG5-wsJqpGX1sWB5ia22GDzo-xKpCfka8-8sQMXrcF3rJVNdr08
```

## 处理要求

1. 遍历 [repoIds_simple.json](file:///Users/leoyang/Documents/langchainAgents/mericoComment/repoIds_simple.json) 中的所有项目 ID
2. 向指定接口发起请求获取重复函数列表
3. 将结果以合适的方式展示给用户