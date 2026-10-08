# 🐶 Petstore API 自动化测试框架

> 基于 Python + pytest + Allure 的 Swagger Petstore 接口自动化测试项目
> 被测地址：`https://petstore.swagger.io/v2`

[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/pytest-7%2B-orange)](https://docs.pytest.org/)

---

## 📋 项目概览

对 Swagger 官方 Petstore API（v2）进行全面的接口自动化测试，涵盖完整 CRUD 业务流和各类异常场景。

## 🏗️ 项目结构

```
Test_Swagger/
├── .github/workflows/ci.yml     # GitHub Actions CI 流水线
├── config/env.yaml              # 环境配置（URL、认证、超时、日志）
├── common/                      # 通用组件层
│   ├── logger.py                # Loguru 日志封装（文件+控制台+脱敏）
│   ├── request_client.py        # HTTP 客户端（Session + Retry + Allure 附件）
│   └── assertion.py             # 断言工具（状态码 / 字段值 / 嵌套路径）
├── api/pet_api.py               # API 对象层（Pet CRUD 封装）
├── data/testcases/*.yaml        # 数据驱动用例（正向 + 反向）
├── testcases/
│   ├── conftest.py              # Fixture 注册 + YAML 加载 + 模板解析
│   └── test_pet_store.py        # 测试执行层（CRUD 测试类 + 完整业务流）
├── pytest.ini                   # Pytest 配置（markers / addopts）
├── requirements.txt             # Python 依赖
└── README.md
```

## 🧱 框架分层

```
测试层 (test_pet_store.py + YAML 用例)
        ↑
API 对象层 (PetApi)
        ↑
Client 层 (RequestClient + Logger + Assertion)
        ↑
配置层 (env.yaml)
```

| 层级 | 职责 | 核心文件 |
|------|------|----------|
| config | 环境配置管理 | `env.yaml` |
| common | HTTP 客户端 / 日志 / 断言 | `request_client.py`, `logger.py`, `assertion.py` |
| api | 接口对象封装 | `pet_api.py` |
| data | YAML 数据驱动用例 | `data/testcases/*.yaml` |
| testcases | 测试执行层 + Fixture | `test_pet_store.py`, `conftest.py` |

## 🧪 测试覆盖

### 正向用例（Happy Path）

- 携带完整字段创建 Pet
- 仅必填字段创建 Pet
- 通过有效 ID 查询 Pet
- 更新 Pet 并回查验证持久化
- 删除 Pet 后查询确认 404
- **完整业务流**：创建 → 查询 → 更新 → 查询 → 删除 → 查询

### 反向用例（Negative / Edge Cases）

- 缺失必填字段 `name`
- 空请求体
- 重复创建相同 ID
- 字段类型错误（name 传数字）
- 查询不存在的 ID
- 非法 ID 格式（负数 / 字符串 / 特殊字符）
- 更新不存在的 Pet
- 删除不存在的 Pet
- 重复删除（删除两次）

---

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.11+
python -m venv venv
# Linux / Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行全部用例
pytest

# 仅冒烟测试
pytest -m smoke

# 仅反向用例
pytest -m negative

# 带 Allure 结果输出
pytest --alluredir=./allure-results

# 生成 HTML 报告
allure generate ./allure-results -o ./allure-report --clean
allure open ./allure-report
```

### 3. 环境配置

编辑 `config/env.yaml`：

```yaml
base:
  env: test
  base_url: https://petstore.swagger.io/v2
  api_key: special-key
  timeout: 10
  log_level: DEBUG
  allure_report_dir: "./allure-results"
```

> API Key 也可通过环境变量 `PETSTORE_API_KEY` 注入（优先级高于配置文件）。

---

## 🤖 CI / CD

每次 push / PR 到 `main` 或 `master` 分支，GitHub Actions 自动执行：

```
lint (ruff) → test (Python 3.11 × 3.12 矩阵, pytest-xdist) → publish (Allure 报告部署到 GitHub Pages)
```

流水线配置见 `.github/workflows/ci.yml`。Allure 报告发布到 `https://<username>.github.io/<repo>/`。

---

## 🧩 核心设计

### 数据驱动

所有用例从 `data/testcases/*.yaml` 加载，支持模板变量替换（如 `{new_pet_id}`、`{pet_id}`）。新增用例只需加 YAML，无需改测试代码。

### Fixture 依赖注入链

```
env_config → api_key → request_client → pet_api → created_pet_id
                                         → new_pet_id
                                         → nonexistent_id
```

`created_pet_id` fixture 自动在测试前创建 Pet、测试后清理（yield + teardown），保证每条用例独立。

### HTTP 客户端特性

- 基于 `requests.Session` + `HTTPAdapter` 连接池复用
- 内置 `urllib3` Retry 策略（5xx 自动重试 2 次）
- 请求 / 响应自动脱敏记录到 Allure（api_key 显示为 `***`）
- 统一异常分类（Timeout / ConnectionError / RequestException）

### 断言策略

| 维度 | 方式 |
|------|------|
| HTTP 状态码 | `verify_status_code` |
| 响应体字段值 | `verify_json_fields`（支持嵌套路径 `category.name`） |
| 字段存在性 | `verify_field_exists` |
| 数组校验 | `verify_array_non_empty` |

---

## 📄 依赖清单

| 包 | 版本 | 用途 |
|----|------|------|
| pytest | ≥7.4.0 | 测试框架 |
| pytest-xdist | ≥3.3.0 | 并发执行 |
| requests | ≥2.31.0 | HTTP 客户端 |
| PyYAML | ≥6.0 | YAML 数据解析 |
| allure-pytest | ≥2.13.0 | 测试报告 |
| loguru | ≥0.7.0 | 日志管理 |

## 🔧 扩展指南

1. **新增接口**：在 `api/` 下新建 `xxx_api.py`，组合 `RequestClient` 封装接口方法
2. **新增用例**：在 `data/testcases/` 下新建 YAML，字段遵循现有 schema
3. **新增测试类**：在 `testcases/` 下 `@pytest.mark.parametrize` 绑定 YAML 用例

---

## 📜 License

MIT
