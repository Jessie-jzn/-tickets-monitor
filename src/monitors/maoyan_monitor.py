from .base_monitor import BaseMonitor
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import random

class MaoyanMonitor(BaseMonitor):
    def __init__(self, config: dict):
        super().__init__(config)
        self.maoyan_config = config.get('maoyan', {})
        self.headers = {
            "Host": "wx.maoyan.com",
            "mtgsig": self.maoyan_config.get('mtgsig', ''),
            "content-type": "application/json",
            "x-wxa-query": "{\"modelStyle\":\"0\",\"isNewPage\":\"true\",\"id\":\"359265\",\"isHotProject\":\"0\"}",
            "x-wxa-referer": "pages/show/detail/v2/index",
            "uuid": self.maoyan_config.get('uuid', ''),
            "version": "wallet-v5.10.5",
            "X-Requested-With": "wxapp",
            "x-wxa-page": "pages/showsubs/ticket-level/v2/index",
            "token": self.maoyan_config.get('token', ''),
            "X-Channel-ID": "70001",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/4G Language/zh_CN",
            "Referer": "https://servicewechat.com/wxdbb4c5f1b8ee7da1/1554/page-frame.html"
        }
        self.tickets_url = "https://wx.maoyan.com/my/odea/show/tickets"
        # 创建新的session并设置重试策略
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        # 禁用代理
        self.session.trust_env = False

    def check_availability(self, url: str) -> bool:
        try:
            # 遍历所有配置的演唱会
            for show_config in self.maoyan_config.get('shows', []):
                show_name = show_config.get('name', '未知演出')
                self.logger.info(f"\n正在检查 {show_name}")
                
                params = {
                    "token": self.maoyan_config.get('token', ''),
                    "sellChannel": "7",
                    "showId": show_config.get('show_id'),
                    "projectId": show_config.get('project_id'),
                    "clientPlatform": "2",
                    "cityId": self.maoyan_config.get('city_id', '')
                }
                
                # 添加重试机制
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        response = self.session.get(
                            self.tickets_url,
                            headers=self.headers,
                            params=params,
                            timeout=(5, 10),
                            verify=True
                        )
                        break
                    except requests.exceptions.RequestException as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            raise e
                        time.sleep(1)
                
                if response.status_code != 200:
                    self.logger.error(f"{show_name} 请求失败，状态码: {response.status_code}")
                    continue
                
                result = response.json()
                if not result.get("success"):
                    self.logger.error(f"{show_name} 请求返回错误: {result.get('msg', '未知错误')}")
                    continue

                target_prices = show_config.get('target_prices', [])
                found_target_ticket = False
                available_tickets = []

                show_info = result.get("data", {}).get("showVO", {})
                show_time = show_info.get("showName", "未知时间")
                
                self.logger.info(f"场次：{show_time}")
                self.logger.info(f"开售时间：{self.format_timestamp(show_info.get('onSaleTime'))}")

                tickets = result.get("data", {}).get("ticketsVO", [])
                for ticket in tickets:
                    price = ticket.get('ticketPriceVO', {}).get('sellPrice', 0)
                    status = "有票" if ticket.get("showStatus") == 2 else "无票"
                    target_price = "（目标价格）" if price in target_prices else ""
                    remaining = f"剩余：{ticket.get('remainingStock', 0)}张" if ticket.get('remainingStock', 0) > 0 else ""
                    
                    self.logger.info(f"{ticket.get('description')} ({price}元): {status} {remaining} {target_price}")
                    
                    if ticket.get("showStatus") == 2:  # 有票
                        ticket_info = f"场次：{show_time}，{ticket.get('description')}，价格：{price}元，{remaining}"
                        available_tickets.append(ticket_info)
                        
                        if price in target_prices:
                            found_target_ticket = True
                            self.logger.info(f"\n发现目标票价: {ticket.get('description')} ({price}元)")

                if available_tickets:
                    subject = f"猫眼发现可用票务！- {show_name}"
                    body = f"""
演出：{show_name}
场次：{show_time}
开售时间：{self.format_timestamp(show_info.get('onSaleTime'))}

发现以下票档有票：

""" + "\n".join(available_tickets)
                    self.notify(subject, body)

                # 每个演出检查完后等待一小段时间
                time.sleep(random.uniform(1, 3))
                
            return found_target_ticket
            
        except Exception as e:
            self.logger.error(f"猫眼检查失败: {str(e)}")
            return False

    def format_timestamp(self, timestamp: int) -> str:
        """格式化时间戳"""
        if not timestamp:
            return "未知"
        from datetime import datetime
        return datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')