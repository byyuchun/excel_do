# 🚀 Drill Scene Import Tool

本工具用于 **批量导入演练场景（Drill Scene）** 到指定平台接口。它可以从 Excel 文件读取演练场景数据，并通过 API 自动提交。

---

## 📦 功能特性

- 从 Excel 中读取指定 Sheet 的数据
- 支持字段映射与格式转换
- 自动填充默认值（如未在 Excel 中提供）
- 支持数组字段的智能拆分（如用逗号、斜杠、空格分隔）
- 支持 Bearer Token 身份认证
- 可打印请求结构，方便调试与预览

---

## 🛠️ 环境依赖

- Python 3.x
- 依赖库安装：

```bash
pip install pandas requests openpyxl

