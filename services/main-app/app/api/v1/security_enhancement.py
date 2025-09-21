"""
安全加固API端点
提供权限控制、数据加密、安全审计等功能
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.core.security import get_current_active_user
from app.services.security_enhancement_service import security_enhancement_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/security", tags=["security"])


# 请求模型
class EncryptDataRequest(BaseModel):
    data: str = Field(..., description="要加密的数据")


class DecryptDataRequest(BaseModel):
    encrypted_data: str = Field(..., description="要解密的数据")


class RSAEncryptRequest(BaseModel):
    data: str = Field(..., description="要RSA加密的数据")


class RSADecryptRequest(BaseModel):
    encrypted_data: str = Field(..., description="要RSA解密的数据")


class HashPasswordRequest(BaseModel):
    password: str = Field(..., description="要哈希的密码")


class VerifyPasswordRequest(BaseModel):
    password: str = Field(..., description="要验证的密码")
    hashed_password: str = Field(..., description="已哈希的密码")
    salt: str = Field(..., description="盐值")


class GenerateTokenRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    additional_claims: Optional[Dict[str, Any]] = Field(None, description="额外声明")


class RevokeTokenRequest(BaseModel):
    token: str = Field(..., description="要撤销的令牌")


class CheckPermissionRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")


class SecurityReportRequest(BaseModel):
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")


# 响应模型
class EncryptDataResponse(BaseModel):
    encrypted_data: str
    algorithm: str = "AES-256"


class DecryptDataResponse(BaseModel):
    decrypted_data: str


class RSAEncryptResponse(BaseModel):
    encrypted_data: str
    algorithm: str = "RSA-OAEP"


class RSADecryptResponse(BaseModel):
    decrypted_data: str


class HashPasswordResponse(BaseModel):
    hashed_password: str
    salt: str
    algorithm: str = "PBKDF2-SHA256"


class VerifyPasswordResponse(BaseModel):
    is_valid: bool


class GenerateTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    token_id: str


class RevokeTokenResponse(BaseModel):
    success: bool
    message: str


class CheckPermissionResponse(BaseModel):
    has_permission: bool
    user_id: str
    resource: str
    action: str


class SecurityReportResponse(BaseModel):
    report_period: Dict[str, str]
    summary: Dict[str, int]
    top_events: List[Dict[str, Any]]
    recommendations: List[str]


@router.get("/health")
async def security_health_check():
    """安全服务健康检查"""
    return {
        "status": "healthy",
        "service": "security_enhancement",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "data_encryption",
            "rsa_encryption",
            "secure_password_hashing",
            "token_management",
            "permission_checking",
            "security_auditing"
        ]
    }


@router.post("/encrypt", response_model=EncryptDataResponse)
async def encrypt_data(
    request: EncryptDataRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """加密敏感数据"""
    try:
        encrypted_data = await security_enhancement_service.encrypt_sensitive_data(request.data)
        
        # 记录加密操作审计日志
        await security_enhancement_service.log_security_event(
            "data_encrypted",
            current_user["id"],
            {"data_length": len(request.data)}
        )
        
        return EncryptDataResponse(
            encrypted_data=encrypted_data,
            algorithm="AES-256"
        )
    except Exception as e:
        logger.error(f"Failed to encrypt data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt data"
        )


@router.post("/decrypt", response_model=DecryptDataResponse)
async def decrypt_data(
    request: DecryptDataRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """解密敏感数据"""
    try:
        decrypted_data = await security_enhancement_service.decrypt_sensitive_data(request.encrypted_data)
        
        # 记录解密操作审计日志
        await security_enhancement_service.log_security_event(
            "data_decrypted",
            current_user["id"],
            {"data_length": len(decrypted_data)}
        )
        
        return DecryptDataResponse(decrypted_data=decrypted_data)
    except Exception as e:
        logger.error(f"Failed to decrypt data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt data"
        )


@router.post("/rsa/encrypt", response_model=RSAEncryptResponse)
async def rsa_encrypt(
    request: RSAEncryptRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """RSA加密数据"""
    try:
        encrypted_data = await security_enhancement_service.rsa_encrypt(request.data)
        
        # 记录RSA加密操作审计日志
        await security_enhancement_service.log_security_event(
            "rsa_encrypted",
            current_user["id"],
            {"data_length": len(request.data)}
        )
        
        return RSAEncryptResponse(
            encrypted_data=encrypted_data,
            algorithm="RSA-OAEP"
        )
    except Exception as e:
        logger.error(f"Failed to RSA encrypt data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to RSA encrypt data"
        )


@router.post("/rsa/decrypt", response_model=RSADecryptResponse)
async def rsa_decrypt(
    request: RSADecryptRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """RSA解密数据"""
    try:
        decrypted_data = await security_enhancement_service.rsa_decrypt(request.encrypted_data)
        
        # 记录RSA解密操作审计日志
        await security_enhancement_service.log_security_event(
            "rsa_decrypted",
            current_user["id"],
            {"data_length": len(decrypted_data)}
        )
        
        return RSADecryptResponse(decrypted_data=decrypted_data)
    except Exception as e:
        logger.error(f"Failed to RSA decrypt data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to RSA decrypt data"
        )


@router.post("/password/hash", response_model=HashPasswordResponse)
async def hash_password(
    request: HashPasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """安全密码哈希"""
    try:
        hashed_password, salt = await security_enhancement_service.hash_password_secure(request.password)
        
        # 记录密码哈希操作审计日志
        await security_enhancement_service.log_security_event(
            "password_hashed",
            current_user["id"],
            {"password_length": len(request.password)}
        )
        
        return HashPasswordResponse(
            hashed_password=hashed_password,
            salt=salt,
            algorithm="PBKDF2-SHA256"
        )
    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to hash password"
        )


@router.post("/password/verify", response_model=VerifyPasswordResponse)
async def verify_password(
    request: VerifyPasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """验证密码"""
    try:
        is_valid = await security_enhancement_service.verify_password_secure(
            request.password,
            request.hashed_password,
            request.salt
        )
        
        # 记录密码验证操作审计日志
        await security_enhancement_service.log_security_event(
            "password_verified",
            current_user["id"],
            {"is_valid": is_valid}
        )
        
        return VerifyPasswordResponse(is_valid=is_valid)
    except Exception as e:
        logger.error(f"Failed to verify password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify password"
        )


@router.post("/token/generate", response_model=GenerateTokenResponse)
async def generate_secure_token(
    request: GenerateTokenRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """生成安全令牌"""
    try:
        token = await security_enhancement_service.generate_secure_token(
            request.user_id,
            request.additional_claims
        )
        
        # 解析令牌获取过期时间
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        expires_at = datetime.fromtimestamp(payload["exp"])
        token_id = payload["jti"]
        
        return GenerateTokenResponse(
            token=token,
            expires_at=expires_at,
            token_id=token_id
        )
    except Exception as e:
        logger.error(f"Failed to generate secure token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secure token"
        )


@router.post("/token/revoke", response_model=RevokeTokenResponse)
async def revoke_token(
    request: RevokeTokenRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """撤销令牌"""
    try:
        success = await security_enhancement_service.revoke_token(
            request.token,
            current_user["id"]
        )
        
        return RevokeTokenResponse(
            success=success,
            message="Token revoked successfully" if success else "Failed to revoke token"
        )
    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke token"
        )


@router.post("/permission/check", response_model=CheckPermissionResponse)
async def check_permission(
    request: CheckPermissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """检查用户权限"""
    try:
        has_permission = await security_enhancement_service.check_permission(
            request.user_id,
            request.resource,
            request.action
        )
        
        # 记录权限检查审计日志
        await security_enhancement_service.log_security_event(
            "permission_checked",
            current_user["id"],
            {
                "target_user_id": request.user_id,
                "resource": request.resource,
                "action": request.action,
                "has_permission": has_permission
            }
        )
        
        return CheckPermissionResponse(
            has_permission=has_permission,
            user_id=request.user_id,
            resource=request.resource,
            action=request.action
        )
    except Exception as e:
        logger.error(f"Failed to check permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check permission"
        )


@router.post("/report", response_model=SecurityReportResponse)
async def generate_security_report(
    request: SecurityReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """生成安全报告"""
    try:
        report = await security_enhancement_service.generate_security_report(
            request.start_date,
            request.end_date
        )
        
        # 记录安全报告生成审计日志
        await security_enhancement_service.log_security_event(
            "security_report_generated",
            current_user["id"],
            {
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "total_events": report["summary"]["total_events"]
            }
        )
        
        return SecurityReportResponse(**report)
    except Exception as e:
        logger.error(f"Failed to generate security report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate security report"
        )


@router.get("/suspicious-activity")
async def check_suspicious_activity(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """检查可疑活动"""
    try:
        # 模拟活动数据
        activity_data = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        is_suspicious = await security_enhancement_service.detect_suspicious_activity(
            user_id,
            activity_data
        )
        
        return {
            "user_id": user_id,
            "is_suspicious": is_suspicious,
            "activity_data": activity_data,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to check suspicious activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check suspicious activity"
        )


@router.get("/public-key")
async def get_public_key():
    """获取RSA公钥"""
    try:
        # 获取公钥的PEM格式
        public_key_pem = security_enhancement_service.rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        return {
            "public_key": public_key_pem,
            "algorithm": "RSA",
            "key_size": 2048
        }
    except Exception as e:
        logger.error(f"Failed to get public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get public key"
        )
