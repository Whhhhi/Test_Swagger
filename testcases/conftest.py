"""
Pytest 全局 Fixture 定义

提供：
- env_config       — 加载 env.yaml 环境配置
- api_key          — API Key 注入（环境变量优先）
- request_client   — 已注入认证信息的 HTTP 客户端
- pet_api          — Pet API 操作对象
- new_pet_id       — 每次测试生成一个唯一 ID
- created_pet_id   — 创建一只可供查询/更新/删除的 Pet
- nonexistent_id   — 保证不存在的 Pet ID
"""

import os
import time
from pathlib import Path

import pytest
import yaml

from api.pet_api import PetApi
from common.logger import log, setup_logger
from common.request_client import RequestClient


# ============================================================
# Session 级别 Fixture
# ============================================================


@pytest.fixture(scope="session", autouse=True)
def session_init(env_config):
    """Session 级初始化：配置日志"""
    log_level = env_config.get("log_level", "DEBUG")
    log_retention = env_config.get("log_retention", "7 days")
    setup_logger(log_level=log_level, log_retention=log_retention)
    log.info("=" * 60)
    log.info("Petstore API 自动化测试 — 启动")
    log.info("环境: {}", env_config.get("env", "unknown"))
    log.info("Base URL: {}", env_config.get("base_url"))
    log.info("=" * 60)
    yield
    log.info("=" * 60)
    log.info("Petstore API 自动化测试 — 结束")
    log.info("=" * 60)


@pytest.fixture(scope="session")
def env_config():
    """加载 config/env.yaml 环境配置"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "env.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["base"]


@pytest.fixture(scope="session")
def api_key(env_config) -> str:
    """获取 API Key

    优先级: 环境变量 PETSTORE_API_KEY > env.yaml 中的 api_key
    """
    return os.environ.get("PETSTORE_API_KEY") or env_config.get("api_key", "special-key")


@pytest.fixture(scope="session")
def request_client(env_config, api_key) -> RequestClient:
    """创建已注入 API Key 的 HTTP 客户端"""
    default_headers = env_config.get("default_headers", {}).copy()
    # 注入 API Key 认证 Header
    default_headers["api_key"] = api_key

    client = RequestClient(
        base_url=env_config["base_url"],
        default_headers=default_headers,
        timeout=env_config.get("timeout", 10),
    )
    log.info("HTTP 客户端初始化完成 (base_url={})", env_config["base_url"])
    return client


@pytest.fixture(scope="session")
def pet_api(request_client) -> PetApi:
    """Pet API 操作对象"""
    return PetApi(request_client)


# ============================================================
# Function 级别 Fixture
# ============================================================


@pytest.fixture(scope="function")
def new_pet_id() -> int:
    """生成一个唯一的 Pet ID（基于时间戳）"""
    pet_id = int(time.time() * 1_000_000) % 100_000_000
    log.debug("生成新 Pet ID: {}", pet_id)
    return pet_id


@pytest.fixture(scope="function")
def nonexistent_id() -> int:
    """返回一个保证不存在的 Pet ID"""
    return 999_999_999


@pytest.fixture(scope="function")
def created_pet_id(pet_api, request) -> int:
    """创建一只 Pet 并返回其 ID

    供 GET / PUT / DELETE 测试作为前置数据使用。
    测试完成后自动清理该 Pet。
    """
    # 生成唯一 ID
    pet_id = int(time.time() * 1_000_000) % 100_000_000

    payload = {
        "id": pet_id,
        "name": f"TestPet-{pet_id % 10000}",
        "photoUrls": ["https://example.com/pet.jpg"],
        "status": "available",
    }

    resp = pet_api.create_pet(payload)
    if resp.status_code == 200:
        created_id = resp.json().get("id", pet_id)
        log.info("前置 Pet 创建成功: ID={}", created_id)
    else:
        created_id = pet_id
        log.warning("前置 Pet 创建返回 {}，使用生成 ID: {}", resp.status_code, created_id)

    yield created_id

    # Teardown: 清理测试数据
    delete_resp = pet_api.delete_pet(created_id)
    if delete_resp.status_code == 200:
        log.info("Teardown: 清理 Pet ID={} 成功", created_id)
    else:
        log.info("Teardown: 清理 Pet ID={} (无需清理: {})", created_id, delete_resp.status_code)


# ============================================================
# YAML 测试数据加载工具
# ============================================================


def load_test_cases(yaml_file: str) -> list[dict]:
    """从 data/testcases/ 目录加载 YAML 测试用例

    Args:
        yaml_file: YAML 文件名（如 test_create_pet.yaml）

    Returns:
        测试用例列表（每个 case 为一个 dict）
    """
    data_path = Path(__file__).resolve().parent.parent / "data" / "testcases" / yaml_file
    if not data_path.exists():
        raise FileNotFoundError(f"测试数据文件不存在: {data_path}")

    with open(data_path, encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    if not cases:
        return []

    log.info("加载测试数据: {} ({} 条用例)", yaml_file, len(cases))
    return cases


def resolve_template(data, context: dict):
    """递归替换数据结构中的 {placeholder} 模板变量

    Args:
        data: 任意类型的数据（dict, list, str 等）
        context: 变量名到值的映射字典

    Returns:
        替换后的数据
    """
    if isinstance(data, dict):
        return {k: resolve_template(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_template(item, context) for item in data]
    elif isinstance(data, str):
        # 纯变量替换: "{new_pet_id}" → 值（不转换类型）
        if data.startswith("{") and data.endswith("}") and " " not in data:
            key = data.strip("{}")
            if key in context:
                return context[key]
        # 带前缀/后缀的字符串模板替换: "/pet/{pet_id}" → "/pet/12345"
        import re

        def _replacer(match):
            key = match.group(1)
            return str(context.get(key, match.group(0)))

        return re.sub(r"\{(\w+)\}", _replacer, data)
    return data
