import logging
import yaml
import os
from typing import Dict
import asyncio
import threading
import time

def setup_logging():
    """设置日志"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/monitor.log'),
            logging.StreamHandler()
        ]
    )

def load_config() -> Dict:
    """加载配置文件"""
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_monitor(monitor_class, config, urls):
    """运行单个监控器"""
    monitor = monitor_class(config)
    monitor.monitor(urls)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        config = load_config()
        monitors = []

        # 启动LiveLab监控
        if config['targets']['livelab']['enabled']:
            from monitors.livelab_monitor import LiveLabMonitor
            livelab_thread = threading.Thread(
                target=run_monitor,
                args=(LiveLabMonitor, config, config['targets']['livelab']['urls']),
                daemon=True
            )
            monitors.append(livelab_thread)
            
        # 启动猫眼监控
        if config['targets']['maoyan']['enabled']:
            from monitors.maoyan_monitor import MaoyanMonitor
            maoyan_thread = threading.Thread(
                target=run_monitor,
                args=(MaoyanMonitor, config, config['targets']['maoyan']['urls']),
                daemon=True
            )
            monitors.append(maoyan_thread)

        # 启动所有监控线程
        for monitor in monitors:
            monitor.start()

        # 等待所有线程运行
        try:
            while True:
                for monitor in monitors:
                    if not monitor.is_alive():
                        logger.error("监控线程意外退出，重新启动...")
                        monitor.start()
                logger.info("所有监控正在运行...")
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在退出...")
            
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")

if __name__ == "__main__":
    main() 