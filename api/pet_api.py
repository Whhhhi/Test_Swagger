"""
Pet API 对象封装

对应 Petstore 的 /pet 相关接口：
- POST   /pet              创建 Pet
- GET    /pet/{petId}      通过 ID 查询 Pet
- PUT    /pet              更新 Pet
- DELETE /pet/{petId}      删除 Pet
"""

from typing import Any, Dict, Optional

import allure

from common.request_client import RequestClient


class PetApi:
    """Pet 接口操作类"""

    def __init__(self, client: RequestClient):
        """
        Args:
            client: 已注入认证信息的 HTTP 客户端
        """
        self.client = client

    # ────────────────────────── POST /pet ──────────────────────────

    @allure.step("📦 创建 Pet")
    def create_pet(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> "requests.Response":
        """创建 Pet

        POST /pet

        Args:
            payload: Pet 对象 JSON body
            headers: 额外请求头

        Returns:
            Response 对象
        """
        return self.client.post(
            "/pet",
            json_data=payload,
            headers=headers,
        )

    # ────────────────────── GET /pet/{petId} ───────────────────────

    @allure.step("🔍 通过 ID 查询 Pet: petId={pet_id}")
    def get_pet_by_id(
        self,
        pet_id: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> "requests.Response":
        """通过 ID 查询 Pet

        GET /pet/{petId}

        Args:
            pet_id: Pet ID（数字或字符串）
            headers: 额外请求头

        Returns:
            Response 对象
        """
        return self.client.get(
            f"/pet/{pet_id}",
            headers=headers,
        )

    # ──────────────────────── PUT /pet ─────────────────────────────

    @allure.step("✏️ 更新 Pet")
    def update_pet(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> "requests.Response":
        """更新 Pet

        PUT /pet

        Args:
            payload: 完整的 Pet 对象 JSON body
            headers: 额外请求头

        Returns:
            Response 对象
        """
        return self.client.put(
            "/pet",
            json_data=payload,
            headers=headers,
        )

    # ──────────────────── DELETE /pet/{petId} ─────────────────────

    @allure.step("🗑️ 删除 Pet: petId={pet_id}")
    def delete_pet(
        self,
        pet_id: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> "requests.Response":
        """删除 Pet

        DELETE /pet/{petId}

        Args:
            pet_id: Pet ID
            headers: 额外请求头

        Returns:
            Response 对象
        """
        return self.client.delete(
            f"/pet/{pet_id}",
            headers=headers,
        )
