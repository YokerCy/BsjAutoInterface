# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 11:15 
@Author  : bo_god
@File    : conftest.py
@Project : smart_auto_interface 
@Depict    :
'''
import pytest
import requests
import allure
import json
import re
import time
from base.log import logger
from base.redConfig import Config
from base.throttle import throttle


@pytest.fixture(scope="session")
def cfg():
    """将配置类作为 fixture 暴露出来"""
    return Config()


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="test", help="set env")


@pytest.fixture(scope="session")
def env(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def user_client(env):
    cfg = Config(env=env)

    class Client:
        def __init__(self, config_obj):
            self.config = config_obj
            self.session = requests.Session()  # 全局唯一的会话对象
            self.base_url = self.config.base_url
            self.base_api_url = self.config.base_api_url

            self.userId = None  # 新增：用于存放用户ID

            env_headers = self.config.env_conf.get("common_headers", {})
            # 将读取到的键值对批量更新到 session.headers 中
            if env_headers:
                self.session.headers.update(env_headers)

        def login(self):
            # 1. 从配置读取
            current_env = self.config.env
            acc_info = self.config.data["environments"][current_env]["accounts"]["admin"]
            username = acc_info["username"]
            raw_password = acc_info["password"]
            # 2. 密码处理：假设需要实时加密发送
            encrypted_pwd = cfg.aes_encrypt_like_cryptojs_ecb(raw_password)

            # 3. 发送登录
            login_url = f"{self.base_url}/user/login"
            payload = {"userName": username, "password": encrypted_pwd}

            res = self.session.post(login_url, json=payload)
            res_data = res.json()
            token = res_data.get("data", {}).get("sid")

            self.userId = res_data["data"]["userId"]  # 提取字段

            # 4. 【关键】更新 Session 的 Headers
            # 这一步执行后，该 client 实例后续发出的所有请求都会自动带上这个 header
            if token:
                self.session.headers.update({"token": f"{token}"})
            return res

        def send_by_key(self, method, endpoint_key, **kwargs):
            """平台接口请求（用 base_url）"""
            # 1. 获取基础路由
            path = self.config.get_endpoint(endpoint_key)

            # 2. 处理路径参数 {id}
            if "path_params" in kwargs:
                path = path.format(**kwargs.pop("path_params"))

            url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

            logger.info(f"发送请求 --> {method} {url}")
            # if kwargs.get("json"):
            #     logger.debug(f"请求参数: {kwargs.get('json')}")

            # 3. 处理全局固定 params 参数 (URL后面的参数)
            # 获取 yaml 里的 common_params
            all_params = self.config.data["environments"][self.config.env]["common_params"].copy()

            # 如果本次调用也传了 params，则进行合并（覆盖或新增）
            if "params" in kwargs:
                all_params.update(kwargs.pop("params"))

            # 4. 重新放回 kwargs 中发送
            kwargs["params"] = all_params

            res = self._request_with_retry(method, url, endpoint_key=endpoint_key, **kwargs)

            try:
                # 记录请求 URL
                allure.attach(res.url, name="请求全部路径 URL", attachment_type=allure.attachment_type.TEXT)
                # 记录 cURL 命令 (调用我们下面定义的转换函数)
                curl_cmd = self.to_curl(res.request)
                allure.attach(curl_cmd, name="复制此 cURL 手动复现", attachment_type=allure.attachment_type.TEXT)

                # 记录响应体 (可选：方便直接在报告看返回)
                allure.attach(
                    json.dumps(res.json(), indent=2, ensure_ascii=False),
                    name="实际响应结果",
                    attachment_type=allure.attachment_type.JSON
                )
            except Exception as e:
                # 防止在非 pytest 环境或解析 JSON 失败时报错影响主流程
                logger.error(f"Allure 附件添加失败: {e}")
            # 执行请求：此时 self.session 已带 Token，kwargs 已带合并后的 params 和 json
            return res

        def _request_with_retry(self, method, url, max_retries=3, endpoint_key=None, **kwargs):
            """
            带「主动节流 + 限流自动重试」的请求。

            背景：服务端在请求过频时会返回
                {"code": 503, "msg": "Rate limit exceeded. Please retry in 120 seconds.",
                 "subCode": "server.busy.retry"}
            这属于「请求被拒」，不是接口坏了 —— 断言失败会污染巡检结果（假红）。

            两道防线：
              1) 主动节流（throttle）：请求前就按接口限制控制频率，降低撞上限流的概率
              2) 被动重试：万一仍被限流，按服务端提示的秒数等待后重试；
                 重试仍失败则把最后一次响应原样返回，交由断言报错（保证不掩盖真问题）。
            """
            res = None
            for attempt in range(1, max_retries + 1):
                # 第一道防线：主动节流（首次请求前也走一次，保证与上次调用的间隔）
                if endpoint_key:
                    throttle(endpoint_key)

                res = self.session.request(method, url, **kwargs)
                try:
                    body = res.json()
                except Exception:
                    return res  # 非 JSON（网关错误页等），不做限流判定

                is_limited = (
                    body.get("code") == 503
                    or body.get("subCode") == "server.busy.retry"
                    or "rate limit" in str(body.get("msg", "")).lower()
                )
                if not is_limited:
                    return res

                # 从 msg 里解析服务端要求的等待秒数（如 "retry in 120 seconds"）
                wait = 120
                m = re.search(r"retry in (\d+)", str(body.get("msg", "")))
                if m:
                    wait = int(m.group(1))
                wait = min(wait, 180)  # 上限保护，避免异常值把用例挂死

                if attempt < max_retries:
                    logger.warning(
                        f"⏳ 触发接口限流（第 {attempt}/{max_retries} 次），"
                        f"按服务端提示等待 {wait}s 后重试: {url}"
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"❌ 限流重试 {max_retries} 次仍失败，返回最后一次响应: {url}"
                    )
            return res

        def send_api(self, method, endpoint_key, **kwargs):
            """
                开放接口请求（用 base_api_url）
                - 自动拼接 base_api_url
                - session 已带 key/version/Accept-Language/Content-Type
                - 不需要 token
                - 自动处理限流重试，避免「被限流」被误判成接口失败
            """
            # 1. 获取基础路由
            path = self.config.get_endpoint(endpoint_key)

            # 2. 处理路径参数 {id}
            if "path_params" in kwargs:
                path = path.format(**kwargs.pop("path_params"))

            url = f"{self.base_api_url.rstrip('/')}/{path.lstrip('/')}"
            logger.info(f"开放接口请求 --> {method} {url}")

            res = self._request_with_retry(method, url, endpoint_key=endpoint_key, **kwargs)

            try:
                allure.attach(res.url, name="请求URL",
                              attachment_type=allure.attachment_type.TEXT)
                curl_cmd = self.to_curl(res.request)
                allure.attach(curl_cmd, name="cURL命令",
                              attachment_type=allure.attachment_type.TEXT)
                allure.attach(
                    json.dumps(res.json(), indent=2, ensure_ascii=False),
                    name="响应结果",
                    attachment_type=allure.attachment_type.JSON
                )
            except Exception as e:
                logger.error(f"Allure 附件添加失败: {e}")

            return res

         # ========== 🆕 快捷方法 ==========
        def api_get(self, endpoint_key, **kwargs):
            return self.send_api("GET", endpoint_key, **kwargs)

        def api_post(self, endpoint_key, **kwargs):
            return self.send_api("POST", endpoint_key, **kwargs)

        def to_curl(self, request):
            """将 requests 的 request 对象转换为 cURL 命令字符串"""
            headers = ["'{0}: {1}'".format(k, v) for k, v in request.headers.items()]
            header_str = " -H ".join(headers)

            # 处理 body 数据
            data = ""
            if request.body:
                if isinstance(request.body, bytes):
                    data = request.body.decode('utf-8')
                else:
                    data = str(request.body)

            # 拼装 cURL
            base_curl = f"curl -X {request.method} -H {header_str}"
            if data:
                # 替换掉数据中的换行符防止命令断掉
                data_clean = data.replace('\n', '').replace('\r', '')
                base_curl += f" -d '{data_clean}'"

            base_curl += f" '{request.url}'"
            return base_curl

    client = Client(cfg)
    client.login()  # 初始化即完成登录和 Token 注入
    return client


# ========== 🆕 新增：开放接口专用 Client（不登录） ==========
@pytest.fixture(scope="session")
def api_client(env):
    """开放接口 Client — 只用 key 鉴权，不走登录"""
    cfg = Config(env=env)

    class ApiClient:
        def __init__(self, config_obj):
            self.config = config_obj
            self.session = requests.Session()
            self.base_api_url = self.config.base_api_url

            # 固定鉴权 Header
            self.session.headers.update({
                "key": self.config.env_conf.get("common_headers", {}).get("key", ""),
                "version": "1.0",
                "Accept-Language": "en",
                "Content-Type": "application/json",
            })

        def _request_with_retry(self, method, url, max_retries=3, **kwargs):
            """带限流自动重试的请求，逻辑同 user_client（避免被限流误判成接口失败）。"""
            res = None
            for attempt in range(1, max_retries + 1):
                res = self.session.request(method, url, **kwargs)
                try:
                    body = res.json()
                except Exception:
                    return res

                is_limited = (
                    body.get("code") == 503
                    or body.get("subCode") == "server.busy.retry"
                    or "rate limit" in str(body.get("msg", "")).lower()
                )
                if not is_limited:
                    return res

                wait = 120
                m = re.search(r"retry in (\d+)", str(body.get("msg", "")))
                if m:
                    wait = int(m.group(1))
                wait = min(wait, 180)

                if attempt < max_retries:
                    logger.warning(
                        f"⏳ 触发接口限流（第 {attempt}/{max_retries} 次），"
                        f"按服务端提示等待 {wait}s 后重试: {url}"
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"❌ 限流重试 {max_retries} 次仍失败，返回最后一次响应: {url}")
            return res

        def send_api(self, method, endpoint_key, **kwargs):
            # 1. 获取基础路由
            path = self.config.get_endpoint(endpoint_key)

            # 2. 处理路径参数 {id}
            if "path_params" in kwargs:
                path = path.format(**kwargs.pop("path_params"))

            url = f"{self.base_api_url.rstrip('/')}/{path.lstrip('/')}"
            logger.info(f"开放接口请求 --> {method} {url}")

            res = self._request_with_retry(method, url, endpoint_key=endpoint_key, **kwargs)

            try:
                allure.attach(res.url, name="请求URL",
                              attachment_type=allure.attachment_type.TEXT)
                allure.attach(
                    json.dumps(res.json(), indent=2, ensure_ascii=False),
                    name="响应结果",
                    attachment_type=allure.attachment_type.JSON
                )
            except Exception as e:
                logger.error(f"Allure 附件添加失败: {e}")

            return res

        def api_post(self, endpoint_key, **kwargs):
            return self.send_api("POST", endpoint_key, **kwargs)

        def api_get(self, endpoint_key, **kwargs):
            return self.send_api("GET", endpoint_key, **kwargs)

    return ApiClient(cfg)
