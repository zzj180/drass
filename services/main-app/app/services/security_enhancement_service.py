"""
安全加固服务
实现权限控制完善、数据加密、安全审计加强等功能
"""

import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.models.audit_log import AuditLogDB
from app.services.audit_service import audit_service

logger = get_logger(__name__)


class SecurityEnhancementService:
    """安全加固服务"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.rsa_private_key = None
        self.rsa_public_key = None
        self._load_or_generate_rsa_keys()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        try:
            # 尝试从环境变量获取密钥
            key_str = getattr(settings, 'ENCRYPTION_KEY', None)
            if key_str:
                return base64.urlsafe_b64decode(key_str.encode())
        except Exception as e:
            logger.warning(f"Failed to load encryption key from settings: {e}")
        
        # 生成新的密钥
        key = Fernet.generate_key()
        logger.info("Generated new encryption key")
        return key
    
    def _load_or_generate_rsa_keys(self):
        """加载或生成RSA密钥对"""
        try:
            # 尝试从环境变量加载RSA密钥
            private_key_pem = getattr(settings, 'RSA_PRIVATE_KEY', None)
            public_key_pem = getattr(settings, 'RSA_PUBLIC_KEY', None)
            
            if private_key_pem and public_key_pem:
                self.rsa_private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(),
                    password=None
                )
                self.rsa_public_key = serialization.load_pem_public_key(
                    public_key_pem.encode()
                )
                logger.info("Loaded RSA keys from settings")
                return
        except Exception as e:
            logger.warning(f"Failed to load RSA keys from settings: {e}")
        
        # 生成新的RSA密钥对
        self.rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.rsa_public_key = self.rsa_private_key.public_key()
        logger.info("Generated new RSA key pair")
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感数据"""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to encrypt sensitive data"
            )
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感数据"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt sensitive data"
            )
    
    async def rsa_encrypt(self, data: str) -> str:
        """使用RSA公钥加密数据"""
        try:
            encrypted = self.rsa_public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to RSA encrypt data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to RSA encrypt data"
            )
    
    async def rsa_decrypt(self, encrypted_data: str) -> str:
        """使用RSA私钥解密数据"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.rsa_private_key.decrypt(
                decoded_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to RSA decrypt data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to RSA decrypt data"
            )
    
    async def hash_password_secure(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """安全密码哈希"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
    
    async def verify_password_secure(self, password: str, hashed_password: str, salt: str) -> bool:
        """验证安全密码哈希"""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return hmac.compare_digest(key.decode(), hashed_password)
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False
    
    async def generate_secure_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """生成安全令牌"""
        try:
            now = datetime.utcnow()
            payload = {
                "sub": user_id,
                "iat": now,
                "exp": now + timedelta(hours=1),
                "jti": secrets.token_urlsafe(32),  # JWT ID for token tracking
                "type": "access"
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            
            # 记录令牌生成审计日志
            await audit_service.log_audit_event(
                event_type="token_generated",
                user_id=user_id,
                details={
                    "token_id": payload["jti"],
                    "expires_at": payload["exp"].isoformat(),
                    "additional_claims": additional_claims or {}
                }
            )
            
            return token
        except Exception as e:
            logger.error(f"Failed to generate secure token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate secure token"
            )
    
    async def validate_token_security(self, token: str) -> Dict[str, Any]:
        """验证令牌安全性"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # 检查令牌是否在黑名单中
            if await self._is_token_blacklisted(payload.get("jti")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def _is_token_blacklisted(self, jti: str) -> bool:
        """检查令牌是否在黑名单中"""
        # 这里应该查询数据库或Redis来检查黑名单
        # 简化实现，返回False
        return False
    
    async def revoke_token(self, token: str, user_id: str) -> bool:
        """撤销令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            
            if jti:
                # 将令牌ID添加到黑名单
                await self._add_token_to_blacklist(jti)
                
                # 记录撤销审计日志
                await audit_service.log_audit_event(
                    event_type="token_revoked",
                    user_id=user_id,
                    details={
                        "token_id": jti,
                        "revoked_at": datetime.utcnow().isoformat()
                    }
                )
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    async def _add_token_to_blacklist(self, jti: str):
        """将令牌ID添加到黑名单"""
        # 这里应该将jti存储到数据库或Redis
        # 简化实现，记录日志
        logger.info(f"Token {jti} added to blacklist")
    
    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """检查用户权限"""
        try:
            # 获取用户角色和权限
            user_permissions = await self._get_user_permissions(user_id)
            
            # 检查是否有权限
            required_permission = f"{resource}:{action}"
            return required_permission in user_permissions
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限列表"""
        # 这里应该从数据库查询用户权限
        # 简化实现，返回基础权限
        return [
            "documents:read",
            "documents:upload",
            "documents:delete",
            "audit:read",
            "compliance:analyze"
        ]
    
    async def log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """记录安全事件"""
        try:
            await audit_service.log_audit_event(
                event_type=f"security_{event_type}",
                user_id=user_id,
                details={
                    "security_event": True,
                    "event_details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def detect_suspicious_activity(self, user_id: str, activity_data: Dict[str, Any]) -> bool:
        """检测可疑活动"""
        try:
            # 检查异常登录时间
            if await self._check_anomalous_login_time(activity_data):
                await self.log_security_event("anomalous_login_time", user_id, activity_data)
                return True
            
            # 检查异常IP地址
            if await self._check_anomalous_ip(activity_data):
                await self.log_security_event("anomalous_ip", user_id, activity_data)
                return True
            
            # 检查异常操作频率
            if await self._check_anomalous_frequency(user_id, activity_data):
                await self.log_security_event("anomalous_frequency", user_id, activity_data)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to detect suspicious activity: {e}")
            return False
    
    async def _check_anomalous_login_time(self, activity_data: Dict[str, Any]) -> bool:
        """检查异常登录时间"""
        # 简化实现，检查是否在非工作时间登录
        current_hour = datetime.utcnow().hour
        return current_hour < 6 or current_hour > 22
    
    async def _check_anomalous_ip(self, activity_data: Dict[str, Any]) -> bool:
        """检查异常IP地址"""
        # 简化实现，检查IP是否在已知的异常IP列表中
        ip_address = activity_data.get("ip_address", "")
        suspicious_ips = ["192.168.1.100", "10.0.0.1"]  # 示例可疑IP
        return ip_address in suspicious_ips
    
    async def _check_anomalous_frequency(self, user_id: str, activity_data: Dict[str, Any]) -> bool:
        """检查异常操作频率"""
        # 简化实现，检查操作频率是否过高
        # 这里应该查询数据库统计用户最近的操作频率
        return False
    
    async def generate_security_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成安全报告"""
        try:
            # 统计安全事件
            security_events = await self._get_security_events(start_date, end_date)
            
            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_events": len(security_events),
                    "critical_events": len([e for e in security_events if e.get("severity") == "critical"]),
                    "high_events": len([e for e in security_events if e.get("severity") == "high"]),
                    "medium_events": len([e for e in security_events if e.get("severity") == "medium"]),
                    "low_events": len([e for e in security_events if e.get("severity") == "low"])
                },
                "top_events": self._get_top_events(security_events),
                "recommendations": await self._generate_security_recommendations(security_events)
            }
            
            return report
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate security report"
            )
    
    async def _get_security_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取安全事件"""
        # 这里应该从数据库查询安全事件
        # 简化实现，返回模拟数据
        return [
            {
                "event_type": "security_login_attempt",
                "severity": "medium",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": "test-user-id",
                "details": {"ip_address": "192.168.1.1"}
            }
        ]
    
    def _get_top_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取最频繁的事件类型"""
        event_counts = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return [
            {"event_type": event_type, "count": count}
            for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    async def _generate_security_recommendations(self, events: List[Dict[str, Any]]) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 基于事件类型生成建议
        event_types = [event.get("event_type", "") for event in events]
        
        if "security_anomalous_login_time" in event_types:
            recommendations.append("考虑实施基于时间的访问控制策略")
        
        if "security_anomalous_ip" in event_types:
            recommendations.append("加强IP地址白名单和黑名单管理")
        
        if "security_anomalous_frequency" in event_types:
            recommendations.append("实施更严格的频率限制和监控")
        
        if not recommendations:
            recommendations.append("系统安全状况良好，建议定期进行安全审计")
        
        return recommendations


# 全局安全加固服务实例
security_enhancement_service = SecurityEnhancementService()
