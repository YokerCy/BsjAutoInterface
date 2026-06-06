# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 19:47 
@Author  : bo_god
@File    : log.py
@Project : smart_auto_interface 
@Depict    : 日志封装
'''
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler

class Logger:
    def __init__(self, name="Inspection"):
        # 1. 创建日志目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 2. 创建日志对象
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 防止重复添加 Handler 导致日志重叠打印
        if not self.logger.handlers:
            # 3. 定义格式：时间 - 级别 - 文件名[行号] - 消息
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(filename)s[line:%(lineno)d] - %(message)s'
            )

            # 4. 文件处理器：按天轮转，保留最近 30 天
            log_file = os.path.join(log_dir, f"{time.strftime('%Y-%m-%d')}.log")
            file_handler = TimedRotatingFileHandler(
                log_file, when='D', interval=1, backupCount=30, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)

            # 5. 控制台处理器：用于实时查看
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)

            # 6. 添加到 Logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

# 初始化一个单例供全局使用
logger = Logger().get_logger()