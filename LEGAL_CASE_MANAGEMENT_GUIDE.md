# 案例管理功能使用指南

本指南将帮助您了解和使用企业微信法律客服系统的案例管理功能，包括案例的创建、查询、更新、删除，以及案例标签管理、案例文档管理、案例进度管理等功能。

## 一、案例管理功能概述

案例管理模块提供以下功能：

- **案例创建**：创建新的法律案例，包括案例基本信息、类型、优先级等
- **案例查询**：根据各种条件查询案例，如状态、类型、客户等
- **案例更新**：更新案例信息，如状态、处理人、描述等
- **案例删除**：删除不需要的案例
- **案例标签管理**：为案例添加和管理标签，便于分类和检索
- **案例文档管理**：为案例添加相关文档，如合同、证据等
- **案例进度管理**：跟踪案例处理进度，记录每个阶段的状态
- **案例检索和推荐**：根据关键词搜索案例，推荐相似案例

## 二、案例创建

### 1. 通过API创建案例

```python
from modules.case.case_manager import case_manager

# 创建案例数据
case_data = {
    'title': '劳动合同纠纷案例',
    'description': '员工因公司拖欠工资提起劳动仲裁',
    'case_type': 'labor',
    'priority': 1,
    'customer_id': 1,
    'user_id': 2,
    'tags': ['劳动合同', '工资纠纷', '劳动仲裁']
}

# 创建案例
case = case_manager.create_case(case_data)
print(f"创建案例成功: {case.case_id} - {case.title}")
```

### 2. 案例类型说明

案例类型包括：
- `contract`：合同纠纷
- `labor`：劳动纠纷
- `civil`：民事诉讼
- `criminal`：刑事辩护
- `property`：财产权利
- `marriage`：婚姻家庭
- `intellectual`：知识产权
- `administrative`：行政法
- `company`：公司法
- `other`：其他

## 三、案例查询

### 1. 根据ID查询案例

```python
from modules.case.case_manager import case_manager

# 根据ID查询案例
case = case_manager.get_case(1)
if case:
    print(f"案例信息: {case.title} - {case.status}")
else:
    print("案例不存在")

# 根据案例编号查询案例
case_by_id = case_manager.get_case_by_case_id("CASE_20260212123456_abc123")
if case_by_id:
    print(f"案例信息: {case_by_id.title} - {case_by_id.status}")
```

### 2. 批量查询案例

```python
from modules.case.case_manager import case_manager

# 查询所有案例
all_cases = case_manager.list_cases()
print(f"总案例数: {len(all_cases)}")

# 根据状态查询案例
pending_cases = case_manager.list_cases(status="pending")
print(f"待处理案例数: {len(pending_cases)}")

# 根据类型查询案例
labor_cases = case_manager.list_cases(case_type="labor")
print(f"劳动纠纷案例数: {len(labor_cases)}")

# 根据客户查询案例
customer_cases = case_manager.list_cases(customer_id=1)
print(f"客户1的案例数: {len(customer_cases)}")

# 根据处理人查询案例
user_cases = case_manager.list_cases(user_id=2)
print(f"处理人2的案例数: {len(user_cases)}")
```

## 四、案例更新

### 1. 更新案例基本信息

```python
from modules.case.case_manager import case_manager

# 更新案例数据
update_data = {
    'title': '劳动合同纠纷案例（更新）',
    'description': '员工因公司拖欠工资提起劳动仲裁，要求支付拖欠工资和经济补偿金',
    'priority': 2,
    'tags': ['劳动合同', '工资纠纷', '劳动仲裁', '经济补偿金']
}

# 更新案例
updated_case = case_manager.update_case(1, update_data)
print(f"更新案例成功: {updated_case.title}")
```

### 2. 分配案例

```python
from modules.case.case_manager import case_manager

# 分配案例给处理人
assigned_case = case_manager.assign_case(1, 3)  # 分配给用户ID为3的处理人
print(f"分配案例成功: {assigned_case.title} -> 处理人ID: {assigned_case.user_id}")
```

### 3. 完成案例

```python
from modules.case.case_manager import case_manager

# 完成案例
completed_case = case_manager.complete_case(
    1, 
    satisfaction_score=5, 
    feedback="处理结果满意，律师专业负责"
)
print(f"完成案例成功: {completed_case.title} - 满意度: {completed_case.satisfaction_score}")
```

## 五、案例标签管理

### 1. 添加和更新标签

