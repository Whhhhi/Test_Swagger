"""
HTTP 请求客户端封装

封装 requests 库，提供：
- 统一的会话管理（Session + 连接池）
- 自动注入认证 Header
- 请求/响应日志记录（Allure 附件 + Loguru）
- 超时与重试支持
- 统一异常处理
"""

import json
from typing import Any, Optional

import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common.logger import log, bind_logger


class RequestClient:
    """轻量级 HTTP 客户端，封装 requests.Session"""

    def __init__(
        self,
        base_url: str,
        default_headers: Optional[dict] = None,
        timeout: int = 10,
        retry_times: int = 2,
    ):
        """
        Args:
            base_url: API 基础地址
            default_headers: 默认请求头
            timeout: 请求超时（秒）
            retry_times: 失败重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=retry_times,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # 设置默认 Header
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(default_headers or {}),
        }
        self.session.headers.update(self.default_headers)

    def _build_url(self, path: str) -> str:
        """拼接完整 URL"""
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    def _log_request(
        self,
        method: str,
        url: str,
        headers: dict,
        params: Optional[dict],
        json_body: Any,
    ):
        """记录请求信息到 Allure"""
        curl = f"curl -X {method} '{url}'"
        for k, v in headers.items():
            if k.lower() != "api_key":  # 敏感信息脱敏
                curl += f" -H '{k}: {v}'"
            else:
                curl += f" -H '{k}: ***'"
        if json_body:
            curl += f" -d '{json.dumps(json_body, ensure_ascii=False)}'"

        allure.attach(
            name=f"➡️ Request {method}",
            body=(
                f"**URL:** {url}\n\n"
                f"**Headers:**\n```\n{json.dumps(headers, indent=2, ensure_ascii=False)}\n```\n\n"
                f"**Body:**\n```json\n{json.dumps(json_body, indent=2, ensure_ascii=False) if json_body else '{}'}\n```\n\n"
                f"**cURL:**\n```bash\n{curl}\n```"
            ),
            attachment_type=allure.attachment_type.TEXT,
        )

    def _log_response(self, response: requests.Response, elapsed_ms: float):
        """记录响应信息到 Allure"""
        try:
            resp_body = response.json()
            body_str = json.dumps(resp_body, indent=2, ensure_ascii=False)
        except Exception:
            body_str = response.text or "(empty)"

        allure.attach(
            name=f"⬅️ Response {response.status_code}",
            body=(
                f"**Status:** {response.status_code}\n\n"
                f"**Time:** {elapsed_ms:.0f}ms\n\n"
                f"**Headers:**\n```\n{json.dumps(dict(response.headers), indent=2, ensure_ascii=False)}\n```\n\n"
                f"**Body:**\n```json\n{body_str}\n```"
            ),
            attachment_type=allure.attachment_type.TEXT,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json_data: Any = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        """通用请求方法

        Args:
            method: HTTP 方法（GET/POST/PUT/DELETE）
            path: 请求路径（如 /pet）
            params: URL 查询参数
            json_data: JSON 请求体
            headers: 额外请求头（会合并到默认 Header）

        Returns:
            requests.Response 对象

        Raises:
            requests.RequestException: 网络层异常
        """
        url = self._build_url(path)
        merged_headers = {**self.default_headers, **(headers or {})}

        self._log_request(method, url, merged_headers, params, json_data)

        logger = bind_logger(request_id=f"{method} {path}")

        try:
            start = __import__("time").time()
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=merged_headers,
                timeout=self.timeout,
                **kwargs,
            )
            elapsed = (__import__("time").time() - start) * 1000

            self._log_response(response, elapsed)

            logger.info(
                "[{:>3d}] {:6s} {} ({:.0f}ms)".format(
                    response.status_code, method, url, elapsed
                )
            )

            return response

        except requests.exceptions.Timeout as e:
            logger.error("请求超时: {} {} — {}", method, url, e)
            allure.attach(
                name="❌ Timeout",
                body=f"请求超时: {method} {url}\n{e}",
                attachment_type=allure.attachment_type.TEXT,
            )
            raise

        except requests.exceptions.ConnectionError as e:
            logger.error("连接失败: {} {} — {}", method, url, e)
            allure.attach(
                name="❌ ConnectionError",
                body=f"连接失败: {method} {url}\n{e}",
                attachment_type=allure.attachment_type.TEXT,
            )
            raise

        except requests.exceptions.RequestException as e:
            logger.error("请求异常: {} {} — {}", method, url, e)
            allure.attach(
                name="❌ RequestException",
                body=f"请求异常: {method} {url}\n{e}",
                attachment_type=allure.attachment_type.TEXT,
            )
            raise

    # ---- 便捷方法 ----

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
