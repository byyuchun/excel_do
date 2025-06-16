
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_drills.py

Usage:
    python import_drills.py \
        --excel /path/to/drills.xlsx \
        --sheet LOE-Base \
        --url http://localhost:6789/api/v4/drill_scene/create_drill \
        [--token YOUR_BEARER_TOKEN] \
        [--preview]
"""


# 数据格式：{"view_mode":"feature_tree","virtual_lark_tree_id":"1849021990216667344","virtual_team_tree_id":"1849021795747762428","submit_params":{"drill_type":1,"virtual_lark_tree_id":"1849021990216667344","virtual_team_tree_id":"1849021795747762428","drill_name":"测试传参格式","drill_scene_desc":"测试传参格式","drill_scene_priority":"P0","infra_type":["Abase"],"business_domain":["测试"],"tag":["测试"],"sub_business_domain":["测试"],"qa_manager":"gengao.0106","mttr":"undefined-undefined-undefined"}}
import argparse
import sys
import pandas as pd
import requests
import re
import json

virtual_lark_tree_id="1867116590202360264"
virtual_team_tree_id="1867116569771905229"
EXCEL_NAME="LOE-AI"
EXCEL_PATH = "/Users/bytedance/Downloads/演练库2.0_"+EXCEL_NAME+".xlsx"
SHEET_NAME = EXCEL_NAME
API_URL     = "https://ha-platform.bytedance.net/api/v4/drill_scene/create_drill"
TOKEN       = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2luZm8iOnsidXNlcm5hbWUiOiJnZW5nYW8uMDEwNiIsInBpY3R1cmUiOiJodHRwczovL3MxLWltZmlsZS5mZWlzaHVjZG4uY29tL3N0YXRpYy1yZXNvdXJjZS92MS92M18wMGxpXzYxOTYxMzFiLTNiZDYtNDAwNy1iY2U5LTVlNDE4NjIzNDM1Z34_aW1hZ2Vfc2l6ZT1ub29wXHUwMDI2Y3V0X3R5cGU9XHUwMDI2cXVhbGl0eT1cdTAwMjZmb3JtYXQ9cG5nXHUwMDI2c3RpY2tlcl9mb3JtYXQ9LndlYnAiLCJuYW1lIjoiZ2VuZ2FvLjAxMDYiLCJuaWNrbmFtZSI6Imdlbmdhby4wMTA2IiwiaWQiOjAsImVtYWlsIjoiZ2VuZ2FvLjAxMDZAYnl0ZWRhbmNlLmNvbSIsImlzX2FkbWluIjowfSwiZXhwIjoxNzc2ODM5MDA2LCJpc3MiOiJteS1wcm9qZWN0In0.1BTkiPuoHavFzG58aU_dG4GaK7mOQTN1sAZUeIJzZNM"
# —— 把 Excel 列映射到 submit_params 的字段 ——
field_map = {
    "drill_name":           "场景new",
    "drill_desc":           "风险描述",
    "drill_status_msg":      "风险状态",
    # 原子演练场景字段（可选）
    "risk_type":            "风险类型",
    "sub_risk_type":        "风险子项",
    "drill_scene_desc":     "drill_scene_desc",
    "drill_scene_priority": "drill_scene_priority",
    # "entrance_psm":         "entrance_psm",//可以不要
    # "entrance_method":      "entrance_method",
    "business_domain":      "业务域",
    "sub_business_domain":  "子模块",
    "qa_manager":           "qa_manager",
    "infra_type":           "基建类型",
    "tag":                  "",
    "drill_status_msg":     "计划演练季度",
}

# —— 后端必填项及其默认值 ——
required_defaults = {
    # 基本信息
    "drill_name":               "",              # 必填，Excel 中一定得有
    "drill_type":               1,               # 默认原子演练
    "drill_camp_id":            "006",           # 演练活动是006 原子演练
    # 演练环境
    # "drill_env_type":           0,               # 默认 pre_release
    # "drill_cluster":            "lane-lark-drill",
    # "drill_status_msg":         "新创建",
    # MTTR
    # "mttr":                     "5-10-15",
    # 应急信息
    # "emergency_platform_type":  0,
    # "emergency_business":       "测试boe",
    # "emergency_unit":           "boe",
    # "emergency_level":          1,
    # "emergency_desc":           "这是备注信息",
    # "emergency_group_member":   ["zhoufachao"],
    # 原子演练额外字段（drill_type=1 时）
    "drill_scene_desc":         "暂无待添加",
    "drill_scene_priority":     "P1",
    # "entrance_psm":             "default_psm",
    # "entrance_method":          "http",
    "infra_type":                "暂无待添加",
    "business_domain":           "暂无待添加",
    "sub_business_domain":       "暂无待添加",
    "qa_manager":               "gengao.0106",
    # 风险数组字段，保证 key 存在
    "risk_type":                "[]",
    "sub_risk_type":            "[]",
}



def parse_array(val):
    """Parse JSON-array or split on comma/中文逗号/斜杠。
    如果拆分后只有一个元素且该元素包含空格，则按空格再拆分并排序（例如 "Mysql MQ" -> ["MQ", "Mysql"]）。"""
    if isinstance(val, list):
        return val
    if not isinstance(val, str):
        return []

    s = val.strip()
    # 如果是 JSON-array 字符串，优先尝试 json.loads
    if s.startswith('[') and s.endswith(']'):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass

    # 先按逗号/中文逗号/斜杠拆分
    parts = re.split(r'[,，/／]+', s)
    # 如果拆分后只有一个元素，且该元素中包含空格，就再按空格拆分，并按字母顺序排序
    if len(parts) == 1 and " " in parts[0]:
        subparts = parts[0].split()
        return sorted([p.strip() for p in subparts if p.strip()])

    # 其他情况下，去除空白后直接返回拆分结果
    return [p.strip() for p in parts if p.strip()]

def parse_array1(val):
    """Parse JSON-array or split on comma/中文逗号/斜杠."""
    if isinstance(val, list):
        return val
    if not isinstance(val, str):
        return []
    s = val.strip()
    if s.startswith('[') and s.endswith(']'):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    parts = re.split(r'[,，/／]+', s)
    return [p.strip() for p in parts if p.strip()]

def main():
    headers = {
        "Content-Type": "application/json",
        "Authorization": TOKEN,
        "accept-language":"zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7,ja;q=0.6"

    }
    # 读取 Excel
    try:
        df = pd.read_excel(EXCEL_PATH,
                           sheet_name=SHEET_NAME,
                           dtype=str,
                           keep_default_na=False)
    except Exception as e:
        print(f"Error reading Excel '{EXCEL_PATH}': {e}", file=sys.stderr)
        sys.exit(1)

    # 补齐 required_defaults 中提到的列：如果 Excel 没这一列，
    # 或者单元格空，就先插入默认值，方便后面 mapping
    for key, default in required_defaults.items():
        col = field_map.get(key, key)  # 如果 mapping 中没有，Excel 列名就等于字段名
        if col not in df.columns:
            df[col] = str(default)
        else:
            df[col] = df[col].replace(["", None], str(default))

    array_fields = ["risk_type", "sub_risk_type","infra_type","business_domain","sub_business_domain"]

    for idx, row in df.iterrows():
        # 1) 构造 submit_params
        submit_params = {}
        for key, col in field_map.items():
            submit_params[key] = row.get(col, "")

        # 2) 再补齐所有 required_defaults
        for key, default in required_defaults.items():
            if key not in submit_params or submit_params[key] in ("", None):
                submit_params[key] = default

        # 3) 数组字段 parse
        for f in array_fields:
            submit_params[f] = parse_array(submit_params[f])

        # 4) 构造完整 payload
        payload = {
            "view_mode":             "feature_tree",
            "virtual_lark_tree_id":  row.get("virtual_lark_tree_id", virtual_lark_tree_id),
            "virtual_team_tree_id":  row.get("virtual_team_tree_id", virtual_team_tree_id),
            "submit_params":         submit_params,
        }

        # 5) 打印 & 预览
        print(payload)
        print(f"\n--- Row {idx} payload ---")
        print(json.dumps(payload, ensure_ascii=False, indent=2))



        # 6) 发送请求
        try:
            print("▶▶▶ 请求 URL:", API_URL)
            print("▶▶▶ 请求 headers:", headers)
            print(payload)

            resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            body = resp.json()
            if body.get("code", 0) == 0:
                print(f"[{idx}] 导入成功: {body.get('data')}")
            else:
                print(f"[{idx}] 接口错误: {body}", file=sys.stderr)
        except Exception as exc:
            print(f"[{idx}] 请求失败: {exc}", file=sys.stderr)

    print("全部完成。")

if __name__ == "__main__":
    main()
