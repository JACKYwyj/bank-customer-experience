"""
公共配置模块 - 环境变量、数据库、API路由配置
Common Configuration Module
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "Bank Customer Experience"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/bank_customer",
        alias="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis配置
    REDIS_HOST: str = Field(default="localhost", alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, alias="REDIS_PORT")
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    
    # Kafka配置
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_TOPIC_EMOTION: str = "emotion-events"
    KAFKA_TOPIC_JOURNEY: str = "journey-events"
    KAFKA_TOPIC_SERVICE: str = "service-flow-events"
    KAFKA_CONSUMER_GROUP: str = "bank-customer-experience"
    
    # JWT配置
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://bank-customer-experience.com"
    ]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 服务特定配置
    EMOTION_RECOGNITION_ENABLED: bool = True
    EMPATHY_AI_ENABLED: bool = True
    PRIVACY_SHIELD_ENABLED: bool = True
    
    # 空间优化配置
    SPACE_OPTIMIZER_WEIGHT_SERVICE: float = 0.35
    SPACE_OPTIMIZER_WEIGHT_EXPERIENCE: float = 0.40
    SPACE_OPTIMIZER_WEIGHT_UTILIZATION: float = 0.25
    
    # 客户旅程配置
    JOURNEY_EVENT_RETENTION_DAYS: int = 90
    JOURNEY_RECOMMENDATION_LIMIT: int = 10
    
    # 服务流程配置
    FLOW_INSTANCE_TIMEOUT_MINUTES: int = 60
    FLOW_MAX_CONCURRENT_INSTANCES: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


# 全局配置实例
settings = get_settings()
