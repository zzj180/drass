"""
安全测试API端点
提供漏洞扫描、安全测试、修复建议等功能
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.security import get_current_active_user
from app.services.vulnerability_scanner import vulnerability_scanner
from app.services.security_enhancement_service import security_enhancement_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/security-testing", tags=["security-testing"])


# 请求模型
class CodeScanRequest(BaseModel):
    code_path: str = Field(..., description="要扫描的代码路径")


class WebScanRequest(BaseModel):
    url: str = Field(..., description="要扫描的Web应用URL")


class SecurityTestRequest(BaseModel):
    test_type: str = Field(default="all", description="测试类型: all, code, web, dependencies")


# 响应模型
class VulnerabilityResponse(BaseModel):
    type: str
    severity: str
    file: Optional[str] = None
    line: Optional[int] = None
    code: Optional[str] = None
    description: str
    fix_suggestion: str


class ScanReportResponse(BaseModel):
    scan_timestamp: str
    scan_path: str
    total_vulnerabilities: int
    vulnerabilities: List[VulnerabilityResponse]
    severity_summary: Dict[str, int]
    recommendations: List[str]


class SecurityTestResponse(BaseModel):
    test_timestamp: str
    test_type: str
    results: Dict[str, Any]


@router.get("/health")
async def security_testing_health_check():
    """安全测试服务健康检查"""
    return {
        "status": "healthy",
        "service": "security_testing",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "code_vulnerability_scanning",
            "web_application_scanning",
            "dependency_security_testing",
            "security_header_validation",
            "ssl_configuration_checking"
        ]
    }


@router.post("/scan/code", response_model=ScanReportResponse)
async def scan_code_vulnerabilities(
    request: CodeScanRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """扫描代码漏洞"""
    try:
        # 记录扫描操作审计日志
        await security_enhancement_service.log_security_event(
            "code_scan_initiated",
            current_user["id"],
            {"scan_path": request.code_path}
        )
        
        scan_result = await vulnerability_scanner.scan_code_vulnerabilities(request.code_path)
        
        # 记录扫描完成审计日志
        await security_enhancement_service.log_security_event(
            "code_scan_completed",
            current_user["id"],
            {
                "scan_path": request.code_path,
                "vulnerabilities_found": scan_result["total_vulnerabilities"],
                "severity_breakdown": scan_result["severity_summary"]
            }
        )
        
        return ScanReportResponse(**scan_result)
    except Exception as e:
        logger.error(f"Failed to scan code vulnerabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan code vulnerabilities"
        )


@router.post("/scan/web", response_model=ScanReportResponse)
async def scan_web_application(
    request: WebScanRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """扫描Web应用安全"""
    try:
        # 记录扫描操作审计日志
        await security_enhancement_service.log_security_event(
            "web_scan_initiated",
            current_user["id"],
            {"target_url": request.url}
        )
        
        scan_result = await vulnerability_scanner.scan_web_application(request.url)
        
        # 记录扫描完成审计日志
        await security_enhancement_service.log_security_event(
            "web_scan_completed",
            current_user["id"],
            {
                "target_url": request.url,
                "vulnerabilities_found": scan_result["total_vulnerabilities"],
                "severity_breakdown": scan_result["severity_summary"]
            }
        )
        
        return ScanReportResponse(**scan_result)
    except Exception as e:
        logger.error(f"Failed to scan web application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan web application"
        )


@router.post("/test", response_model=SecurityTestResponse)
async def run_security_tests(
    request: SecurityTestRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """运行安全测试"""
    try:
        # 记录测试操作审计日志
        await security_enhancement_service.log_security_event(
            "security_test_initiated",
            current_user["id"],
            {"test_type": request.test_type}
        )
        
        # 在后台运行测试
        test_result = await vulnerability_scanner.run_security_tests(request.test_type)
        
        # 记录测试完成审计日志
        await security_enhancement_service.log_security_event(
            "security_test_completed",
            current_user["id"],
            {
                "test_type": request.test_type,
                "test_results": test_result
            }
        )
        
        return SecurityTestResponse(**test_result)
    except Exception as e:
        logger.error(f"Failed to run security tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run security tests"
        )


@router.get("/scan/current-project")
async def scan_current_project(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """扫描当前项目"""
    try:
        # 记录扫描操作审计日志
        await security_enhancement_service.log_security_event(
            "project_scan_initiated",
            current_user["id"],
            {"project_path": "/home/qwkj/drass"}
        )
        
        # 扫描当前项目
        scan_result = await vulnerability_scanner.scan_code_vulnerabilities("/home/qwkj/drass")
        
        # 记录扫描完成审计日志
        await security_enhancement_service.log_security_event(
            "project_scan_completed",
            current_user["id"],
            {
                "project_path": "/home/qwkj/drass",
                "vulnerabilities_found": scan_result["total_vulnerabilities"],
                "severity_breakdown": scan_result["severity_summary"]
            }
        )
        
        return scan_result
    except Exception as e:
        logger.error(f"Failed to scan current project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan current project"
        )


@router.get("/scan/local-app")
async def scan_local_application(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """扫描本地应用"""
    try:
        # 记录扫描操作审计日志
        await security_enhancement_service.log_security_event(
            "local_app_scan_initiated",
            current_user["id"],
            {"target_url": "http://localhost:8888"}
        )
        
        # 扫描本地应用
        scan_result = await vulnerability_scanner.scan_web_application("http://localhost:8888")
        
        # 记录扫描完成审计日志
        await security_enhancement_service.log_security_event(
            "local_app_scan_completed",
            current_user["id"],
            {
                "target_url": "http://localhost:8888",
                "vulnerabilities_found": scan_result["total_vulnerabilities"],
                "severity_breakdown": scan_result["severity_summary"]
            }
        )
        
        return scan_result
    except Exception as e:
        logger.error(f"Failed to scan local application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan local application"
        )


@router.get("/vulnerability-types")
async def get_vulnerability_types():
    """获取漏洞类型列表"""
    return {
        "vulnerability_types": [
            {
                "type": "sql_injection",
                "severity": "critical",
                "description": "SQL injection vulnerability",
                "fix_suggestion": "Use parameterized queries or ORM methods"
            },
            {
                "type": "xss",
                "severity": "high",
                "description": "Cross-Site Scripting (XSS) vulnerability",
                "fix_suggestion": "Sanitize user input and use template escaping"
            },
            {
                "type": "path_traversal",
                "severity": "high",
                "description": "Path traversal vulnerability",
                "fix_suggestion": "Validate and sanitize file paths"
            },
            {
                "type": "hardcoded_secrets",
                "severity": "high",
                "description": "Hardcoded secret or password found",
                "fix_suggestion": "Use environment variables or secure configuration"
            },
            {
                "type": "insecure_deserialization",
                "severity": "critical",
                "description": "Insecure deserialization vulnerability",
                "fix_suggestion": "Avoid deserializing untrusted data"
            },
            {
                "type": "weak_crypto",
                "severity": "medium",
                "description": "Weak cryptographic algorithm used",
                "fix_suggestion": "Use strong cryptographic algorithms (AES-256, SHA-256)"
            },
            {
                "type": "insecure_random",
                "severity": "medium",
                "description": "Insecure random number generation",
                "fix_suggestion": "Use cryptographically secure random generators"
            },
            {
                "type": "cors_misconfiguration",
                "severity": "medium",
                "description": "CORS misconfiguration detected",
                "fix_suggestion": "Configure CORS with specific allowed origins"
            },
            {
                "type": "insecure_import",
                "severity": "medium",
                "description": "Potentially insecure module import",
                "fix_suggestion": "Use secure alternatives or validate input"
            },
            {
                "type": "insecure_dependency",
                "severity": "high",
                "description": "Insecure dependency version detected",
                "fix_suggestion": "Update to a secure version of the dependency"
            }
        ]
    }


@router.get("/security-headers")
async def get_security_headers():
    """获取安全头配置"""
    return {
        "security_headers": {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        },
        "recommendations": [
            "Implement all recommended security headers",
            "Configure Content-Security-Policy based on your application needs",
            "Use Strict-Transport-Security for HTTPS enforcement",
            "Set appropriate X-Frame-Options to prevent clickjacking",
            "Configure Referrer-Policy to control referrer information"
        ]
    }


@router.get("/scan/status")
async def get_scan_status():
    """获取扫描状态"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "available_scans": [
            "code_vulnerability_scan",
            "web_application_scan",
            "dependency_security_scan",
            "security_header_validation",
            "ssl_configuration_check"
        ],
        "last_scan": None  # 可以添加最后扫描时间
    }


@router.post("/scan/quick")
async def quick_security_scan(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """快速安全扫描"""
    try:
        # 记录快速扫描操作审计日志
        await security_enhancement_service.log_security_event(
            "quick_scan_initiated",
            current_user["id"],
            {}
        )
        
        # 运行快速扫描
        test_result = await vulnerability_scanner.run_security_tests("all")
        
        # 记录快速扫描完成审计日志
        await security_enhancement_service.log_security_event(
            "quick_scan_completed",
            current_user["id"],
            {"test_results": test_result}
        )
        
        return {
            "scan_type": "quick",
            "timestamp": datetime.utcnow().isoformat(),
            "results": test_result,
            "summary": {
                "total_tests": len(test_result.get("results", {})),
                "status": "completed"
            }
        }
    except Exception as e:
        logger.error(f"Failed to run quick security scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run quick security scan"
        )
