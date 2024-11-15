from typing import List, Dict, Optional
from .base_monitor import BaseMonitor
import time
import random
import json
from datetime import datetime

class LiveLabMonitor(BaseMonitor):
    def __init__(self, config: dict):
        super().__init__(config)
        self.livelab_config = config.get('livelab', {})
        self.headers = {
            "Host": "api.livelab.com.cn",
            "Authorization": self.livelab_config.get('authorization', ''),
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/WIFI Language/zh_CN",
            "Referer": "https://servicewechat.com/wx5a8f481d967649eb/101/page-frame.html"
        }
        self.base_url = "https://api.livelab.com.cn"
        self.performs_url = f"{self.base_url}/performance/app/project/get_performs"
        self.project_url = f"{self.base_url}/performance/app/project/get_project_info"
        self.params = {
            "project_id": self.livelab_config.get('project_id'),
            "retry": "false"
        }

    def get_project_info(self) -> Dict:
        """获取演出详细信息"""
        try:
            params = {
                **self.params,
                "v": str(int(time.time() * 1000))
            }
            response = self.session.get(
                self.project_url,
                headers=self.headers,
                params=params,
                timeout=(5, 10)
            )
            
            if response.status_code != 200:
                self.logger.error("获取演出信息失败")
                return {}
            
            result = response.json()
            if result.get("code") != 10000:
                return {}

            project_name = result.get("data", {}).get("projectName", "未知演出")
            self.logger.info(f"\n演出：{project_name}")
            
            return {"name": project_name}
            
        except Exception as e:
            self.logger.error(f"获取演出信息失败: {str(e)}")
            return {}

    def check_availability(self, url: str) -> bool:
        try:
            # 先获取演出详细信息
            show_info = self.get_project_info()
            
            # 获取票务信息
            self.params["v"] = str(int(time.time() * 1000))
            response = self.session.get(
                self.performs_url,
                headers=self.headers,
                params=self.params,
                timeout=(5, 10)
            )
            
            if response.status_code != 200:
                self.logger.error("LiveLab请求失败")
                return False
            
            result = response.json()
            if result.get("code") != 10000:
                return False

            target_prices = self.livelab_config.get('target_prices', [])
            target_dates = self.livelab_config.get('target_dates', [])
            found_target_ticket = False
            available_tickets = []

            perform_infos = result.get("data", {}).get("performInfos", [])
            for date_info in perform_infos:
                for perform in date_info.get("performInfo", []):
                    show_time = perform['name']
                    self.logger.info(f"\nLiveLab场次: {perform['name']}")

                    for plan in perform.get("seatPlans", []):
                        has_ticket = (not any(tag.get("tag") == "缺票登记" for tag in plan.get("tags", []))) or plan.get("display") == 1
                        price = plan.get('price')
                        status = "有票" if has_ticket else "无票"
                        target_price = "（目标价格）" if price in target_prices else ""
                        target_date = "（目标场次）" if any(date in show_time for date in target_dates) else ""
                        
                        self.logger.info(f"{plan['seatPlanName']} ({price}元): {status} {target_price}{target_date}")
                        
                        if has_ticket:
                            ticket_info = f"场次：{show_time}，{plan['seatPlanName']}，价格：{price}元"
                            available_tickets.append(ticket_info)
                            
                            if price in target_prices and any(date in show_time for date in target_dates):
                                found_target_ticket = True
                                self.logger.info(f"\n发现目标票价: {price}元")
                                if self.create_order(perform.get('id'), plan.get('seatPlanId'), price):
                                    subject = "LiveLab下单成功通知！"
                                    body = f"""
演出：{show_info.get('name')}
场馆：{show_info.get('venue')}
城市：{show_info.get('city')}

下单成功！
场次：{show_time}
票档：{plan['seatPlanName']}
价格：{price}元

请尽快支付！
"""
                                    self.notify(subject, body)
                                    return True

            if available_tickets and not found_target_ticket:
                subject = "LiveLab发现可用票务！"
                body = f"""
演出：{show_info.get('name')}
场馆：{show_info.get('venue')}
城市：{show_info.get('city')}

发现以下场次有票：

""" + "\n".join(available_tickets) + f"""
"""
                self.notify(subject, body)

            return found_target_ticket

        except Exception as e:
            self.logger.error(f"LiveLab检查失败: {str(e)}")
            return False

    def create_order(self, perform_id: str, seat_plan_id: str, price: int) -> bool:
        """创建订单"""
        try:
            order_url = "https://api.livelab.com.cn/order/app/center/v3/create"
            contact = self.livelab_config.get('contact', {})
            order_data = {
                "deliveryType": 1,
                "contactName": contact.get('name'),
                "contactPhone": contact.get('phone'),
                "combineTicketVos": None,
                "ordinaryTicketVos": None,
                "payment": price,
                "totalPrice": price,
                "performId": perform_id,
                "projectId": self.livelab_config.get('project_id'),
                "privilegeCodeList": [],
                "audienceCount": 1,
                "frequentIds": self.livelab_config.get('frequent_ids', []),
                "seatPlanIds": [seat_plan_id],
                "blackBox": ":0"
            }
            
            response = self.session.post(
                order_url,
                headers=self.headers,
                json=order_data,
                timeout=(5, 10)
            )
            
            result = response.json()
            if result.get("code") == 0:
                self.logger.info(f"下单成功！票价：{price}元")
                return True
            else:
                self.logger.error(f"下单失败: {result.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            self.logger.error(f"创建订单失败: {str(e)}")
            return False
