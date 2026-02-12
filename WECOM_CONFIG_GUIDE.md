# 企业微信法律客服系统配置指南

本指南将帮助您完成企业微信法律客服系统的配置，包括在企业微信后台获取必要的配置参数，以及在系统中正确设置这些参数。系统支持企业微信消息处理、智能问答、案例管理、合同模板管理、系统监控等功能。

## 一、企业微信后台配置步骤

### 1. 登录企业微信管理后台

访问企业微信管理后台：[https://work.weixin.qq.com/](https://work.weixin.qq.com/)

使用企业管理员账号登录。

### 2. 创建应用

1. 进入「应用管理」→「自建」→「创建应用」
2. 填写应用信息：
   - 应用名称：法律客服系统
   - 应用描述：企业微信法律智能客服系统
   - 可见范围：选择需要使用该应用的部门或成员
3. 点击「创建应用」按钮

### 3. 获取应用凭证

创建应用后，在应用详情页可以获取以下信息：

- **AgentId**：应用ID
- **Secret**：应用密钥（需要点击「查看」按钮获取）

### 4. 获取企业ID

在企业微信管理后台的「我的企业」→「企业信息」页面，可以找到：

- **企业ID**（CorpID）

### 5. 配置回调URL

1. 在应用详情页，找到「开发者接口」部分
2. 点击「设置」按钮，进入接口配置页面
3. 填写以下信息：
   - **URL**：`http://your-server-domain:8000/api/wecom/callback`
   - **Token**：自定义字符串，用于验证消息来源
   - **EncodingAESKey**：点击「随机生成」按钮获取
4. 点击「保存」按钮

### 6. 权限设置

1. 在应用详情页，找到「权限管理」部分
2. 确保应用拥有以下权限：
   - 消息发送权限
   - 通讯录访问权限（可选）

## 二、系统配置文件设置

### 1. 打开配置文件

编辑 `config/config.ini` 文件，找到 `[wecom]` 部分：

```ini
[wecom]
# 企业微信配置
corp_id =
app_id =
app_secret =
token =
aes_key =
encoding_aes_key =
agent_id =
```

### 2. 填写配置参数

根据企业微信后台获取的信息，填写以下参数：

- **corp_id**：企业ID（CorpID）
- **app_secret**：应用密钥（Secret）
- **agent_id**：应用ID（AgentId）
- **token**：回调URL中设置的Token
- **encoding_aes_key**：回调URL中设置的EncodingAESKey

示例配置：

```ini
[wecom]
# 企业微信配置
corp_id = ww1234567890abcdef
app_id = 1000001
app_secret = abcdefghijklmnopqrstuvwxyz123456
 token = your_custom_token
 aes_key =
encoding_aes_key = abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz12
agent_id = 1000001
```

### 3. 设置服务类型

在 `[general]` 部分，确保 `service_type` 设置为 `wecom`：

```ini
[general]
# 系统基本配置
system_name = 微信法律客服系统
system_version = 1.0.0
debug = true
service_type = wecom  # wechat 或 wecom
```

## 三、启动企业微信客服系统

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动系统

```bash
# 启动Web服务
python main.py

# 或使用uvicorn直接启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 验证配置

系统启动后，可以通过以下方式验证企业微信配置是否正确：

1. 运行测试脚本：
   ```bash
   python test_wecom_service.py
   ```

2. 在企业微信中向应用发送消息，系统应该能够自动回复

## 四、常见问题排查

### 1. 访问令牌获取失败

- 检查 `corp_id` 和 `app_secret` 是否正确
- 确保应用已经启用
- 检查网络连接是否正常

### 2. 消息发送失败

- 检查 `agent_id` 是否正确
- 确保用户在应用的可见范围内
- 检查企业微信后台是否有发送消息的权限

### 3. 消息接收失败

- 检查回调URL是否可以正常访问
- 确保 `token` 和 `encoding_aes_key` 配置正确
- 检查系统日志中是否有相关错误信息

### 4. 智能问答不工作

- 确保知识库已经初始化
- 检查AI模型是否正确加载
- 查看系统日志中的错误信息

## 五、配置示例

以下是一个完整的企业微信配置示例：

```ini
[wecom]
# 企业微信配置
corp_id = ww1234567890abcdef
app_id = 1000001
app_secret = abcdefghijklmnopqrstuvwxyz123456
 token = legal_service_token
 aes_key =
encoding_aes_key = abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz12
agent_id = 1000001
```

## 六、联系支持

如果您在配置过程中遇到问题，可以：

1. 查看系统日志获取详细错误信息
2. 检查企业微信开发者文档：[https://developer.work.weixin.qq.com/document/path/90664](https://developer.work.weixin.qq.com/document/path/90664)
3. 联系系统管理员获取技术支持

---

**注意**：企业微信配置参数包含敏感信息，请妥善保管，不要泄露给无关人员。
