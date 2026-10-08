"""
Petstore API 核心测试

测试覆盖:
  - 创建 Pet   → POST /pet
  - 查询 Pet   → GET  /pet/{petId}
  - 更新 Pet   → PUT  /pet
  - 删除 Pet   → DELETE /pet/{petId}
  - 完整业务流 → Create → Get → Update → Delete

数据驱动:
  所有正向/反向用例均从 data/testcases/*.yaml 加载
"""

import json
from copy import deepcopy

import allure
import pytest

from common.assertion import (
    verify_status_code,
    verify_json_fields,
    verify_field_exists,
)
from common.logger import log
from testcases.conftest import load_test_cases, resolve_template

# ============================================================
# Helpers
# ============================================================


def _log_case(case: dict, context: dict) -> None:
    """记录用例信息到 Allure（不执行请求）"""
    resolved = resolve_template(deepcopy(case), context)
    allure.dynamic.title(case.get("title", "未命名用例"))
    allure.attach(
        name="📋 用例信息",
        body=(
            f"**Method:** {case.get('method')}\n\n"
            f"**Path:** {case.get('path')}\n\n"
            f"**Expected Status:** {case.get('expected_status')}\n\n"
            f"**Resolved Payload:**\n```json\n"
            f"{json.dumps(resolved.get('payload'), indent=2, ensure_ascii=False) if resolved.get('payload') else 'N/A'}\n"
            f"```"
        ),
        attachment_type=allure.attachment_type.TEXT,
    )


def _execute_and_assert(
    pet_api,
    case: dict,
    context: dict,
) -> None:
    """解析模板 → 发送请求 → 断言

    Args:
        pet_api: PetApi 实例
        case: 原始 YAML 用例 dict
        context: 模板变量上下文
    """
    resolved = resolve_template(deepcopy(case), context)

    method = resolved["method"]
    path = resolved["path"]
    payload = resolved.get("payload")
    headers = resolved.get("headers")
    expected_status = resolved["expected_status"]
    expected_fields = resolved.get("expected_body_fields", {})

    # 根据 method 调用对应 API
    _method_dispatch = {
        "POST": lambda: pet_api.create_pet(payload, headers=headers),
        "GET": lambda: pet_api.get_pet_by_id(
            path.rstrip("/").rsplit("/", 1)[-1], headers=headers
        ),
        "PUT": lambda: pet_api.update_pet(payload, headers=headers),
        "DELETE": lambda: pet_api.delete_pet(
            path.rstrip("/").rsplit("/", 1)[-1], headers=headers
        ),
    }

    caller = _method_dispatch.get(method)
    if caller is None:
        pytest.fail(f"不支持的 HTTP 方法: {method}")

    response = caller()

    # 断言状态码
    verify_status_code(response.status_code, expected_status)

    # 断言响应体字段
    if expected_fields:
        try:
            resp_json = response.json()
            verify_json_fields(resp_json, expected_fields)
        except (json.JSONDecodeError, ValueError) as e:
            log.warning("响应体非 JSON，跳过字段断言: {}", e)

    # 额外日志
    log.info(
        "[PASS] {} {} → {} | {}",
        method,
        path,
        response.status_code,
        case.get("title", ""),
    )


# ============================================================
# 1. 创建 Pet
# ============================================================


@allure.epic("Petstore API")
@allure.feature("创建 Pet")
class TestCreatePet:
    """创建 Pet — POST /pet"""

    @allure.story("正向用例")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.positive
    @pytest.mark.parametrize("case", load_test_cases("test_create_pet.yaml"))
    def test_create_pet(self, case, pet_api, new_pet_id, request):
        """数据驱动：创建 Pet"""
        _log_case(case, {"new_pet_id": new_pet_id})

        # 处理特殊场景：重复创建
        if case.get("run_mode") == "duplicate":
            # 先成功创建一次
            first_payload = resolve_template(deepcopy(case["payload"]), {"new_pet_id": new_pet_id})
            resp1 = pet_api.create_pet(first_payload)
            log.info("首次创建状态码: {} (用于重复测试)", resp1.status_code)
            # 第二次创建（期望 405）
            _execute_and_assert(pet_api, case, {"new_pet_id": new_pet_id})
        else:
            _execute_and_assert(pet_api, case, {"new_pet_id": new_pet_id})

    @allure.story("正向用例")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_create_pet_minimal(self, pet_api, new_pet_id):
        """最简正向 — 仅 id + name + photoUrls"""
        payload = {
            "id": new_pet_id,
            "name": "MinimalPet",
            "photoUrls": [],
        }
        resp = pet_api.create_pet(payload)
        verify_status_code(resp.status_code, 200)
        resp_json = resp.json()
        verify_field_exists(resp_json, "id")
        verify_json_fields(resp_json, {"name": "MinimalPet"})


