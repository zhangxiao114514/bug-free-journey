# -*- coding: utf-8 -*-
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_knowledge_base():
    """初始化知识库数据"""
    try:
        logger.info("开始初始化知识库数据...")
        
        # 尝试导入数据库模块
        try:
            from sqlalchemy.orm import Session
            from utils.database import get_db, engine, Base
            from models.knowledge import KnowledgeBase
            
            # 初始化数据库表
            logger.info("开始初始化数据库表...")
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表初始化完成")
            
            # 获取数据库会话
            db = next(get_db())
            
            # 检查是否已有数据
            existing_count = db.query(KnowledgeBase).count()
            if existing_count > 0:
                logger.info(f"知识库已有 {existing_count} 条数据，跳过初始化")
                return
            
            # 法律知识分类
            categories = [
                "劳动纠纷", "民事诉讼", "刑事辩护", "知识产权",
                "婚姻家庭", "房产纠纷", "公司法", "交通事故",
                "医疗纠纷", "行政诉讼"
            ]
            
            # 法律知识数据
            knowledge_data = [
                # 劳动纠纷
                {
                    "title": "劳动合同解除的条件",
                    "content": "根据《劳动合同法》第三十九条，用人单位可以解除劳动合同的情形包括：（一）在试用期间被证明不符合录用条件的；（二）严重违反用人单位的规章制度的；（三）严重失职，营私舞弊，给用人单位造成重大损害的；（四）劳动者同时与其他用人单位建立劳动关系，对完成本单位的工作任务造成严重影响，或者经用人单位提出，拒不改正的；（五）因本法第二十六条第一款第一项规定的情形致使劳动合同无效的；（六）被依法追究刑事责任的。",
                    "category": "劳动纠纷",
                    "tags": "劳动合同,解除,条件",
                    "source": "劳动合同法",
                    "author": "系统管理员",
                    "status": "active"
                },
                {
                    "title": "工伤认定的标准",
                    "content": "根据《工伤保险条例》第十四条，职工有下列情形之一的，应当认定为工伤：（一）在工作时间和工作场所内，因工作原因受到事故伤害的；（二）工作时间前后在工作场所内，从事与工作有关的预备性或者收尾性工作受到事故伤害的；（三）在工作时间和工作场所内，因履行工作职责受到暴力等意外伤害的；（四）患职业病的；（五）因工外出期间，由于工作原因受到伤害或者发生事故下落不明的；（六）在上下班途中，受到非本人主要责任的交通事故或者城市轨道交通、客运轮渡、火车事故伤害的；（七）法律、行政法规规定应当认定为工伤的其他情形。",
                    "category": "劳动纠纷",
                    "tags": "工伤,认定,标准",
                    "source": "工伤保险条例",
                    "author": "系统管理员",
                    "status": "active"
                },
                {
                    "title": "加班工资的计算方法",
                    "content": "根据《劳动法》第四十四条，有下列情形之一的，用人单位应当按照下列标准支付高于劳动者正常工作时间工资的工资报酬：（一）安排劳动者延长工作时间的，支付不低于工资的百分之一百五十的工资报酬；（二）休息日安排劳动者工作又不能安排补休的，支付不低于工资的百分之二百的工资报酬；（三）法定休假日安排劳动者工作的，支付不低于工资的百分之三百的工资报酬。",
                    "category": "劳动纠纷",
                    "tags": "加班,工资,计算",
                    "source": "劳动法",
                    "author": "系统管理员",
                    "status": "active"
                }
            ]
            
            # 批量插入数据
            for item in knowledge_data:
                knowledge = KnowledgeBase(**item)
                db.add(knowledge)
            
            db.commit()
            logger.info(f"知识库数据初始化完成，共添加 {len(knowledge_data)} 条数据")
        except ImportError as e:
            logger.warning(f"数据库模块导入失败，跳过数据库初始化: {e}")
        except Exception as e:
            logger.error(f"初始化知识库数据时出错: {e}")
            # 继续执行，不中断程序
    except Exception as e:
        logger.error(f"初始化知识库时出错: {e}")

def main():
    """主函数"""
    try:
        # 初始化知识库数据
        init_knowledge_base()
        
        logger.info("知识库初始化成功完成")
    except Exception as e:
        logger.error(f"初始化知识库时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()