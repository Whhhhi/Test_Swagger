# 🐶 Petstore API 自动化测试框架

> 基于 Python + pytest + Allure 的 Swagger Petstore 接口自动化测试项目
>
> 🎯 **面试指南**：[INTERVIEW_GUIDE.md](./INTERVIEW_GUIDE.md) — 包含测试概念速通、项目架构解读、面试 TOP 20 问答，适合有 Python 开发基础但缺乏测试经验的同学。

---

## 📋 项目概览

对 Swagger 官方 Petstore API（v2）进行全面的接口自动化测试，涵盖正向业务流和各类异常场景。

**被测地址:** `https://petstore.swagger.io/v2`

---

## 🏗️ 项目结构

```
Test_Swagger/
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── pytest.ini                   # Pytest 配置
│
├── config/                      # 环境与全局配置层
│   ├── __init__.py
│   └── env.yaml                 # 环境配置（URL、认证、超时等）
│
├── common/                      # 通用工具层
│   ├── __init__.py
│   ├── logger.py                # 日志封装（Loguru）
│   ├── request_client.py        # HTTP 请求客户端封装
│   └── assertion.py             # 断言工具方法
│
├── api/                         # API 对象层
│   ├── __init__.py
│   └── pet_api.py               # Pet 相关接口封装
│
├── data/                        # 测试数据层
│   ├── __init__.py
│   └── testcases/               # YAML 数据驱动用例
│       ├── test_create_pet.yaml  # 创建 Pet 用例
│       ├── test_get_pet.yaml     # 查询 Pet 用例
│       ├── test_update_pet.yaml  # 更新 Pet 用例
│       └── test_delete_pet.yaml  # 删除 Pet 用例
│
└── testcases/                   # 测试用例执行层
    ├── __init__.py
    ├── conftest.py              # Fixture（API Key 注入、环境加载）
    └── test_pet_store.py        # Pet 业务流主测试类
```

---

## 🧱 框架分层

| 层级 | 职责 | 核心文件 |
|------|------|----------|
| **config** | 环境配置管理 | `env.yaml` |
| **common** | 通用组件（HTTP 客户端、日志、断言） | `request_client.py`, `logger.py`, `assertion.py` |
| **api** | 接口对象封装 | `pet_api.py` |
| **data** | YAML 数据驱动用例 | `data/testcases/*.yaml` |
| **testcases** | 测试执行层 | `test_pet_store.py`, `conftest.py` |

---

## 🔄 核心业务流

```
创建 Pet (POST /pet)
    → 通过 ID 查询 (GET /pet/{petId})
        → 更新 Pet (PUT /pet)
            → 删除 Pet (DELETE /pet/{petId})
```

其中每个步骤均覆盖 **正向** 与 **反向** 用例。

---

## 🧪 测试覆盖

### 正向用例（Happy Path）
| 场景 | 说明 |
|------|------|
| `test_create_pet_full_fields` | 携带完整必填字段创建 Pet |
| `test_get_pet_by_id` | 通过有效 ID 查询 Pet |
| `test_update_pet_name` | 更新 Pet 名称 |
| `test_delete_pet` | 删除已存在的 Pet |
| `test_full_business_flow` | 完整业务流：创建 → 查询 → 更新 → 删除 |

### 反向用例（Negative / Edge Cases）
| 场景 | 说明 | 预期 |
|------|------|------|
| `test_create_pet_missing_required` | 缺失必填字段 `name` | 400 / 500 |
| `test_create_pet_duplicate_id` | 重复创建相同 ID | 405 / 500 |
| `test_get_pet_invalid_id` | 非法 ID 格式（字符串） | 404 |
| `test_get_pet_nonexistent` | 查询不存在的 ID | 404 |
| `test_update_pet_nonexistent` | 更新不存在的 Pet | 404 |
| `test_delete_pet_nonexistent` | 删除不存在的 Pet | 404 |
| `test_delete_pet_invalid_id` | 非法 ID 格式删除 | 404 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.10+
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行全部用例
pytest

# 运行带 Allure 报告的用例
pytest --alluredir=./allure-results

# 生成并查看 Allure 报告
allure generate ./allure-results -o ./allure-report --clean
allure open ./allure-report
```

### 3. 环境配置

编辑 `config/env.yaml` 修改目标环境：

```yaml
base:
  env: test
  base_url: https://petstore.swagger.io/v2
  api_key: special-key          # Swagger 官方 Demo Key
  timeout: 10
  log_level: DEBUG
```

> **注意:** Petstore API 的 `api_key` 在 Header 中传递，Swagger 官方 Demo Key 为 `special-key`。
> 生产环境请替换为真实 API Key 并通过环境变量注入。

---

## 📊 测试报告

- **Allure 报告:** 提供直观的测试结果看板
- **Loguru 日志:** `logs/petstore_{time}.log` — 自动轮转、按天归档
- **控制台输出:** pytest 原生 + Allure 步骤展示

---

## ✅ 断言策略

| 维度 | 方式 |
|------|------|
| HTTP 状态码 | `assert response.status_code == expected` |
| 响应体字段 | YAML 中声明 `expected_body_fields`，框架递归校验 |
| 业务逻辑 | 创建后反查 ID 一致性；删除后查询确认 404 |
| 类型校验 | 隐式：返回 JSON 类型与字段存在性 |

---

## 📄 依赖清单

| 包 | 用途 |
|----|------|
| pytest | 测试框架 |
| requests | HTTP 客户端 |
| PyYAML | YAML 解析 |
| allure-pytest | 测试报告 |
| loguru | 日志管理 |

---

## 🔧 扩展指南

1. **新增接口:** 在 `api/` 下新建 `xxx_api.py`，继承或直接封装 HTTP 方法
2. **新增用例:** 在 `data/testcases/` 下新建 YAML 文件，在 `testcases/` 下绑定测试方法
3. **新增环境:** 在 `env.yaml` 的 `base` 下新增字段，通过 `conftest.py` 的 `env_config` fixture 注入

---

*Generated for Swagger Petstore API Testing — 2026*