# ============================================================
# 2. 查询 Pet
# ============================================================


@allure.epic("Petstore API")
@allure.feature("查询 Pet")
class TestGetPet:
    """查询 Pet — GET /pet/{petId}"""

    @allure.story("正向/反向用例")
    @pytest.mark.parametrize("case", load_test_cases("test_get_pet.yaml"))
    def test_get_pet(self, case, pet_api, created_pet_id, nonexistent_id):
        """数据驱动：查询 Pet"""
        context = {
            "pet_id": created_pet_id,
            "nonexistent_id": nonexistent_id,
        }
        _log_case(case, context)
        _execute_and_assert(pet_api, case, context)

    @allure.story("正向用例")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_get_created_pet_verify_all_fields(self, pet_api, created_pet_id):
        """查询已创建的 Pet 并验证完整字段结构"""
        resp = pet_api.get_pet_by_id(created_pet_id)
        verify_status_code(resp.status_code, 200)

        body = resp.json()
        verify_field_exists(body, "id")
        verify_field_exists(body, "name")
        verify_field_exists(body, "photoUrls")
        log.info("Pet ID={} 查询成功，包含完整字段结构", created_pet_id)


# ============================================================
# 3. 更新 Pet
# ============================================================


@allure.epic("Petstore API")
@allure.feature("更新 Pet")
class TestUpdatePet:
    """更新 Pet — PUT /pet"""

    @allure.story("正向/反向用例")
    @pytest.mark.parametrize("case", load_test_cases("test_update_pet.yaml"))
    def test_update_pet(self, case, pet_api, created_pet_id, nonexistent_id):
        """数据驱动：更新 Pet"""
        context = {
            "pet_id": created_pet_id,
            "nonexistent_id": nonexistent_id,
        }
        _log_case(case, context)
        _execute_and_assert(pet_api, case, context)

    @allure.story("正向用例")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_update_pet_verify_persisted(self, pet_api, created_pet_id):
        """更新 Pet 并查询验证持久化成功"""
        new_name = f"Updated-{created_pet_id % 10000}"
        update_payload = {
            "id": created_pet_id,
            "name": new_name,
            "photoUrls": [],
            "status": "sold",
        }
        # 更新
        resp_update = pet_api.update_pet(update_payload)
        verify_status_code(resp_update.status_code, 200)

        # 回查验证
        resp_get = pet_api.get_pet_by_id(created_pet_id)
        verify_status_code(resp_get.status_code, 200)
        verify_json_fields(
            resp_get.json(),
            {
                "id": created_pet_id,
                "name": new_name,
                "status": "sold",
            },
        )
        log.info("Pet ID={} 更新已持久化: name={}, status=sold", created_pet_id, new_name)


# ============================================================
# 4. 删除 Pet
# ============================================================


@allure.epic("Petstore API")
@allure.feature("删除 Pet")
class TestDeletePet:
    """删除 Pet — DELETE /pet/{petId}"""

    @allure.story("正向/反向用例")
    @pytest.mark.parametrize("case", load_test_cases("test_delete_pet.yaml"))
    def test_delete_pet(self, case, pet_api, created_pet_id, nonexistent_id):
        """数据驱动：删除 Pet"""
        context = {
            "pet_id": created_pet_id,
            "nonexistent_id": nonexistent_id,
        }

        # 处理特殊场景：重复删除（先删一次）
        if case.get("run_mode") == "delete_twice":
            _log_case(case, context)
            resolved = resolve_template(deepcopy(case), context)
            path = resolved["path"]
            pet_id_from_path = path.rstrip("/").rsplit("/", 1)[-1]
            # 第一次删除（应该成功）
            resp1 = pet_api.delete_pet(pet_id_from_path)
            log.info("首次删除状态码: {} (准备二次删除)", resp1.status_code)
            # 第二次删除（期望 404）
            resp2 = pet_api.delete_pet(pet_id_from_path)
            verify_status_code(resp2.status_code, case["expected_status"])
        else:
            _execute_and_assert(pet_api, case, context)

    @allure.story("正向用例")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_delete_pet_verify_gone(self, pet_api, created_pet_id):
        """删除 Pet 后验证查询返回 404"""
        # 删除
        resp_del = pet_api.delete_pet(created_pet_id)
        verify_status_code(resp_del.status_code, 200)

        # 回查确认已删除
        resp_get = pet_api.get_pet_by_id(created_pet_id)
        verify_status_code(resp_get.status_code, 404)
        log.info("Pet ID={} 删除确认: 查询返回 404", created_pet_id)


