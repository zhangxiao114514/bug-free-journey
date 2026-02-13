import os
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

from utils.config import config_manager
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        # 获取安全配置
        self.aes_key = config_manager.get('security', 'aes_key', 'your_aes_key_here').encode('utf-8')
        self.aes_iv = config_manager.get('security', 'aes_iv', 'your_aes_iv_here').encode('utf-8')
        self.token_secret = config_manager.get('security', 'token_secret', 'your_jwt_secret_here')
        self.token_expiry = config_manager.getint('security', 'token_expiry', 86400)
        
        # 确保密钥长度正确
        if len(self.aes_key) != 32:  # AES-256
            self.aes_key = self._pad_key(self.aes_key, 32)
        if len(self.aes_iv) != 16:  # AES block size
            self.aes_iv = self._pad_key(self.aes_iv, 16)
    
    def _pad_key(self, key: bytes, length: int) -> bytes:
        """填充密钥到指定长度"""
        if len(key) >= length:
            return key[:length]
        return key + (length - len(key)) * b'\x00'
    
    def encrypt(self, data: str) -> str:
        """加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            加密后的数据（base64编码）
        """
        try:
            # 创建加密器
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CBC(self.aes_iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # 填充数据
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
            
            # 加密
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # base64编码
            return base64.b64encode(ciphertext).decode('utf-8')
        except Exception as e:
            logger.error(f"加密数据时出错: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据
        
        Args:
            encrypted_data: 加密后的数据（base64编码）
            
        Returns:
            解密后的数据
        """
        try:
            # base64解码
            ciphertext = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # 创建解密器
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CBC(self.aes_iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # 解密
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # 去填充
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data.decode('utf-8')
        except Exception as e:
            logger.error(f"解密数据时出错: {e}")
            raise
    
    def generate_token(self, user_id: int, role: str = 'user') -> str:
        """生成JWT令牌
        
        Args:
            user_id: 用户ID
            role: 用户角色
            
        Returns:
            JWT令牌
        """
        try:
            # 构建载荷
            payload = {
                'user_id': user_id,
                'role': role,
                'exp': datetime.utcnow() + timedelta(seconds=self.token_expiry),
                'iat': datetime.utcnow(),
                'jti': self._generate_jti()
            }
            
            # 生成令牌
            token = jwt.encode(payload, self.token_secret, algorithm='HS256')
            
            return token
        except Exception as e:
            logger.error(f"生成令牌时出错: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌载荷
        """
        try:
            # 验证令牌
            payload = jwt.decode(token, self.token_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("令牌已过期")
            raise
        except jwt.InvalidTokenError:
            logger.error("无效的令牌")
            raise
        except Exception as e:
            logger.error(f"验证令牌时出错: {e}")
            raise
    
    def _generate_jti(self) -> str:
        """生成JWT ID"""
        return hashlib.sha256(os.urandom(32)).hexdigest()
    
    def hash_password(self, password: str) -> str:
        """哈希密码
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        try:
            # 使用HMAC-SHA256哈希密码
            hashed = hmac.new(
                self.aes_key,  # 使用AES密钥作为哈希密钥
                password.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return hashed
        except Exception as e:
            logger.error(f"哈希密码时出错: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            password: 原始密码
            hashed_password: 哈希后的密码
            
        Returns:
            密码是否正确
        """
        try:
            return self.hash_password(password) == hashed_password
        except Exception as e:
            logger.error(f"验证密码时出错: {e}")
            return False
    
    def generate_csrf_token(self, user_id: int) -> str:
        """生成CSRF令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            CSRF令牌
        """
        try:
            # 构建CSRF令牌
            data = f"{user_id}:{datetime.utcnow().isoformat()}"
            token = hmac.new(
                self.aes_key,
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return token
        except Exception as e:
            logger.error(f"生成CSRF令牌时出错: {e}")
            raise
    
    def verify_csrf_token(self, user_id: int, token: str) -> bool:
        """验证CSRF令牌
        
        Args:
            user_id: 用户ID
            token: CSRF令牌
            
        Returns:
            CSRF令牌是否有效
        """
        try:
            # 验证CSRF令牌
            data = f"{user_id}:{datetime.utcnow().isoformat().split('.')[0]}"
            expected_token = hmac.new(
                self.aes_key,
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return token == expected_token
        except Exception as e:
            logger.error(f"验证CSRF令牌时出错: {e}")
            return False

# 创建安全管理器实例
security_manager = SecurityManager()

# 安全相关的辅助函数
def get_current_user(token: str) -> Dict[str, Any]:
    """获取当前用户信息
    
    Args:
        token: JWT令牌
        
    Returns:
        用户信息
    """
    return security_manager.verify_token(token)

def require_role(required_role: str):
    """角色装饰器
    
    Args:
        required_role: 所需角色
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从请求中获取令牌和用户信息
            # 这里需要根据具体的框架和请求上下文来实现
            # 例如，在FastAPI中，可以通过Depends获取当前用户
            user_info = kwargs.get('user_info')
            if not user_info:
                raise ValueError("用户信息不存在")
            
            if user_info.get('role') != required_role:
                raise ValueError("权限不足")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator