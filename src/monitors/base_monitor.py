import logging
import time
import random
from abc import ABC, abstractmethod
from typing import List, Optional
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

import requests
from requests.exceptions import RequestException
from src.utils.email_sender import send_email

class BaseMonitor(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.monitor_count = 0  # 监控次数计数器
        
    @abstractmethod
    def check_availability(self, url: str) -> bool:
        """检查票务是否可用"""
        pass

    def monitor(self, urls: List[str]):
        """监控主循环"""
        while True:
            self.monitor_count += 1
            self.logger.info(f"\n第 {self.monitor_count} 次监控")
            
            # 每50次监控后休息2-5分钟
            if self.monitor_count % 50 == 0:
                rest_time = random.randint(120, 300)  # 2-5分钟
                self.logger.info(f"已完成 {self.monitor_count} 次监控，休息 {rest_time} 秒...")
                time.sleep(rest_time)
                continue

            for url in urls:
                try:
                    if self.check_availability(url):
                        self.logger.info(f"发现可用票务! URL: {url}")
                except Exception as e:
                    self.logger.error(f"监控出错: {str(e)}")
            
            time.sleep(self.config['monitor']['interval'])

    def notify(self, subject: str, body: str):
        """发送通知"""
        try:
            send_email(self.config['email'], subject, body)
            self.logger.info("通知邮件发送成功")
        except Exception as e:
            self.logger.error(f"发送通知失败: {str(e)}")