# ============================================================
# 5. 完整业务流
# ============================================================


@allure.epic("Petstore API")
@allure.feature("完整业务流")
class TestFullFlow:
    """Create → Get → Update → Get → Delete → Get"""

    @allure.story("端到端业务流")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.full_flow
    @pytest.mark.smoke
    def test_full_business_flow(self, pet_api, new_pet_id):
        """完整业务流: 创建 → 查询 → 更新 → 查询 → 删除 → 查询删除确认"""

        pet_id = new_pet_id
        log.info("=" * 50)
        log.info("开始完整业务流测试 (Pet ID={})", pet_id)
        log.info("=" * 50)

        # ---- Step 1: 创建 Pet ----
        with allure.step(f"1️⃣  创建 Pet (ID={pet_id})"):
            create_payload = {
                "id": pet_id,
                "category": {"id": 1, "name": "dogs"},
                "name": "FlowBuddy",
                "photoUrls": ["https://example.com/flow.jpg"],
                "tags": [{"id": 1, "name": "friendly"}],
                "status": "available",
            }
            resp = pet_api.create_pet(create_payload)
            verify_status_code(resp.status_code, 200)
            verify_json_fields(
                resp.json(),
                {"name": "FlowBuddy", "status": "available"},
            )
            log.info("✅ 创建成功: ID={}", pet_id)

        # ---- Step 2: 通过 ID 查询 ----
        with allure.step(f"2️⃣  通过 ID 查询 Pet (ID={pet_id})"):
            resp = pet_api.get_pet_by_id(pet_id)
            verify_status_code(resp.status_code, 200)
            verify_json_fields(
                resp.json(),
                {"id": pet_id, "name": "FlowBuddy"},
            )
            log.info("✅ 查询成功: name=FlowBuddy")

        # ---- Step 3: 更新 Pet ----
        with allure.step(f"3️⃣  更新 Pet (ID={pet_id})"):
            update_payload = {
                "id": pet_id,
                "name": "FlowBuddy-Updated",
                "photoUrls": ["https://example.com/flow.jpg"],
                "tags": [{"id": 2, "name": "trained"}],
                "status": "sold",
            }
            resp = pet_api.update_pet(update_payload)
            verify_status_code(resp.status_code, 200)
            verify_json_fields(
                resp.json(),
                {"name": "FlowBuddy-Updated", "status": "sold"},
            )
            log.info("✅ 更新成功: name=FlowBuddy-Updated, status=sold")

        # ---- Step 4: 查询验证更新已持久化 ----
        with allure.step(f"4️⃣  回查验证更新已持久化 (ID={pet_id})"):
            resp = pet_api.get_pet_by_id(pet_id)
            verify_status_code(resp.status_code, 200)
            verify_json_fields(
                resp.json(),
                {
                    "id": pet_id,
                    "name": "FlowBuddy-Updated",
                    "status": "sold",
                },
            )
            log.info("✅ 更新已持久化确认")

        # ---- Step 5: 删除 Pet ----
        with allure.step(f"5️⃣  删除 Pet (ID={pet_id})"):
            resp = pet_api.delete_pet(pet_id)
            verify_status_code(resp.status_code, 200)
            log.info("✅ 删除成功")

        # ---- Step 6: 查询确认已删除 ----
        with allure.step(f"6️⃣  查询确认 Pet 已删除 (ID={pet_id})"):
            resp = pet_api.get_pet_by_id(pet_id)
            verify_status_code(resp.status_code, 404)
            log.info("✅ 删除确认: 查询返回 404")

        log.info("=" * 50)
        log.info("🎉 完整业务流测试通过 (Pet ID={})", pet_id)
        log.info("=" * 50)
