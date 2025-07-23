"""
Phase 2 E2E Test Configuration
Settings and constants for advanced testing scenarios
"""

import os
from typing import Dict, List, Any


class Phase2TestConfig:
    """Configuration for Phase 2 E2E tests"""
    
    # Base URLs
    BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8501")
    API_BASE_URL = os.getenv("E2E_API_BASE_URL", "http://localhost:8501/api")
    
    # Test timeouts (milliseconds)
    TIMEOUTS = {
        "default": 30000,
        "analysis": 60000,
        "pdf_generation": 90000,
        "network_request": 15000,
        "page_load": 10000,
        "element_visible": 5000
    }
    
    # Performance budgets
    PERFORMANCE_BUDGETS = {
        "dashboard": {
            "domContentLoaded": 3000,
            "loadComplete": 5000,
            "firstPaint": 2000,
            "firstContentfulPaint": 2500,
            "memoryUsageMB": 50
        },
        "settings": {
            "domContentLoaded": 2000,
            "loadComplete": 3000,
            "memoryUsageMB": 30
        },
        "execution": {
            "domContentLoaded": 2000,
            "loadComplete": 3000,
            "analysisComplete": 60000,
            "memoryUsageMB": 75
        },
        "results": {
            "domContentLoaded": 4000,
            "loadComplete": 8000,
            "chartRender": 5000,
            "memoryUsageMB": 100
        }
    }
    
    # Responsive design breakpoints
    BREAKPOINTS = {
        "mobile": {"width": 375, "height": 812},
        "mobile_large": {"width": 414, "height": 896},
        "tablet": {"width": 768, "height": 1024},
        "tablet_large": {"width": 1024, "height": 768},
        "desktop": {"width": 1920, "height": 1080},
        "desktop_small": {"width": 1366, "height": 768}
    }
    
    # Test data sets
    STOCK_SYMBOLS = {
        "valid": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
            "META", "NVDA", "JPM", "JNJ", "V",
            "PG", "UNH", "HD", "MA", "DIS"
        ],
        "special_chars": [
            "BRK.A", "BF.B", "GOOG", "GOOGL"
        ],
        "invalid": [
            "INVALID123", "NOTREAL", "12345", "!@#$%", 
            "", "   ", "TOOLONG" * 10
        ],
        "edge_cases": [
            "A", "ZZ", "AAA", "ZZZZ"  # Very short symbols
        ]
    }
    
    # Security test payloads
    SECURITY_PAYLOADS = {
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "<<SCRIPT>alert('XSS')//<</SCRIPT>",
            "<script>document.location='http://evil.com'</script>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>"
        ],
        "sql_injection": [
            "'; DROP TABLE stocks; --",
            "' OR '1'='1",
            "'; DELETE FROM users; --",
            "' UNION SELECT password FROM users --",
            "admin'/*",
            "' OR 1=1 --",
            "'; EXEC sp_configure 'show advanced options', 1 --"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ],
        "special_chars": [
            "!@#$%^&*()",
            "~`{}[]|\\:;\"'<>,.?/",
            "áéíóúñü",
            "中文字符",
            "العربية", 
            "🚀💎📈"
        ]
    }
    
    # Error scenarios for testing
    ERROR_SCENARIOS = {
        "network_failure": {
            "description": "Complete network failure",
            "action": "abort_all_requests"
        },
        "api_timeout": {
            "description": "API request timeout",
            "delay_ms": 30000
        },
        "rate_limit": {
            "description": "API rate limit exceeded",
            "status": 429,
            "response": {
                "error": "Rate limit exceeded",
                "message": "API制限に達しました。しばらくお待ちください",
                "retry_after": 60
            }
        },
        "server_overload": {
            "description": "Server overload (529 error)",
            "status": 529,
            "response": {
                "type": "error",
                "error": {
                    "type": "overloaded_error",
                    "message": "Overloaded"
                }
            }
        },
        "server_error": {
            "description": "Internal server error",
            "status": 500,
            "response": {
                "error": "Internal server error",
                "message": "サーバーエラーが発生しました"
            }
        },
        "unauthorized": {
            "description": "Unauthorized access",
            "status": 401,
            "response": {
                "error": "Unauthorized",
                "message": "認証に失敗しました"
            }
        },
        "not_found": {
            "description": "Resource not found",
            "status": 404,
            "response": {
                "error": "Not found",
                "message": "指定されたリソースが見つかりません"
            }
        }
    }
    
    # Browser configurations
    BROWSER_CONFIGS = {
        "chromium": {
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions"
            ]
        },
        "firefox": {
            "args": [
                "--headless"
            ]
        },
        "webkit": {
            "args": []
        }
    }
    
    # Mobile device configurations
    MOBILE_DEVICES = {
        "iphone_12": {
            "viewport": {"width": 390, "height": 844},
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "device_scale_factor": 3,
            "is_mobile": True,
            "has_touch": True
        },
        "android_pixel": {
            "viewport": {"width": 393, "height": 851},
            "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 4) AppleWebKit/537.36",
            "device_scale_factor": 2.75,
            "is_mobile": True,
            "has_touch": True
        },
        "ipad": {
            "viewport": {"width": 768, "height": 1024},
            "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "device_scale_factor": 2,
            "is_mobile": False,
            "has_touch": True
        }
    }
    
    # Test execution settings
    TEST_SETTINGS = {
        "parallel_workers": 4,
        "retry_count": 2,
        "screenshot_on_failure": True,
        "capture_trace": True,
        "slow_mo": 100,  # milliseconds
        "video_mode": "retain-on-failure"
    }
    
    # Accessibility settings
    ACCESSIBILITY_CONFIG = {
        "required_headers": ["h1", "h2", "h3"],
        "max_heading_levels": 6,
        "required_alt_text": True,
        "required_form_labels": True,
        "color_contrast_ratio": 4.5,
        "focus_indicators": True
    }
    
    # Security headers to check
    SECURITY_HEADERS = [
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Strict-Transport-Security"
    ]
    
    # Environment-specific overrides
    @classmethod
    def get_config(cls, environment: str = "local") -> Dict[str, Any]:
        """Get environment-specific configuration"""
        base_config = {
            "base_url": cls.BASE_URL,
            "timeouts": cls.TIMEOUTS,
            "performance_budgets": cls.PERFORMANCE_BUDGETS,
            "breakpoints": cls.BREAKPOINTS,
            "test_settings": cls.TEST_SETTINGS
        }
        
        env_overrides = {
            "ci": {
                "timeouts": {**cls.TIMEOUTS, "default": 45000, "analysis": 90000},
                "test_settings": {**cls.TEST_SETTINGS, "parallel_workers": 2}
            },
            "staging": {
                "base_url": "https://staging.tradingagents.com"
            },
            "production": {
                "base_url": "https://tradingagents.com",
                "test_settings": {**cls.TEST_SETTINGS, "parallel_workers": 1}
            }
        }
        
        if environment in env_overrides:
            # Deep merge configurations
            for key, value in env_overrides[environment].items():
                if isinstance(value, dict) and key in base_config:
                    base_config[key] = {**base_config[key], **value}
                else:
                    base_config[key] = value
        
        return base_config


# Test categories and priorities
TEST_CATEGORIES = {
    "smoke": {
        "priority": "critical",
        "timeout_multiplier": 1.0,
        "retry_count": 3
    },
    "regression": {
        "priority": "high", 
        "timeout_multiplier": 1.2,
        "retry_count": 2
    },
    "performance": {
        "priority": "medium",
        "timeout_multiplier": 2.0,
        "retry_count": 1
    },
    "security": {
        "priority": "high",
        "timeout_multiplier": 1.5,
        "retry_count": 2
    },
    "accessibility": {
        "priority": "medium",
        "timeout_multiplier": 1.0,
        "retry_count": 1
    },
    "visual": {
        "priority": "low",
        "timeout_multiplier": 1.0,
        "retry_count": 1
    }
}


# Test markers for pytest
PYTEST_MARKERS = {
    "smoke": "marks tests as smoke tests",
    "regression": "marks tests as regression tests", 
    "performance": "marks tests as performance tests",
    "security": "marks tests as security tests",
    "accessibility": "marks tests as accessibility tests",
    "visual": "marks tests as visual regression tests",
    "slow": "marks tests as slow running tests",
    "network": "marks tests that require network access",
    "api": "marks tests that interact with APIs"
}