在创建或更新案例时，可以通过 `tags` 参数添加或更新标签：

```python
# 创建案例时添加标签
case_data = {
    'title': '案例标题',
    'description': '案例描述',
    'case_type': 'contract',
    'tags': ['标签1', '标签2', '标签3']
}

# 更新案例时更新标签
update_data = {
    'tags': ['标签1', '标签2', '标签4', '标签5']  # 会替换原有标签
}
```

## 六、案例文档管理

### 1. 添加案例文档

```python
from modules.case.case_manager import case_manager

# 文档数据
document_data = {
    'document_name': '劳动合同',
    'document_path': '/path/to/contract.pdf',
    'document_type': 'pdf',
    'description': '员工与公司签订的劳动合同',
    'uploaded_by': 2
}

# 添加文档
document = case_manager.add_case_document(1, document_data)
print(f"添加文档成功: {document.document_name}")
```

## 七、案例进度管理

### 1. 更新案例进度

```python
from modules.case.case_manager import case_manager

# 更新进度
progress = case_manager.update_case_progress(
    1, 
    stage="调查取证", 
    status="completed", 
    description="已收集相关证据，包括劳动合同、工资条、考勤记录等"
)
print(f"更新进度成功: {progress.stage} - {progress.status}")
```

### 2. 进度状态说明

进度状态包括：
- `in_progress`：进行中
- `completed`：已完成
- `pending`：待处理
- `cancelled`：已取消

## 八、案例检索和推荐

### 1. 搜索案例

```python
from modules.case.case_manager import case_manager

# 搜索案例
search_results = case_manager.search_cases("劳动合同纠纷")
print(f"搜索结果数量: {len(search_results)}")
for case in search_results:
    print(f"- {case.title} ({case.case_type})")
```

### 2. 推荐相似案例

```python
from modules.case.case_manager import case_manager

# 推荐相似案例
recommendations = case_manager.recommend_cases(1, limit=5)
print(f"推荐案例数量: {len(recommendations)}")
for case in recommendations:
    print(f"- {case.title} ({case.case_type})")
```

## 九、案例统计

### 1. 获取待处理案例

```python
from modules.case.case_manager import case_manager

# 获取待处理案例
pending_cases = case_manager.get_pending_cases()
print(f"待处理案例数: {len(pending_cases)}")
```

### 2. 获取处理中案例

```python
from modules.case.case_manager import case_manager

# 获取处理中案例
processing_cases = case_manager.get_processing_cases()
print(f"处理中案例数: {len(processing_cases)}")
```

### 3. 获取已完成案例

```python
from modules.case.case_manager import case_manager

# 获取已完成案例
completed_cases = case_manager.get_completed_cases()
print(f"已完成案例数: {len(completed_cases)}")
```

## 十、常见问题排查

### 1. 案例创建失败

**可能原因**：
- 缺少必填字段：`title`、`case_type`、`customer_id` 是必填字段
- 客户ID不存在：`customer_id` 对应的客户不存在
- 处理人ID不存在：`user_id` 对应的用户不存在

**解决方案**：
- 确保提供所有必填字段
- 确保客户ID和处理人ID正确存在

### 2. 案例查询无结果

**可能原因**：
- 案例ID不存在：查询的案例ID或编号不存在
- 查询条件过于严格：过滤条件导致无匹配结果

**解决方案**：
- 检查案例ID或编号是否正确
- 调整查询条件，使用更宽松的过滤条件

### 3. 案例文档添加失败

**可能原因**：
- 案例不存在：`case_id` 对应的案例不存在
- 文件路径无效：`document_path` 指向的文件不存在

**解决方案**：
- 确保案例ID正确存在
- 确保文件路径有效

## 十一、最佳实践

1. **规范案例信息**：创建案例时，提供详细的标题和描述，便于后续查询和管理
2. **合理使用标签**：为案例添加合适的标签，便于分类和检索
3. **及时更新进度**：定期更新案例进度，确保案例处理状态透明
4. **完整文档管理**：为案例添加所有相关文档，便于案例分析和参考
5. **利用案例推荐**：在处理新案例时，参考系统推荐的相似案例，提高处理效率
6. **定期清理案例**：定期清理不需要的案例，保持系统整洁

## 十二、联系支持

如果您在使用案例管理功能时遇到问题，可以：

1. 查看系统日志获取详细错误信息
2. 检查案例数据是否正确
3. 联系系统管理员获取技术支持
