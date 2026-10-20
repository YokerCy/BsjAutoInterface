# -*- coding: UTF-8 -*-
'''
@File    : secrets.py
@Project : smart_auto_interface
@Depict  : 密钥取值统一入口（避免凭据硬编码进入公开仓库）

取值优先级（高 -> 低）：
    1. 环境变量          TEST_USERNAME / TEST_PASSWORD / OPEN_API_KEY ...
    2. conf/config.local.yaml -> secrets.<NAME>   （本地私有文件，已被 .gitignore 忽略）
    3. 代码里传入的默认值

conf/config.yaml 中统一写占位符 ${NAME}，加载时由本模块展开；
占位符解析不到会直接报错并提示两种配置方式，避免"静默用空密码去登录"。

CI / 服务器上只配环境变量即可，无需落地任何明文文件。
'''
import os

import yaml

_LOCAL_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "conf",
    "config.local.yaml",
)

_cache = None


def _local_secrets():
    """读取 conf/config.local.yaml 的 secrets 段（文件不存在则视为空）。"""
    global _cache
    if _cache is not None:
        return _cache

    data = {}
    if os.path.exists(_LOCAL_CONFIG):
        try:
            with open(_LOCAL_CONFIG, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            data = (loaded.get("secrets") or {}) if isinstance(loaded, dict) else {}
        except Exception:  # 文件损坏不应阻断用例，交给后续取值报错
            data = {}
    _cache = {str(k): v for k, v in data.items()}
    return _cache


def reload():
    """清缓存：改了 config.local.yaml 又不想重启进程时用。"""
    global _cache
    _cache = None


def get(name, default=None):
    """
    按优先级取单个密钥。
    :param name: 变量名（大写，如 TEST_PASSWORD）
    :param default: 都没有时的兜底值
    """
    value = os.environ.get(name)
    if value is not None and str(value).strip() != "":
        return value

    value = _local_secrets().get(name)
    if value is not None and str(value).strip() != "":
        return value

    return default


def require(name):
    """取必填密钥，缺失时报可操作的错误。"""
    value = get(name)
    if value is None or str(value).strip() == "":
        raise RuntimeError(
            f"缺少密钥 {name}。请二选一配置：\n"
            f"  1) 环境变量：set {name}=<值>   (Linux/macOS: export {name}=<值>)\n"
            f"  2) 本地配置：conf/config.local.yaml -> secrets.{name}: \"<值>\"\n"
            f"（config.local.yaml 已被 .gitignore 忽略，不会进仓库）"
        )
    return value


def expand(value):
    """
    递归展开数据结构里的 ${NAME} 占位符。
    整串就是一个占位符时返回原生值（保留 int 等类型），否则做字符串替换。
    """
    if isinstance(value, dict):
        return {k: expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand(v) for v in value]
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    # 整串占位符：${TEST_PASSWORD}
    if stripped.startswith("${") and stripped.endswith("}") and stripped.count("${") == 1:
        return require(stripped[2:-1])

    # 字符串内嵌占位符：prefix-${NAME}-suffix
    result = value
    start = 0
    while True:
        i = result.find("${", start)
        if i == -1:
            break
        j = result.find("}", i)
        if j == -1:
            break
        name = result[i + 2:j]
        result = result[:i] + str(require(name)) + result[j + 1:]
        start = i + len(str(require(name)))
    return result
