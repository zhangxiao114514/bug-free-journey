# 系统监控功能使用指南

本指南将帮助您了解和使用企业微信法律客服系统的监控功能，包括系统运行状态监控、业务数据监控、告警机制和监控数据可视化。

## 一、监控功能概述

系统监控模块提供以下功能：

- **系统指标监控**：CPU使用率、内存使用率、磁盘使用率
- **服务指标监控**：服务状态、响应时间
- **业务指标监控**：消息处理量、咨询量、案例量、满意度评分
- **告警机制**：系统异常时自动发送告警通知
- **监控数据可视化**：通过Prometheus和Grafana查看监控数据

## 二、监控配置

### 1. 配置文件设置

在 `config/config.ini` 文件中，`[monitoring]` 部分包含监控相关的配置：

```ini
[monitoring]
# 监控配置
enabled = true
metrics_port = 8001
alert_enabled = true
alert_threshold_response_time = 5
alert_threshold_error_rate = 0.1
alert_notification_channels = wecom,email
```

**配置项说明**：
- `enabled`：是否启用监控功能
- `metrics_port`：Prometheus指标服务器端口
- `alert_enabled`：是否启用告警机制
- `alert_threshold_response_time`：响应时间告警阈值（秒）
- `alert_threshold_error_rate`：错误率告警阈值
- `alert_notification_channels`：告警通知渠道（wecom,email）

### 2. 启动监控服务

监控服务会在系统启动时自动启动，也可以通过以下方式手动启动：

```python
from modules.system.monitoring import start_monitoring
start_monitoring()
```

## 三、监控数据访问

### 1. Prometheus指标

系统启动后，Prometheus指标可以通过以下地址访问：

```
http://your-server:8001/metrics
```

**主要指标**：
- `wecom_messages_total`：处理的消息总数
- `wecom_messages_errors_total`：消息处理错误总数
- `wecom_message_processing_seconds`：消息处理时间
- `system_cpu_usage_percent`：系统CPU使用率
- `system_memory_usage_percent`：系统内存使用率
- `system_disk_usage_percent`：系统磁盘使用率
- `service_up`：服务状态
- `service_response_time_seconds`：服务响应时间
- `consultations_total`：咨询总数
- `cases_total`：案例总数
- `average_satisfaction_score`：平均满意度评分

### 2. 仪表盘数据

通过系统管理仪表盘可以查看监控数据：

```python
from modules.system.dashboard import get_dashboard_data
data = get_dashboard_data(duration=24)  # 获取24小时内的数据
```

## 四、告警机制

### 1. 告警类型

系统会监控以下情况并发送告警：

- **系统资源告警**：CPU使用率 > 80%
- **系统资源告警**：内存使用率 > 80%
- **系统资源告警**：磁盘使用率 > 90%
- **服务告警**：响应时间 > 5秒
- **业务告警**：消息量异常增长（今日消息量是昨日的5倍以上）

### 2. 告警通知

告警通知会通过以下渠道发送：

- **企业微信**：发送告警消息到企业微信
- **邮件**：发送告警邮件到管理员邮箱

### 3. 告警历史

告警历史可以通过以下方式获取：

```python
from modules.system.monitoring import system_monitor
alerts = system_monitor.get_monitoring_data()['alerts']
```

## 五、系统状态查看

### 1. 系统状态API

系统状态可以通过以下API获取：

```python
from modules.system.monitoring import system_monitor
status = system_monitor.get_system_status()
```

**返回数据示例**：

```json
{
  "timestamp": "2026-02-12T21:46:44.290Z",
  "monitoring_enabled": true,
  "service_status": "up",
  "metrics_port": 8001,
  "alert_enabled": true,
  "cpu_usage": 10.5,
  "memory_usage": 65.2,
  "disk_usage": 45.8,
  "response_time": 0.3
}
```

### 2. 服务管理

通过系统管理仪表盘可以管理监控服务：

- **启动监控服务**：开始收集监控数据
- **停止监控服务**：停止收集监控数据

## 六、监控数据可视化

### 1. Prometheus配置

1. 安装Prometheus：https://prometheus.io/download/

2. 配置Prometheus，添加系统监控目标：

```yaml
scrape_configs:
  - job_name: 'wecom_legal_service'
    static_configs:
      - targets: ['localhost:8001']
```

3. 启动Prometheus：

```bash
./prometheus --config.file=prometheus.yml
```

4. 访问Prometheus UI：

```
http://localhost:9090
```

### 2. Grafana配置

1. 安装Grafana：https://grafana.com/grafana/download

2. 启动Grafana：

```bash
./grafana-server
```

3. 访问Grafana UI：

```
http://localhost:3000
```

4. 添加Prometheus数据源：
   - 数据源类型：Prometheus
   - URL：http://localhost:9090

5. 导入仪表盘模板：
   - 可以使用Grafana的导入功能，导入适合监控企业应用的仪表盘模板

## 七、常见问题排查

### 1. 监控服务无法启动

**可能原因**：
- 端口被占用：`metrics_port` 配置的端口已被其他服务占用
- 依赖缺失：缺少 `prometheus-client` 或 `psutil` 依赖

**解决方案**：
- 更改 `metrics_port` 配置为其他可用端口
- 安装缺失的依赖：`pip install prometheus-client psutil`

### 2. 告警通知未收到

**可能原因**：
- 告警通知渠道配置错误
- 企业微信或邮件配置不正确

**解决方案**：
- 检查 `alert_notification_channels` 配置
- 检查企业微信和邮件的配置

### 3. 监控数据不准确

**可能原因**：
- 监控服务未正常运行
- 数据收集间隔设置不合理

**解决方案**：
- 确保监控服务正常运行
- 调整监控数据收集间隔（默认1分钟）

## 八、最佳实践

1. **设置合理的告警阈值**：根据系统实际运行情况调整告警阈值
2. **定期查看监控数据**：通过Prometheus和Grafana定期查看系统运行状态
3. **配置监控仪表盘**：创建适合业务需求的监控仪表盘
4. **备份监控数据**：定期备份重要的监控数据
5. **优化系统资源**：根据监控数据优化系统资源配置

## 九、联系支持

如果您在使用监控功能时遇到问题，可以：

1. 查看系统日志获取详细错误信息
2. 检查监控配置是否正确
3. 联系系统管理员获取技术支持
