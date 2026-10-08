"""
断言工具模块

提供灵活且可读性强的响应断言方法：
- verify_status_code — 验证 HTTP 状态码
- verify_json_field — 验证 JSON 响应体指定字段
- verify_json_fields — 批量验证多个字段（支持模糊匹配）
- verify_json_structure — 验证 JSON 结构（字段存在性与类型）
"""

from typing import Any, Dict, Optional

import allure


@allure.step("🔍 验证 HTTP 状态码: 期望={expected}, 实际={actual}")
def verify_status_code(actual: int, expected: int) -> None:
    """验证 HTTP 响应状态码

    Args:
        actual: 实际状态码
        expected: 期望状态码

    Raises:
        AssertionError: 不匹配时抛出
    """
    assert actual == expected, (
        f"❌ 状态码不匹配: 期望 {expected}, 实际 {actual}"
    )


@allure.step("🔍 验证响应体字段: {field_path} == {expected_value}")
def verify_json_field(
    response_body: dict,
    field_path: str,
    expected_value: Any,
) -> None:
    """验证 JSON 响应体中指定路径的字段值

    支持点号分隔的嵌套路径，例如 "category.name"

    Args:
        response_body: 响应 JSON 字典
        field_path: 字段路径（如 "id", "category.name"）
        expected_value: 期望值

    Raises:
        AssertionError: 字段缺失或值不匹配
    """
    parts = field_path.split(".")
    current = response_body

    for part in parts:
        if not isinstance(current, dict):
            raise AssertionError(
                f"❌ 路径 '{field_path}' 在 '{part}' 处中断: "
                f"上一级不是 dict (实际: {type(current).__name__})"
            )
        if part not in current:
            raise AssertionError(
                f"❌ 字段 '{field_path}' 不存在于响应体中\n"
                f"可用字段: {list(current.keys())}"
            )
        current = current[part]

    assert current == expected_value, (
        f"❌ 字段 '{field_path}' 值不匹配: "
        f"期望 '{expected_value}', 实际 '{current}'"
    )


@allure.step("🔍 批量验证响应体字段")
def verify_json_fields(
    response_body: dict,
    fields: Dict[str, Any],
) -> None:
    """批量验证多个字段值

    遍历 {field_path: expected_value} 字典，逐一验证。

    Args:
        response_body: 响应 JSON 字典
        fields: 字段名到期望值的映射
    """
    for field_path, expected_value in fields.items():
        verify_json_field(response_body, field_path, expected_value)


@allure.step("🔍 验证响应体字段存在性: {field_path}")
def verify_field_exists(response_body: dict, field_path: str) -> None:
    """验证 JSON 响应体中指定路径的字段存在（不校验值）

    Args:
        response_body: 响应 JSON 字典
        field_path: 字段路径（如 "category.name"）

    Raises:
        AssertionError: 字段不存在时抛出
    """
    parts = field_path.split(".")
    current = response_body
    for part in parts:
        if not isinstance(current, dict):
            raise AssertionError(
                f"❌ 路径 '{field_path}' 在 '{part}' 处中断: "
                f"非 dict 类型 ({type(current).__name__})"
            )
        if part not in current:
            raise AssertionError(
                f"❌ 字段 '{field_path}' 不存在于响应体中\n"
                f"可用字段: {list(current.keys())}"
            )
        current = current[part]


@allure.step("🔍 验证数组字段非空: {field_path}")
def verify_array_non_empty(response_body: dict, field_path: str) -> None:
    """验证 JSON 响应体中的数组字段非空

    Args:
        response_body: 响应 JSON 字典
        field_path: 数组字段路径

    Raises:
        AssertionError: 字段不存在、非数组或空数组时抛出
    """
    parts = field_path.split(".")
    current = response_body
    for part in parts:
        if not isinstance(current, dict):
            raise AssertionError(
                f"❌ 路径 '{field_path}' 在 '{part}' 处中断"
            )
        if part not in current:
            raise AssertionError(f"❌ 字段 '{field_path}' 不存在")
        current = current[part]

    assert isinstance(current, list), (
        f"❌ 字段 '{field_path}' 不是数组 (实际: {type(current).__name__})"
    )
    assert len(current) > 0, (
        f"❌ 字段 '{field_path}' 为空数组"
    )


@allure.step("🔍 验证响应结构完整性")
def verify_minimal_structure(response_body: dict, required_fields: list) -> None:
    """验证最小字段集存在

    Args:
        response_body: 响应 JSON 字典
        required_fields: 必须存在的字段路径列表
    """
    missing = []
    for field in required_fields:
        parts = field.split(".")
        current = response_body
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                missing.append(field)
                break
            current = current[part]

    assert not missing, (
        f"❌ 以下必填字段缺失: {missing}"
    )
