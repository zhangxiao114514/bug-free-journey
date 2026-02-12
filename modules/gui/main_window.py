import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QDialog, QFormLayout, QLineEdit, QTextEdit, 
    QComboBox, QDateEdit, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QDate

from utils.config import config_manager
from modules.customer.customer_manager import customer_manager
from modules.consultation.consultation_manager import consultation_manager
from modules.knowledge.knowledge_manager import knowledge_manager
from modules.document.document_manager import document_manager
from modules.message.wechat_service import message_service

logger = logging.getLogger(__name__)

class LegalServiceGUI(QMainWindow):
    """法律客服系统GUI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信法律客服系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.setFont(font)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 创建各个选项卡
        self._create_customer_tab()
        self._create_consultation_tab()
        self._create_knowledge_tab()
        self._create_document_tab()
        self._create_analytics_tab()
        self._create_system_tab()
        
        # 创建状态栏
        self.statusBar().showMessage("系统就绪")
    
    def _create_customer_tab(self):
        """创建客户管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 顶部操作栏
        top_layout = QHBoxLayout()
        add_btn = QPushButton("添加客户")
        edit_btn = QPushButton("编辑客户")
        delete_btn = QPushButton("删除客户")
        refresh_btn = QPushButton("刷新")
        
        add_btn.clicked.connect(self._add_customer)
        edit_btn.clicked.connect(self._edit_customer)
        delete_btn.clicked.connect(self._delete_customer)
        refresh_btn.clicked.connect(self._refresh_customer_table)
        
        top_layout.addWidget(add_btn)
        top_layout.addWidget(edit_btn)
        top_layout.addWidget(delete_btn)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 客户表格
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels(["ID", "微信ID", "昵称", "电话", "状态", "创建时间"])
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.customer_table)
        
        # 刷新表格
        self._refresh_customer_table()
        
        self.tab_widget.addTab(tab, "客户管理")
    
    def _refresh_customer_table(self):
        """刷新客户表格"""
        try:
            customers = customer_manager.list_customers()
            
            self.customer_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                self.customer_table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
                self.customer_table.setItem(row, 1, QTableWidgetItem(customer.wechat_id))
                self.customer_table.setItem(row, 2, QTableWidgetItem(customer.nickname))
                self.customer_table.setItem(row, 3, QTableWidgetItem(customer.phone or ""))
                self.customer_table.setItem(row, 4, QTableWidgetItem(customer.status))
                self.customer_table.setItem(row, 5, QTableWidgetItem(customer.created_at.strftime("%Y-%m-%d %H:%M:%S")))
            
            self.statusBar().showMessage(f"刷新客户列表成功，共 {len(customers)} 个客户")
            
        except Exception as e:
            logger.error(f"刷新客户表格时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新客户列表时出错: {str(e)}")
    
    def _add_customer(self):
        """添加客户"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加客户")
        layout = QFormLayout(dialog)
        
        wechat_id_edit = QLineEdit()
        nickname_edit = QLineEdit()
        phone_edit = QLineEdit()
        email_edit = QLineEdit()
        status_combo = QComboBox()
        status_combo.addItems(["active", "inactive"])
        
        layout.addRow("微信ID:", wechat_id_edit)
        layout.addRow("昵称:", nickname_edit)
        layout.addRow("电话:", phone_edit)
        layout.addRow("邮箱:", email_edit)
        layout.addRow("状态:", status_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'wechat_id': wechat_id_edit.text(),
                    'nickname': nickname_edit.text(),
                    'phone': phone_edit.text(),
                    'email': email_edit.text(),
                    'status': status_combo.currentText()
                }
                
                customer = customer_manager.create_customer(data)
                self._refresh_customer_table()
                QMessageBox.information(self, "成功", f"添加客户成功: {customer.nickname}")
                
            except Exception as e:
                logger.error(f"添加客户时出错: {e}")
                QMessageBox.critical(self, "错误", f"添加客户时出错: {str(e)}")
    
    def _edit_customer(self):
        """编辑客户"""
        selected_row = self.customer_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的客户")
            return
        
        customer_id = int(self.customer_table.item(selected_row, 0).text())
        customer = customer_manager.get_customer(customer_id)
        
        if not customer:
            QMessageBox.warning(self, "警告", "客户不存在")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑客户")
        layout = QFormLayout(dialog)
        
        wechat_id_edit = QLineEdit(customer.wechat_id)
        nickname_edit = QLineEdit(customer.nickname)
        phone_edit = QLineEdit(customer.phone or "")
        email_edit = QLineEdit(customer.email or "")
        status_combo = QComboBox()
        status_combo.addItems(["active", "inactive"])
        status_combo.setCurrentText(customer.status)
        
        layout.addRow("微信ID:", wechat_id_edit)
        layout.addRow("昵称:", nickname_edit)
        layout.addRow("电话:", phone_edit)
        layout.addRow("邮箱:", email_edit)
        layout.addRow("状态:", status_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'wechat_id': wechat_id_edit.text(),
                    'nickname': nickname_edit.text(),
                    'phone': phone_edit.text(),
                    'email': email_edit.text(),
                    'status': status_combo.currentText()
                }
                
                customer = customer_manager.update_customer(customer_id, data)
                self._refresh_customer_table()
                QMessageBox.information(self, "成功", f"编辑客户成功: {customer.nickname}")
                
            except Exception as e:
                logger.error(f"编辑客户时出错: {e}")
                QMessageBox.critical(self, "错误", f"编辑客户时出错: {str(e)}")
    
    def _delete_customer(self):
        """删除客户"""
        selected_row = self.customer_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的客户")
            return
        
        customer_id = int(self.customer_table.item(selected_row, 0).text())
        customer = customer_manager.get_customer(customer_id)
        
        if not customer:
            QMessageBox.warning(self, "警告", "客户不存在")
            return
        
        reply = QMessageBox.question(self, "确认", f"确定要删除客户 {customer.nickname} 吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                customer_manager.delete_customer(customer_id)
                self._refresh_customer_table()
                QMessageBox.information(self, "成功", f"删除客户成功: {customer.nickname}")
                
            except Exception as e:
                logger.error(f"删除客户时出错: {e}")
                QMessageBox.critical(self, "错误", f"删除客户时出错: {str(e)}")
    
    def _create_consultation_tab(self):
        """创建咨询管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 顶部操作栏
        top_layout = QHBoxLayout()
        add_btn = QPushButton("添加咨询")
        edit_btn = QPushButton("编辑咨询")
        complete_btn = QPushButton("完成咨询")
        refresh_btn = QPushButton("刷新")
        
        add_btn.clicked.connect(self._add_consultation)
        edit_btn.clicked.connect(self._edit_consultation)
        complete_btn.clicked.connect(self._complete_consultation)
        refresh_btn.clicked.connect(self._refresh_consultation_table)
        
        top_layout.addWidget(add_btn)
        top_layout.addWidget(edit_btn)
        top_layout.addWidget(complete_btn)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 咨询表格
        self.consultation_table = QTableWidget()
        self.consultation_table.setColumnCount(7)
        self.consultation_table.setHorizontalHeaderLabels(["ID", "标题", "客户", "状态", "优先级", "创建时间", "完成时间"])
        self.consultation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.consultation_table)
        
        # 刷新表格
        self._refresh_consultation_table()
        
        self.tab_widget.addTab(tab, "咨询管理")
    
    def _refresh_consultation_table(self):
        """刷新咨询表格"""
        try:
            consultations = consultation_manager.list_consultations()
            
            self.consultation_table.setRowCount(len(consultations))
            
            for row, consultation in enumerate(consultations):
                self.consultation_table.setItem(row, 0, QTableWidgetItem(str(consultation.id)))
                self.consultation_table.setItem(row, 1, QTableWidgetItem(consultation.title))
                self.consultation_table.setItem(row, 2, QTableWidgetItem(str(consultation.customer_id)))
                self.consultation_table.setItem(row, 3, QTableWidgetItem(consultation.status))
                self.consultation_table.setItem(row, 4, QTableWidgetItem(str(consultation.priority)))
                self.consultation_table.setItem(row, 5, QTableWidgetItem(consultation.created_at.strftime("%Y-%m-%d %H:%M:%S")))
                if consultation.completed_at:
                    self.consultation_table.setItem(row, 6, QTableWidgetItem(consultation.completed_at.strftime("%Y-%m-%d %H:%M:%S")))
                else:
                    self.consultation_table.setItem(row, 6, QTableWidgetItem(""))
            
            self.statusBar().showMessage(f"刷新咨询列表成功，共 {len(consultations)} 个咨询")
            
        except Exception as e:
            logger.error(f"刷新咨询表格时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新咨询列表时出错: {str(e)}")
    
    def _add_consultation(self):
        """添加咨询"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加咨询")
        layout = QFormLayout(dialog)
        
        customer_id_edit = QLineEdit()
        title_edit = QLineEdit()
        description_edit = QTextEdit()
        category_edit = QLineEdit()
        priority_combo = QComboBox()
        priority_combo.addItems(["0", "1", "2"])
        
        layout.addRow("客户ID:", customer_id_edit)
        layout.addRow("标题:", title_edit)
        layout.addRow("描述:", description_edit)
        layout.addRow("分类:", category_edit)
        layout.addRow("优先级:", priority_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'customer_id': int(customer_id_edit.text()),
                    'title': title_edit.text(),
                    'description': description_edit.toPlainText(),
                    'category': category_edit.text(),
                    'priority': int(priority_combo.currentText())
                }
                
                consultation = consultation_manager.create_consultation(data)
                self._refresh_consultation_table()
                QMessageBox.information(self, "成功", f"添加咨询成功: {consultation.title}")
                
            except Exception as e:
                logger.error(f"添加咨询时出错: {e}")
                QMessageBox.critical(self, "错误", f"添加咨询时出错: {str(e)}")
    
    def _edit_consultation(self):
        """编辑咨询"""
        selected_row = self.consultation_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的咨询")
            return
        
        consultation_id = int(self.consultation_table.item(selected_row, 0).text())
        consultation = consultation_manager.get_consultation(consultation_id)
        
        if not consultation:
            QMessageBox.warning(self, "警告", "咨询不存在")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑咨询")
        layout = QFormLayout(dialog)
        
        customer_id_edit = QLineEdit(str(consultation.customer_id))
        title_edit = QLineEdit(consultation.title)
        description_edit = QTextEdit(consultation.description or "")
        category_edit = QLineEdit(consultation.category or "")
        status_combo = QComboBox()
        status_combo.addItems(["pending", "processing", "completed", "cancelled"])
        status_combo.setCurrentText(consultation.status)
        priority_combo = QComboBox()
        priority_combo.addItems(["0", "1", "2"])
        priority_combo.setCurrentText(str(consultation.priority))
        
        layout.addRow("客户ID:", customer_id_edit)
        layout.addRow("标题:", title_edit)
        layout.addRow("描述:", description_edit)
        layout.addRow("分类:", category_edit)
        layout.addRow("状态:", status_combo)
        layout.addRow("优先级:", priority_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'customer_id': int(customer_id_edit.text()),
                    'title': title_edit.text(),
                    'description': description_edit.toPlainText(),
                    'category': category_edit.text(),
                    'status': status_combo.currentText(),
                    'priority': int(priority_combo.currentText())
                }
                
                consultation = consultation_manager.update_consultation(consultation_id, data)
                self._refresh_consultation_table()
                QMessageBox.information(self, "成功", f"编辑咨询成功: {consultation.title}")
                
            except Exception as e:
                logger.error(f"编辑咨询时出错: {e}")
                QMessageBox.critical(self, "错误", f"编辑咨询时出错: {str(e)}")
    
    def _complete_consultation(self):
        """完成咨询"""
        selected_row = self.consultation_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要完成的咨询")
            return
        
        consultation_id = int(self.consultation_table.item(selected_row, 0).text())
        consultation = consultation_manager.get_consultation(consultation_id)
        
        if not consultation:
            QMessageBox.warning(self, "警告", "咨询不存在")
            return
        
        reply = QMessageBox.question(self, "确认", f"确定要完成咨询 {consultation.title} 吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                consultation = consultation_manager.complete_consultation(consultation_id)
                self._refresh_consultation_table()
                QMessageBox.information(self, "成功", f"完成咨询成功: {consultation.title}")
                
            except Exception as e:
                logger.error(f"完成咨询时出错: {e}")
                QMessageBox.critical(self, "错误", f"完成咨询时出错: {str(e)}")
    
    def _create_knowledge_tab(self):
        """创建知识库选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 顶部操作栏
        top_layout = QHBoxLayout()
        add_btn = QPushButton("添加知识")
        edit_btn = QPushButton("编辑知识")
        delete_btn = QPushButton("删除知识")
        refresh_btn = QPushButton("刷新")
        
        add_btn.clicked.connect(self._add_knowledge)
        edit_btn.clicked.connect(self._edit_knowledge)
        delete_btn.clicked.connect(self._delete_knowledge)
        refresh_btn.clicked.connect(self._refresh_knowledge_table)
        
        top_layout.addWidget(add_btn)
        top_layout.addWidget(edit_btn)
        top_layout.addWidget(delete_btn)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 知识表格
        self.knowledge_table = QTableWidget()
        self.knowledge_table.setColumnCount(6)
        self.knowledge_table.setHorizontalHeaderLabels(["ID", "标题", "分类", "状态", "版本", "创建时间"])
        self.knowledge_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.knowledge_table)
        
        # 刷新表格
        self._refresh_knowledge_table()
        
        self.tab_widget.addTab(tab, "知识库管理")
    
    def _refresh_knowledge_table(self):
        """刷新知识库表格"""
        try:
            knowledge_list = knowledge_manager.list_knowledge()
            
            self.knowledge_table.setRowCount(len(knowledge_list))
            
            for row, knowledge in enumerate(knowledge_list):
                self.knowledge_table.setItem(row, 0, QTableWidgetItem(str(knowledge.id)))
                self.knowledge_table.setItem(row, 1, QTableWidgetItem(knowledge.title))
                self.knowledge_table.setItem(row, 2, QTableWidgetItem(knowledge.category))
                self.knowledge_table.setItem(row, 3, QTableWidgetItem(knowledge.status))
                self.knowledge_table.setItem(row, 4, QTableWidgetItem(str(knowledge.version)))
                self.knowledge_table.setItem(row, 5, QTableWidgetItem(knowledge.created_at.strftime("%Y-%m-%d %H:%M:%S")))
            
            self.statusBar().showMessage(f"刷新知识库成功，共 {len(knowledge_list)} 条知识")
            
        except Exception as e:
            logger.error(f"刷新知识库表格时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新知识库时出错: {str(e)}")
    
    def _add_knowledge(self):
        """添加知识"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加知识")
        layout = QFormLayout(dialog)
        
        title_edit = QLineEdit()
        content_edit = QTextEdit()
        category_edit = QLineEdit()
        subcategory_edit = QLineEdit()
        keywords_edit = QLineEdit()
        tags_edit = QLineEdit()
        status_combo = QComboBox()
        status_combo.addItems(["active", "inactive", "draft"])
        
        layout.addRow("标题:", title_edit)
        layout.addRow("内容:", content_edit)
        layout.addRow("分类:", category_edit)
        layout.addRow("子分类:", subcategory_edit)
        layout.addRow("关键词:", keywords_edit)
        layout.addRow("标签:", tags_edit)
        layout.addRow("状态:", status_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'title': title_edit.text(),
                    'content': content_edit.toPlainText(),
                    'category': category_edit.text(),
                    'subcategory': subcategory_edit.text(),
                    'keywords': keywords_edit.text(),
                    'tags': tags_edit.text(),
                    'status': status_combo.currentText()
                }
                
                knowledge = knowledge_manager.create_knowledge(data)
                self._refresh_knowledge_table()
                QMessageBox.information(self, "成功", f"添加知识成功: {knowledge.title}")
                
            except Exception as e:
                logger.error(f"添加知识时出错: {e}")
                QMessageBox.critical(self, "错误", f"添加知识时出错: {str(e)}")
    
    def _edit_knowledge(self):
        """编辑知识"""
        selected_row = self.knowledge_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的知识")
            return
        
        knowledge_id = int(self.knowledge_table.item(selected_row, 0).text())
        knowledge = knowledge_manager.get_knowledge(knowledge_id)
        
        if not knowledge:
            QMessageBox.warning(self, "警告", "知识不存在")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑知识")
        layout = QFormLayout(dialog)
        
        title_edit = QLineEdit(knowledge.title)
        content_edit = QTextEdit(knowledge.content)
        category_edit = QLineEdit(knowledge.category)
        subcategory_edit = QLineEdit(knowledge.subcategory or "")
        keywords_edit = QLineEdit(knowledge.keywords or "")
        tags_edit = QLineEdit(knowledge.tags or "")
        status_combo = QComboBox()
        status_combo.addItems(["active", "inactive", "draft"])
        status_combo.setCurrentText(knowledge.status)
        
        layout.addRow("标题:", title_edit)
        layout.addRow("内容:", content_edit)
        layout.addRow("分类:", category_edit)
        layout.addRow("子分类:", subcategory_edit)
        layout.addRow("关键词:", keywords_edit)
        layout.addRow("标签:", tags_edit)
        layout.addRow("状态:", status_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'title': title_edit.text(),
                    'content': content_edit.toPlainText(),
                    'category': category_edit.text(),
                    'subcategory': subcategory_edit.text(),
                    'keywords': keywords_edit.text(),
                    'tags': tags_edit.text(),
                    'status': status_combo.currentText()
                }
                
                knowledge = knowledge_manager.update_knowledge(knowledge_id, data)
                self._refresh_knowledge_table()
                QMessageBox.information(self, "成功", f"编辑知识成功: {knowledge.title}")
                
            except Exception as e:
                logger.error(f"编辑知识时出错: {e}")
                QMessageBox.critical(self, "错误", f"编辑知识时出错: {str(e)}")
    
    def _delete_knowledge(self):
        """删除知识"""
        selected_row = self.knowledge_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的知识")
            return
        
        knowledge_id = int(self.knowledge_table.item(selected_row, 0).text())
        knowledge = knowledge_manager.get_knowledge(knowledge_id)
        
        if not knowledge:
            QMessageBox.warning(self, "警告", "知识不存在")
            return
        
        reply = QMessageBox.question(self, "确认", f"确定要删除知识 {knowledge.title} 吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                knowledge_manager.delete_knowledge(knowledge_id)
                self._refresh_knowledge_table()
                QMessageBox.information(self, "成功", f"删除知识成功: {knowledge.title}")
                
            except Exception as e:
                logger.error(f"删除知识时出错: {e}")
                QMessageBox.critical(self, "错误", f"删除知识时出错: {str(e)}")
    
    def _create_document_tab(self):
        """创建文档管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 顶部操作栏
        top_layout = QHBoxLayout()
        upload_btn = QPushButton("上传文档")
        edit_btn = QPushButton("编辑文档")
        delete_btn = QPushButton("删除文档")
        analyze_btn = QPushButton("分析文档")
        refresh_btn = QPushButton("刷新")
        
        upload_btn.clicked.connect(self._upload_document)
        edit_btn.clicked.connect(self._edit_document)
        delete_btn.clicked.connect(self._delete_document)
        analyze_btn.clicked.connect(self._analyze_document)
        refresh_btn.clicked.connect(self._refresh_document_table)
        
        top_layout.addWidget(upload_btn)
        top_layout.addWidget(edit_btn)
        top_layout.addWidget(delete_btn)
        top_layout.addWidget(analyze_btn)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 文档表格
        self.document_table = QTableWidget()
        self.document_table.setColumnCount(7)
        self.document_table.setHorizontalHeaderLabels(["ID", "标题", "文件名", "类型", "大小", "状态", "上传时间"])
        self.document_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.document_table)
        
        # 刷新表格
        self._refresh_document_table()
        
        self.tab_widget.addTab(tab, "文档管理")
    
    def _refresh_document_table(self):
        """刷新文档表格"""
        try:
            documents = document_manager.list_documents()
            
            self.document_table.setRowCount(len(documents))
            
            for row, document in enumerate(documents):
                self.document_table.setItem(row, 0, QTableWidgetItem(str(document.id)))
                self.document_table.setItem(row, 1, QTableWidgetItem(document.title))
                self.document_table.setItem(row, 2, QTableWidgetItem(document.file_name))
                self.document_table.setItem(row, 3, QTableWidgetItem(document.file_type))
                self.document_table.setItem(row, 4, QTableWidgetItem(f"{document.file_size / 1024:.2f} KB"))
                self.document_table.setItem(row, 5, QTableWidgetItem(document.status))
                self.document_table.setItem(row, 6, QTableWidgetItem(document.created_at.strftime("%Y-%m-%d %H:%M:%S")))
            
            self.statusBar().showMessage(f"刷新文档列表成功，共 {len(documents)} 个文档")
            
        except Exception as e:
            logger.error(f"刷新文档表格时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新文档列表时出错: {str(e)}")
    
    def _upload_document(self):
        """上传文档"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文档", "", "所有文件 (*.*);;PDF文件 (*.pdf);;Word文件 (*.doc *.docx);;图片文件 (*.jpg *.jpeg *.png)")
        
        if not file_path:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("上传文档")
        layout = QFormLayout(dialog)
        
        title_edit = QLineEdit(os.path.basename(file_path))
        description_edit = QTextEdit()
        customer_id_edit = QLineEdit()
        
        layout.addRow("标题:", title_edit)
        layout.addRow("描述:", description_edit)
        layout.addRow("客户ID:", customer_id_edit)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'title': title_edit.text(),
                    'description': description_edit.toPlainText(),
                    'customer_id': int(customer_id_edit.text()) if customer_id_edit.text() else None
                }
                
                document = document_manager.upload_document(file_path, data)
                self._refresh_document_table()
                QMessageBox.information(self, "成功", f"上传文档成功: {document.title}")
                
            except Exception as e:
                logger.error(f"上传文档时出错: {e}")
                QMessageBox.critical(self, "错误", f"上传文档时出错: {str(e)}")
    
    def _edit_document(self):
        """编辑文档"""
        selected_row = self.document_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的文档")
            return
        
        document_id = int(self.document_table.item(selected_row, 0).text())
        document = document_manager.get_document(document_id)
        
        if not document:
            QMessageBox.warning(self, "警告", "文档不存在")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑文档")
        layout = QFormLayout(dialog)
        
        title_edit = QLineEdit(document.title)
        description_edit = QTextEdit(document.description or "")
        status_combo = QComboBox()
        status_combo.addItems(["active", "archived", "deleted"])
        status_combo.setCurrentText(document.status)
        
        layout.addRow("标题:", title_edit)
        layout.addRow("描述:", description_edit)
        layout.addRow("状态:", status_combo)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    'title': title_edit.text(),
                    'description': description_edit.toPlainText(),
                    'status': status_combo.currentText()
                }
                
                document = document_manager.update_document(document_id, data)
                self._refresh_document_table()
                QMessageBox.information(self, "成功", f"编辑文档成功: {document.title}")
                
            except Exception as e:
                logger.error(f"编辑文档时出错: {e}")
                QMessageBox.critical(self, "错误", f"编辑文档时出错: {str(e)}")
    
    def _delete_document(self):
        """删除文档"""
        selected_row = self.document_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的文档")
            return
        
        document_id = int(self.document_table.item(selected_row, 0).text())
        document = document_manager.get_document(document_id)
        
        if not document:
            QMessageBox.warning(self, "警告", "文档不存在")
            return
        
        reply = QMessageBox.question(self, "确认", f"确定要删除文档 {document.title} 吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                document_manager.delete_document(document_id)
                self._refresh_document_table()
                QMessageBox.information(self, "成功", f"删除文档成功: {document.title}")
                
            except Exception as e:
                logger.error(f"删除文档时出错: {e}")
                QMessageBox.critical(self, "错误", f"删除文档时出错: {str(e)}")
    
    def _analyze_document(self):
        """分析文档"""
        selected_row = self.document_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要分析的文档")
            return
        
        document_id = int(self.document_table.item(selected_row, 0).text())
        document = document_manager.get_document(document_id)
        
        if not document:
            QMessageBox.warning(self, "警告", "文档不存在")
            return
        
        try:
            analysis = document_manager.analyze_document(document_id)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("文档分析结果")
            layout = QVBoxLayout(dialog)
            
            # 基本信息
            info_text = f"文档: {analysis['title']}\n"
            info_text += f"类型: {analysis['file_type']}\n"
            info_text += f"大小: {analysis['file_size']} bytes\n\n"
            
            # 内容分析
            info_text += "内容分析:\n"
            content_analysis = analysis['content_analysis']
            info_text += f"文本长度: {content_analysis['text_length']}\n"
            info_text += f"词数: {content_analysis['word_count']}\n"
            info_text += f"包含敏感信息: {'是' if content_analysis['has_sensitive_info'] else '否'}\n"
            info_text += f"法律条款: {', '.join(content_analysis['legal_terms']) if content_analysis['legal_terms'] else '无'}\n\n"
            
            # 风险评估
            info_text += "风险评估:\n"
            risk_assessment = analysis['risk_assessment']
            info_text += f"风险等级: {risk_assessment['risk_level']}\n"
            info_text += f"风险描述: {risk_assessment['risk_description']}\n"
            info_text += f"风险因素: {', '.join(risk_assessment['risk_factors']) if risk_assessment['risk_factors'] else '无'}\n"
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            ok_btn = QPushButton("确定")
            ok_btn.clicked.connect(dialog.accept)
            layout.addWidget(ok_btn)
            
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"分析文档时出错: {e}")
            QMessageBox.critical(self, "错误", f"分析文档时出错: {str(e)}")
    
    def _create_analytics_tab(self):
        """创建数据分析选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 顶部操作栏
        top_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新数据")
        export_btn = QPushButton("导出报告")
        
        refresh_btn.clicked.connect(self._refresh_analytics)
        export_btn.clicked.connect(self._export_analytics)
        
        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(export_btn)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 分析内容
        content_layout = QVBoxLayout()
        
        # 客户统计
        customer_stats = QLabel()
        content_layout.addWidget(customer_stats)
        
        # 咨询统计
        consultation_stats = QLabel()
        content_layout.addWidget(consultation_stats)
        
        # 文档统计
        document_stats = QLabel()
        content_layout.addWidget(document_stats)
        
        layout.addLayout(content_layout)
        
        # 刷新数据
        self._refresh_analytics()
        
        self.tab_widget.addTab(tab, "数据分析")
    
    def _refresh_analytics(self):
        """刷新数据分析"""
        try:
            # 获取客户统计
            customers = customer_manager.list_customers()
            active_customers = len([c for c in customers if c.status == "active"])
            
            # 获取咨询统计
            consultations = consultation_manager.list_consultations()
            completed_consultations = len([c for c in consultations if c.status == "completed"])
            pending_consultations = len([c for c in consultations if c.status in ["pending", "processing"]])
            
            # 获取文档统计
            documents = document_manager.list_documents()
            total_documents = len(documents)
            ocr_processed = len([d for d in documents if d.ocr_processed])
            
            # 更新统计信息
            stats_text = f"客户统计: 总计 {len(customers)} 个客户，其中活跃 {active_customers} 个\n"
            stats_text += f"咨询统计: 总计 {len(consultations)} 个咨询，已完成 {completed_consultations} 个，待处理 {pending_consultations} 个\n"
            stats_text += f"文档统计: 总计 {total_documents} 个文档，已OCR处理 {ocr_processed} 个\n"
            stats_text += f"系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 更新标签
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "数据分析":
                    tab = self.tab_widget.widget(i)
                    layout = tab.layout()
                    content_layout = layout.itemAt(1).layout()
                    customer_stats = content_layout.itemAt(0).widget()
                    customer_stats.setText(stats_text)
                    break
            
            self.statusBar().showMessage("刷新数据分析成功")
            
        except Exception as e:
            logger.error(f"刷新数据分析时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新数据分析时出错: {str(e)}")
    
    def _export_analytics(self):
        """导出分析报告"""
        try:
            # 获取统计数据
            customers = customer_manager.list_customers()
            consultations = consultation_manager.list_consultations()
            documents = document_manager.list_documents()
            
            # 生成报告
            report_text = f"法律客服系统分析报告\n"
            report_text += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            report_text += "1. 客户分析\n"
            report_text += f"总计客户数: {len(customers)}\n"
            report_text += f"活跃客户数: {len([c for c in customers if c.status == 'active'])}\n"
            report_text += f"非活跃客户数: {len([c for c in customers if c.status == 'inactive'])}\n\n"
            
            report_text += "2. 咨询分析\n"
            report_text += f"总计咨询数: {len(consultations)}\n"
            report_text += f"已完成咨询: {len([c for c in consultations if c.status == 'completed'])}\n"
            report_text += f"待处理咨询: {len([c for c in consultations if c.status in ['pending', 'processing']])}\n"
            report_text += f"已取消咨询: {len([c for c in consultations if c.status == 'cancelled'])}\n\n"
            
            report_text += "3. 文档分析\n"
            report_text += f"总计文档数: {len(documents)}\n"
            report_text += f"PDF文档: {len([d for d in documents if d.file_type == 'pdf'])}\n"
            report_text += f"Word文档: {len([d for d in documents if d.file_type in ['doc', 'docx']])}\n"
            report_text += f"图片文档: {len([d for d in documents if d.file_type in ['jpg', 'jpeg', 'png']])}\n"
            report_text += f"已OCR处理: {len([d for d in documents if d.ocr_processed])}\n"
            report_text += f"已提取内容: {len([d for d in documents if d.content_extracted])}\n"
            
            # 保存报告
            file_path, _ = QFileDialog.getSaveFileName(self, "保存分析报告", f"analytics_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", "文本文件 (*.txt)")
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                
                QMessageBox.information(self, "成功", f"分析报告导出成功: {file_path}")
                
        except Exception as e:
            logger.error(f"导出分析报告时出错: {e}")
            QMessageBox.critical(self, "错误", f"导出分析报告时出错: {str(e)}")
    
    def _create_system_tab(self):
        """创建系统配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 系统信息
        info_layout = QVBoxLayout()
        system_info = QLabel()
        system_info.setText(f"系统名称: {config_manager.get('general', 'system_name')}\n"
                           f"系统版本: {config_manager.get('general', 'system_version')}\n"
                           f"服务类型: {config_manager.get('general', 'service_type')}\n"
                           f"调试模式: {'开启' if config_manager.getboolean('general', 'debug') else '关闭'}\n"
                           f"配置文件: {config_manager.config_path}")
        info_layout.addWidget(system_info)
        
        layout.addLayout(info_layout)
        
        # 服务状态
        status_layout = QVBoxLayout()
        status_label = QLabel("服务状态:")
        status_layout.addWidget(status_label)
        
        # 消息服务状态
        if 'message_service' in globals():
            service_status = message_service.get_status()
            status_text = f"消息服务类型: {service_status['service_type']}\n"
            status_text += f"消息服务状态: {'运行中' if service_status['is_running'] else '已停止'}\n"
            status_text += f"机器人状态: {service_status['bot_status']}\n"
        else:
            status_text = "消息服务未初始化\n"
        
        status_info = QLabel(status_text)
        status_layout.addWidget(status_info)
        
        layout.addLayout(status_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        start_btn = QPushButton("启动服务")
        stop_btn = QPushButton("停止服务")
        refresh_btn = QPushButton("刷新状态")
        
        start_btn.clicked.connect(self._start_service)
        stop_btn.clicked.connect(self._stop_service)
        refresh_btn.clicked.connect(self._refresh_system_status)
        
        btn_layout.addWidget(start_btn)
        btn_layout.addWidget(stop_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "系统配置")
    
    def _start_service(self):
        """启动服务"""
        try:
            import asyncio
            
            async def start():
                await message_service.start()
            
            asyncio.run(start())
            
            self._refresh_system_status()
            QMessageBox.information(self, "成功", "服务启动成功")
            
        except Exception as e:
            logger.error(f"启动服务时出错: {e}")
            QMessageBox.critical(self, "错误", f"启动服务时出错: {str(e)}")
    
    def _stop_service(self):
        """停止服务"""
        try:
            import asyncio
            
            async def stop():
                await message_service.stop()
            
            asyncio.run(stop())
            
            self._refresh_system_status()
            QMessageBox.information(self, "成功", "服务停止成功")
            
        except Exception as e:
            logger.error(f"停止服务时出错: {e}")
            QMessageBox.critical(self, "错误", f"停止服务时出错: {str(e)}")
    
    def _refresh_system_status(self):
        """刷新系统状态"""
        # 更新系统信息
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "系统配置":
                tab = self.tab_widget.widget(i)
                layout = tab.layout()
                
                # 更新服务状态
                status_layout = layout.itemAt(1).layout()
                status_info = status_layout.itemAt(1).widget()
                
                if 'message_service' in globals():
                    service_status = message_service.get_status()
                    status_text = f"消息服务类型: {service_status['service_type']}\n"
                    status_text += f"消息服务状态: {'运行中' if service_status['is_running'] else '已停止'}\n"
                    status_text += f"机器人状态: {service_status['bot_status']}\n"
                else:
                    status_text = "消息服务未初始化\n"
                
                status_info.setText(status_text)
                break
        
        self.statusBar().showMessage("刷新系统状态成功")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = LegalServiceGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
