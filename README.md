[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/zhangxiao114514/bug-free-journey)

# 企业微信法律客服系统

## 项目概述

企业微信法律客服系统是一个基于Python开发的综合性法律客服解决方案，专为企业微信（WeCom）平台设计，提供智能法律咨询、案例管理、合同模板管理、系统监控等功能。

## 核心功能

### 1. 消息处理模块
- 企业微信消息接收与发送
- 消息分类与优先级管理
- 消息历史记录与查询

### 2. 知识库与智能问答
- 法律知识库管理
- 基于BERT和TF-IDF的混合检索模型
- 智能法律问答系统

### 3. 客户管理
- 客户信息管理
- 客户咨询历史
- 客户标签与分类

### 4. 案例管理
- 案例创建与管理
- 案例标签与分类
- 案例进度跟踪
- 案例文档管理

### 5. 合同模板管理
- 合同模板创建与管理
- 合同生成与预览
- 合同签名管理

### 6. 咨询流程
- 咨询预约与安排
- 咨询记录与跟进
- 咨询结果评估

### 7. 文档处理
- 法律文档上传与管理
- 文档分类与检索
- 文档版本控制

### 8. 系统管理
- 用户权限管理
- 系统配置管理
- 服务监控与告警
- 系统管理仪表盘

### 9. 通知模块
- 企业微信消息通知
- 系统告警通知
- 重要事件提醒

### 10. 数据统计
- 咨询量统计
- 案例处理统计
- 系统性能统计

### 11. 安全合规
- 数据加密存储
- 访问权限控制
- 操作日志记录

## 技术栈

- **后端框架**: Python 3.8+, FastAPI
- **数据库**: MySQL, Redis
- **AI模型**: BERT, TF-IDF
- **监控**: Prometheus, Grafana
- **ORM**: SQLAlchemy
- **API**: 企业微信API
- **缓存**: Redis
- **消息队列**: Redis
- **监控**: prometheus-client, psutil

## 系统架构

```
├── config/              # 配置文件
├── modules/             # 功能模块
│   ├── message/         # 消息处理
│   ├── knowledge/       # 知识库
│   ├── qa/              # 智能问答
│   ├── customer/        # 客户管理
│   ├── case/            # 案例管理
│   ├── contract/        # 合同模板管理
│   ├── consultation/    # 咨询流程
│   ├── document/        # 文档处理
│   ├── system/          # 系统管理
│   ├── notification/    # 通知模块
│   ├── analytics/       # 数据统计
│   └── gui/             # GUI界面
├── utils/               # 工具类
├── main.py              # 主入口
├── requirements.txt     # 依赖文件
├── README.md            # 项目说明
├── WECOM_CONFIG_GUIDE.md # 企业微信配置指南
├── SYSTEM_MONITORING_GUIDE.md # 系统监控指南
└── LEGAL_CASE_MANAGEMENT_GUIDE.md # 案例管理指南
```

## 安装与部署

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd legal_wechat_service

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

1. 复制并修改配置文件
   ```bash
   cp config/config.ini.example config/config.ini
   ```

2. 填写企业微信配置信息（详见 WECOM_CONFIG_GUIDE.md）

3. 配置数据库连接信息

### 3. 数据库初始化

```bash
# 运行数据库迁移脚本
python utils/database.py
```

### 4. 启动服务

```bash
# 启动主服务
python main.py

# 或使用 uvicorn 启动（推荐）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 监控与维护

- **系统监控**: 访问 http://localhost:8000/metrics 获取Prometheus监控指标
- **系统仪表盘**: 访问 http://localhost:8000/dashboard 查看系统状态
- **日志管理**: 系统日志存储在 logs/ 目录

详细监控配置请参考 SYSTEM_MONITORING_GUIDE.md

## 使用指南

### 案例管理

详细使用指南请参考 LEGAL_CASE_MANAGEMENT_GUIDE.md

### 合同模板管理

1. 创建合同模板
2. 基于模板生成合同
3. 管理合同签名流程

### 智能问答

1. 向系统发送法律问题
2. 系统自动检索知识库并生成回答
3. 对于复杂问题，可转人工处理

## API文档

启动服务后，可访问以下地址查看API文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 安全注意事项

1. 企业微信AppSecret请妥善保管，避免泄露
2. 定期更新系统密码和访问令牌
3. 开启系统监控，及时发现异常情况
4. 定期备份数据库，防止数据丢失

## 技术支持

如有问题，请联系技术支持团队或查看相关文档。

## 版本信息

- 版本: 1.0.0
- 发布日期: 2023-10-15
- 支持平台: Windows, Linux, macOS

