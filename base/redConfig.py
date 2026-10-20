# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 11:14 
@Author  : bo_god
@File    : redConfig.py
@Project : smart_auto_interface 
@Depict    : 读取配置文件
'''
import yaml
import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad

from base import secrets as _secrets

class Config:
    def __init__(self, env=None):
        # 动态获取路径，确保在不同环境下都能找到配置文件
        # config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        current_file_path = os.path.abspath(__file__)
        base_dir = os.path.dirname(current_file_path)
        self.project_root = os.path.dirname(base_dir)

        self.config_path = os.path.join(self.project_root, "conf", "config.yaml")
        self.data = self._read_yaml(self.config_path)

        # 设置环境属性
        self.env = self.data.get("default", "test")
        self.env_conf = self.data["environments"][self.env]
        self.base_url = self.data["environments"][self.env]["base_url"]

        # self.env = env or self.data.get("default", "test")
        # self.env_conf = self.data["environments"][self.env]
        #
        # with open(self.config_path, "r", encoding="utf-8") as f:
        #     self.data = yaml.safe_load(f)

    def _read_yaml(self, path):
        """将重复的读取逻辑封装；加载后展开 ${NAME} 密钥占位符"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"未找到配置文件: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # 凭据不落仓库：config.yaml 里写 ${NAME}，实际值来自环境变量或 config.local.yaml
        return _secrets.expand(data)

    def get_url(self, name):
        # 优雅的路径拼接：自动处理 base_url 末尾是否有 / 的情况
        endpoint = self.data["endpoints"].get(name)
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def get_endpoint(self, name):
        """根据名称获取路由"""
        return self.data["endpoints"].get(name, "")

    def get_test_data(self, file_name):
        """
        动态加载 tests/data 目录下的数据文件
        :param file_name: 文件名，如 'vehicle_data' (不用带.yaml)
        """
        data_path = os.path.join(self.project_root, "conf", f"{file_name}.yaml")
        return self._read_yaml(data_path)

    def get_cases_by_interface(self, file_name, interface_name):
        """
        从指定 YAML 中获取特定接口的所有用例
        """
        data = self.get_test_data(file_name)
        return [c for c in data if c.get("interface") == interface_name]

    def aes_encrypt_like_cryptojs_ecb(self, plaintext: str) -> str:
        token = "token=86d7423c-6"
        key_bytes = token.encode("utf-8")   # 正好 16 bytes，不需要补零

        # ECB 模式会忽略 IV，这里不用传
        cipher = AES.new(key_bytes, AES.MODE_ECB)

        # PKCS7 填充到 16 字节块
        padded = pad(plaintext.encode("utf-8"), 16)

        encrypted = cipher.encrypt(padded)

        # crypto-js 默认输出 Base64
        return base64.b64encode(encrypted).decode()

    def aes_decrypt_ecb_cryptojs(self, cipher_b64: str) -> str:
        """
        参数：
          cipher_b64: Base64 密文
          token:      'token=86d7423c-6'
        返回：
          明文字符串
        """
        token = "token=86d7423c-6"
        key_bytes = token.encode("utf-8")   # 必须 16 字节

        cipher = AES.new(key_bytes, AES.MODE_ECB)

        # Base64 解码
        cipher_bytes = base64.b64decode(cipher_b64)

        # AES 解密
        padded_plain = cipher.decrypt(cipher_bytes)

        # 去掉 PKCS7 填充
        plain_bytes = unpad(padded_plain, 16)

        return plain_bytes.decode("utf-8")

    @property
    def base_api_url(self):
        """开放接口的 base_url"""
        return self.data["environments"][self.env].get("base_api_url", "")
