import configparser
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """配置文件管理类"""
    
    def __init__(self, config_path: str = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            # 默认配置文件路径
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
        else:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def getint(self, section: str, key: str, default: int = None) -> int:
        """获取整数类型配置值"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def getfloat(self, section: str, key: str, default: float = None) -> float:
        """获取浮点数类型配置值"""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def getboolean(self, section: str, key: str, default: bool = None) -> bool:
        """获取布尔类型配置值"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def getlist(self, section: str, key: str, default: list = None, sep: str = ',') -> list:
        """获取列表类型配置值"""
        try:
            value = self.config.get(section, key)
            return [item.strip() for item in value.split(sep) if item.strip()]
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default or []
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置节
        
        Args:
            section: 配置节
            
        Returns:
            配置节的所有键值对
        """
        try:
            return dict(self.config[section])
        except configparser.NoSectionError:
            return {}
    
    def has_section(self, section: str) -> bool:
        """检查配置节是否存在"""
        return section in self.config
    
    def has_option(self, section: str, key: str) -> bool:
        """检查配置项是否存在"""
        return self.config.has_option(section, key)
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config(section: str, key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return config_manager.get(section, key, default)

def get_config_int(section: str, key: str, default: int = None) -> int:
    """获取整数类型配置值的便捷函数"""
    return config_manager.getint(section, key, default)

def get_config_float(section: str, key: str, default: float = None) -> float:
    """获取浮点数类型配置值的便捷函数"""
    return config_manager.getfloat(section, key, default)

def get_config_bool(section: str, key: str, default: bool = None) -> bool:
    """获取布尔类型配置值的便捷函数"""
    return config_manager.getboolean(section, key, default)

def get_config_list(section: str, key: str, default: list = None, sep: str = ',') -> list:
    """获取列表类型配置值的便捷函数"""
    return config_manager.getlist(section, key, default, sep)
