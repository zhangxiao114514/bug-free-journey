import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.database import get_db
from modules.contract.models import ContractTemplate, Contract, ContractSignature, ContractStatus, ContractType

logger = logging.getLogger(__name__)

class ContractManager:
    """合同管理器"""
    
    def __init__(self):
        pass
    
    def create_template(self, data: Dict[str, Any]) -> ContractTemplate:
        """创建合同模板
        
        Args:
            data: 模板数据
            
        Returns:
            创建的模板
        """
        db = next(get_db())
        try:
            # 生成模板编号
            template_id = f"TEMPLATE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
            
            # 处理变量定义
            variables = data.get('variables', {})
            variables_json = json.dumps(variables, ensure_ascii=False) if variables else None
            
            # 创建模板
            template = ContractTemplate(
                template_id=template_id,
                name=data['name'],
                description=data.get('description'),
                contract_type=data['contract_type'],
                status=data.get('status', ContractStatus.DRAFT),
                content=data['content'],
                variables=variables_json,
                created_by=data.get('created_by'),
                updated_by=data.get('updated_by')
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            logger.info(f"创建合同模板成功: {template.name}")
            return template
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建合同模板时出错: {e}")
            raise
        finally:
            db.close()
    
    def clone_template(self, template_id: int, new_name: str, created_by: Optional[str] = None) -> ContractTemplate:
        """克隆合同模板
        
        Args:
            template_id: 模板ID
            new_name: 新模板名称
            created_by: 创建人
            
        Returns:
            创建的模板
        """
        db = next(get_db())
        try:
            # 获取原模板
            original_template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
            if not original_template:
                raise ValueError(f"模板不存在: {template_id}")
            
            # 生成新模板编号
            template_id = f"TEMPLATE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
            
            # 创建新模板
            template = ContractTemplate(
                template_id=template_id,
                name=new_name,
                description=original_template.description,
                contract_type=original_template.contract_type,
                status=ContractStatus.DRAFT,
                content=original_template.content,
                variables=original_template.variables,
                created_by=created_by or original_template.created_by,
                updated_by=created_by or original_template.updated_by
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            logger.info(f"克隆合同模板成功: {template.name}")
            return template
            
        except Exception as e:
            db.rollback()
            logger.error(f"克隆合同模板时出错: {e}")
            raise
        finally:
            db.close()
    
    def batch_update_templates(self, template_ids: List[int], data: Dict[str, Any]) -> int:
        """批量更新合同模板
        
        Args:
            template_ids: 模板ID列表
            data: 更新数据
            
        Returns:
            更新的模板数量
        """
        db = next(get_db())
        try:
            # 更新模板
            templates = db.query(ContractTemplate).filter(ContractTemplate.id.in_(template_ids)).all()
            updated_count = 0
            
            for template in templates:
                # 更新字段
                for key, value in data.items():
                    if key == 'variables':
                        # 处理变量定义
                        template.variables = json.dumps(value, ensure_ascii=False) if value else None
                    elif hasattr(template, key):
                        setattr(template, key, value)
                
                template.updated_at = datetime.now()
                updated_count += 1
            
            db.commit()
            logger.info(f"批量更新合同模板成功: {updated_count} 个模板")
            return updated_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"批量更新合同模板时出错: {e}")
            raise
        finally:
            db.close()
    
    def get_template(self, template_id: int) -> Optional[ContractTemplate]:
        """获取合同模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            模板对象
        """
        db = next(get_db())
        try:
            return db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
        finally:
            db.close()
    
    def get_template_by_template_id(self, template_id: str) -> Optional[ContractTemplate]:
        """通过模板编号获取模板
        
        Args:
            template_id: 模板编号
            
        Returns:
            模板对象
        """
        db = next(get_db())
        try:
            return db.query(ContractTemplate).filter(ContractTemplate.template_id == template_id).first()
        finally:
            db.close()
    
    def list_templates(self, **filters) -> List[ContractTemplate]:
        """列出合同模板
        
        Args:
            filters: 过滤条件
            
        Returns:
            模板列表
        """
        db = next(get_db())
        try:
            query = db.query(ContractTemplate)
            
            # 应用过滤条件
            if 'status' in filters:
                query = query.filter(ContractTemplate.status == filters['status'])
            if 'contract_type' in filters:
                query = query.filter(ContractTemplate.contract_type == filters['contract_type'])
            
            # 排序
            query = query.order_by(ContractTemplate.created_at.desc())
            
            return query.all()
        finally:
            db.close()
    
    def update_template(self, template_id: int, data: Dict[str, Any]) -> ContractTemplate:
        """更新合同模板
        
        Args:
            template_id: 模板ID
            data: 更新数据
            
        Returns:
            更新后的模板
        """
        db = next(get_db())
        try:
            # 查找模板
            template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            # 更新字段
            for key, value in data.items():
                if key == 'variables':
                    # 处理变量定义
                    template.variables = json.dumps(value, ensure_ascii=False) if value else None
                elif hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.now()
            db.commit()
            db.refresh(template)
            
            logger.info(f"更新合同模板成功: {template.name}")
            return template
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新合同模板时出错: {e}")
            raise
        finally:
            db.close()
    
    def delete_template(self, template_id: int) -> bool:
        """删除合同模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            是否删除成功
        """
        db = next(get_db())
        try:
            # 查找模板
            template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            # 检查是否有使用该模板的合同
            contract_count = db.query(Contract).filter(Contract.template_id == template_id).count()
            if contract_count > 0:
                raise ValueError(f"该模板已被使用，无法删除（使用次数: {contract_count}）")
            
            # 删除模板
            db.delete(template)
            db.commit()
            
            logger.info(f"删除合同模板成功: {template.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除合同模板时出错: {e}")
            raise
        finally:
            db.close()
    
    def activate_template(self, template_id: int) -> ContractTemplate:
        """激活合同模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            激活后的模板
        """
        return self.update_template(template_id, {'status': ContractStatus.ACTIVE})
    
    def archive_template(self, template_id: int) -> ContractTemplate:
        """归档合同模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            归档后的模板
        """
        return self.update_template(template_id, {'status': ContractStatus.ARCHIVED})
    
    def generate_contract(self, data: Dict[str, Any]) -> Contract:
        """生成合同
        
        Args:
            data: 合同数据，包含template_id和variables
            
        Returns:
            生成的合同
        """
        db = next(get_db())
        try:
            # 获取模板
            template = db.query(ContractTemplate).filter(ContractTemplate.id == data['template_id']).first()
            if not template:
                raise ValueError(f"模板不存在: {data['template_id']}")
            
            # 生成合同编号
            contract_id = f"CONTRACT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
            
            # 替换变量
            variables = data.get('variables', {})
            content = self._replace_variables(template.content, variables)
            
            # 创建合同
            contract = Contract(
                contract_id=contract_id,
                template_id=template.id,
                name=data.get('name', template.name),
                parties=json.dumps(data.get('parties', {}), ensure_ascii=False) if data.get('parties') else None,
                variables=json.dumps(variables, ensure_ascii=False),
                content=content,
                status="draft",
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                customer_id=data.get('customer_id'),
                user_id=data.get('user_id')
            )
            
            db.add(contract)
            db.commit()
            db.refresh(contract)
            
            logger.info(f"生成合同成功: {contract.name}")
            return contract
            
        except Exception as e:
            db.rollback()
            logger.error(f"生成合同时出错: {e}")
            raise
        finally:
            db.close()
    
    def _replace_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """替换变量
        
        Args:
            content: 模板内容
            variables: 变量值
            
        Returns:
            替换后的内容
        """
        result = content
        for key, value in variables.items():
            # 替换 {{variable}} 格式的占位符
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def get_contract(self, contract_id: int) -> Optional[Contract]:
        """获取合同
        
        Args:
            contract_id: 合同ID
            
        Returns:
            合同对象
        """
        db = next(get_db())
        try:
            return db.query(Contract).filter(Contract.id == contract_id).first()
        finally:
            db.close()
    
    def get_contract_by_contract_id(self, contract_id: str) -> Optional[Contract]:
        """通过合同编号获取合同
        
        Args:
            contract_id: 合同编号
            
        Returns:
            合同对象
        """
        db = next(get_db())
        try:
            return db.query(Contract).filter(Contract.contract_id == contract_id).first()
        finally:
            db.close()
    
    def list_contracts(self, **filters) -> List[Contract]:
        """列出合同
        
        Args:
            filters: 过滤条件
            
        Returns:
            合同列表
        """
        db = next(get_db())
        try:
            query = db.query(Contract)
            
            # 应用过滤条件
            if 'status' in filters:
                query = query.filter(Contract.status == filters['status'])
            if 'customer_id' in filters:
                query = query.filter(Contract.customer_id == filters['customer_id'])
            if 'user_id' in filters:
                query = query.filter(Contract.user_id == filters['user_id'])
            if 'template_id' in filters:
                query = query.filter(Contract.template_id == filters['template_id'])
            
            # 排序
            query = query.order_by(Contract.created_at.desc())
            
            return query.all()
        finally:
            db.close()
    
    def update_contract(self, contract_id: int, data: Dict[str, Any]) -> Contract:
        """更新合同
        
        Args:
            contract_id: 合同ID
            data: 更新数据
            
        Returns:
            更新后的合同
        """
        db = next(get_db())
        try:
            # 查找合同
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"合同不存在: {contract_id}")
            
            # 更新字段
            for key, value in data.items():
                if key in ['parties', 'variables']:
                    # 处理JSON字段
                    setattr(contract, key, json.dumps(value, ensure_ascii=False) if value else None)
                elif hasattr(contract, key):
                    setattr(contract, key, value)
            
            contract.updated_at = datetime.now()
            db.commit()
            db.refresh(contract)
            
            logger.info(f"更新合同成功: {contract.name}")
            return contract
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新合同时出错: {e}")
            raise
        finally:
            db.close()
    
    def add_contract_signature(self, contract_id: int, data: Dict[str, Any]) -> ContractSignature:
        """添加合同签名
        
        Args:
            contract_id: 合同ID
            data: 签名数据
            
        Returns:
            创建的签名
        """
        db = next(get_db())
        try:
            # 检查合同是否存在
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"合同不存在: {contract_id}")
            
            # 创建签名
            signature = ContractSignature(
                contract_id=contract_id,
                signer_name=data['signer_name'],
                signer_role=data.get('signer_role'),
                signature_data=data.get('signature_data')
            )
            
            db.add(signature)
            db.commit()
            db.refresh(signature)
            
            logger.info(f"添加合同签名成功: {signature.signer_name}")
            return signature
            
        except Exception as e:
            db.rollback()
            logger.error(f"添加合同签名时出错: {e}")
            raise
        finally:
            db.close()
    
    def submit_contract_for_approval(self, contract_id: int, approver_id: int, reason: Optional[str] = None) -> Contract:
        """提交合同审批
        
        Args:
            contract_id: 合同ID
            approver_id: 审批人ID
            reason: 审批原因
            
        Returns:
            更新后的合同
        """
        db = next(get_db())
        try:
            # 检查合同是否存在
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"合同不存在: {contract_id}")
            
            # 更新合同状态
            contract.status = "pending_approval"
            contract.approver_id = approver_id
            contract.approval_reason = reason
            contract.updated_at = datetime.now()
            
            db.commit()
            db.refresh(contract)
            
            logger.info(f"提交合同审批成功: {contract.name}")
            return contract
            
        except Exception as e:
            db.rollback()
            logger.error(f"提交合同审批时出错: {e}")
            raise
        finally:
            db.close()
    
    def approve_contract(self, contract_id: int, approver_id: int, comment: Optional[str] = None) -> Contract:
        """审批合同
        
        Args:
            contract_id: 合同ID
            approver_id: 审批人ID
            comment: 审批意见
            
        Returns:
            更新后的合同
        """
        db = next(get_db())
        try:
            # 检查合同是否存在
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"合同不存在: {contract_id}")
            
            # 检查审批权限
            if contract.approver_id != approver_id:
                raise ValueError("无权限审批此合同")
            
            # 更新合同状态
            contract.status = "approved"
            contract.approval_comment = comment
            contract.approval_time = datetime.now()
            contract.updated_at = datetime.now()
            
            db.commit()
            db.refresh(contract)
            
            logger.info(f"审批合同成功: {contract.name}")
            return contract
            
        except Exception as e:
            db.rollback()
            logger.error(f"审批合同时出错: {e}")
            raise
        finally:
            db.close()
    
    def reject_contract(self, contract_id: int, approver_id: int, comment: Optional[str] = None) -> Contract:
        """拒绝合同
        
        Args:
            contract_id: 合同ID
            approver_id: 审批人ID
            comment: 拒绝原因
            
        Returns:
            更新后的合同
        """
        db = next(get_db())
        try:
            # 检查合同是否存在
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                raise ValueError(f"合同不存在: {contract_id}")
            
            # 检查审批权限
            if contract.approver_id != approver_id:
                raise ValueError("无权限审批此合同")
            
            # 更新合同状态
            contract.status = "rejected"
            contract.approval_comment = comment
            contract.approval_time = datetime.now()
            contract.updated_at = datetime.now()
            
            db.commit()
            db.refresh(contract)
            
            logger.info(f"拒绝合同成功: {contract.name}")
            return contract
            
        except Exception as e:
            db.rollback()
            logger.error(f"拒绝合同时出错: {e}")
            raise
        finally:
            db.close()
    
    def batch_generate_contracts(self, template_id: int, variables_list: List[Dict[str, Any]], user_id: Optional[int] = None) -> List[Contract]:
        """批量生成合同
        
        Args:
            template_id: 模板ID
            variables_list: 变量列表
            user_id: 用户ID
            
        Returns:
            生成的合同列表
        """
        db = next(get_db())
        try:
            # 获取模板
            template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            contracts = []
            for variables in variables_list:
                # 生成合同编号
                contract_id = f"CONTRACT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
                
                # 替换变量
                content = self._replace_variables(template.content, variables)
                
                # 创建合同
                contract = Contract(
                    contract_id=contract_id,
                    template_id=template.id,
                    name=variables.get('name', template.name),
                    parties=json.dumps(variables.get('parties', {}), ensure_ascii=False) if variables.get('parties') else None,
                    variables=json.dumps(variables, ensure_ascii=False),
                    content=content,
                    status="draft",
                    start_date=variables.get('start_date'),
                    end_date=variables.get('end_date'),
                    customer_id=variables.get('customer_id'),
                    user_id=user_id
                )
                
                db.add(contract)
                contracts.append(contract)
            
            db.commit()
            for contract in contracts:
                db.refresh(contract)
            
            logger.info(f"批量生成合同成功: {len(contracts)} 个合同")
            return contracts
            
        except Exception as e:
            db.rollback()
            logger.error(f"批量生成合同时出错: {e}")
            raise
        finally:
            db.close()
    
    def preview_contract(self, template_id: int, variables: Dict[str, Any]) -> str:
        """预览合同
        
        Args:
            template_id: 模板ID
            variables: 变量值
            
        Returns:
            预览内容
        """
        # 获取模板
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 替换变量
        return self._replace_variables(template.content, variables)

# 创建合同管理器实例
contract_manager = ContractManager()
