# 票务监控系统

自动监控LiveLab和猫眼平台的票务情况，发现目标票价时自动尝试下单并发送邮件通知。

## 功能特点

- 支持多平台监控（LiveLab、猫眼）
- 自动下单功能（LiveLab）
- 邮件通知
- 防封策略（随机UA、动态等待时间）
- 错误重试机制

## 使用方法

1. 安装依赖：
```
pip install -r requirements.txt
```

2. 修改配置文件 `config/config.yaml`：
   - 设置邮箱配置
   - 设置目标票价和场次
   - 设置联系人信息
   - 配置要监控的演唱会信息

3. 运行程序：
```
python src/main.py
```


## 配置说明

### 邮件配置
- smtp_server: SMTP服务器地址
- smtp_port: SMTP端口
- sender: 发件人邮箱
- password: 邮箱密码
- receivers: 收件人邮箱列表

### 监控配置
- interval: 监控间隔（秒）
- retry_times: 重试次数
- timeout: 请求超时时间
- error_wait_time: 错误后等待时间
- max_errors: 最大连续错误次数

### 猫眼配置
- shows: 要监控的演唱会列表
  - name: 演唱会名称
  - show_id: 演出ID
  - project_id: 项目ID
  - target_prices: 目标票价列表

### LiveLab配置
- project_id: 项目ID
- authorization: 认证token
- target_prices: 目标票价列表
- target_dates: 目标日期列表
- contact: 联系人信息

## 注意事项

- 请确保配置文件中的认证信息（token等）是最新的
- 建议使用代理IP避免被封
- 邮箱配置需要使用应用专用密码
- 程序每50次监控会自动休息2-5分钟
- 需要注意定期更新：
- 猫眼的 mtgsig 和 token
- LiveLab 的 authorization
- 目标演唱会的 ID 和票价信息

## 免责声明

1. 本项目仅供学习和研究使用，不得用于商业用途。
2. 使用本项目导致的任何问题，包括但不限于：
   - 账号被封禁
   - 订单异常
   - 财产损失
   - 信息泄露
   等一切风险由使用者自行承担。
3. 请遵守相关平台的使用条款和规则，不得利用本项目进行任何违法或不当行为。
4. 本项目不保证功能的完整性、可靠性和时效性。
5. 使用本项目即表示您同意本免责声明的所有条款。