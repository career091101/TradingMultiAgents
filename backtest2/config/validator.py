"""Configuration validation utilities"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import fields


logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigValidator:
    """Validates configuration values"""
    
    @staticmethod
    def validate_range(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str = "value"
    ) -> None:
        """Validate that value is within range"""
        if min_value is not None and value < min_value:
            raise ConfigValidationError(
                f"{field_name} ({value}) is below minimum allowed value ({min_value})"
            )
        if max_value is not None and value > max_value:
            raise ConfigValidationError(
                f"{field_name} ({value}) is above maximum allowed value ({max_value})"
            )
            
    @staticmethod
    def validate_positive(value: Union[int, float], field_name: str = "value") -> None:
        """Validate that value is positive"""
        if value <= 0:
            raise ConfigValidationError(f"{field_name} must be positive, got {value}")
            
    @staticmethod
    def validate_probability(value: float, field_name: str = "value") -> None:
        """Validate that value is a valid probability (0-1)"""
        ConfigValidator.validate_range(value, 0.0, 1.0, field_name)
        
    @staticmethod
    def validate_percentage(value: float, field_name: str = "value") -> None:
        """Validate that value is a valid percentage (0-100)"""
        ConfigValidator.validate_range(value, 0.0, 100.0, field_name)
        
    @staticmethod
    def validate_not_empty(value: Any, field_name: str = "value") -> None:
        """Validate that value is not empty"""
        if not value:
            raise ConfigValidationError(f"{field_name} cannot be empty")


def validate_risk_config(config: 'RiskConfig') -> List[str]:
    """Validate RiskConfig and return list of warnings"""
    warnings = []
    
    try:
        # Validate position limits
        for profile, limit in config.position_limits.items():
            ConfigValidator.validate_probability(limit, f"position_limit[{profile}]")
        
        # Validate confidence thresholds
        for level, threshold in config.confidence_thresholds.items():
            ConfigValidator.validate_probability(threshold, f"confidence_threshold[{level}]")
        
        # Validate stop loss and take profit
        ConfigValidator.validate_probability(config.stop_loss, "stop_loss")
        ConfigValidator.validate_probability(config.take_profit, "take_profit")
        
        # Validate max positions
        ConfigValidator.validate_positive(config.max_positions, "max_positions")
        ConfigValidator.validate_range(config.max_positions, 1, 100, "max_positions")
        
        # Validate min trade size
        ConfigValidator.validate_positive(config.min_trade_size, "min_trade_size")
        
        # Validate max position size percentage
        ConfigValidator.validate_probability(
            config.max_position_size_pct,
            "max_position_size_pct"
        )
        
        # Logical validations
        if config.stop_loss >= config.take_profit:
            warnings.append("stop_loss should be less than take_profit")
            
        # Check confidence thresholds are ordered
        thresholds = config.confidence_thresholds
        if thresholds.get('high', 0) <= thresholds.get('medium', 0):
            warnings.append("high confidence threshold should be greater than medium")
        if thresholds.get('medium', 0) <= thresholds.get('low', 0):
            warnings.append("medium confidence threshold should be greater than low")
            
    except ConfigValidationError as e:
        raise ConfigValidationError(f"RiskConfig validation failed: {e}")
        
    return warnings


def validate_backtest_config(config: 'BacktestConfig') -> List[str]:
    """Validate BacktestConfig and return list of warnings"""
    warnings = []
    
    try:
        # Validate capital
        ConfigValidator.validate_positive(config.initial_capital, "initial_capital")
        
        # Validate slippage
        ConfigValidator.validate_range(config.slippage, 0.0, 0.1, "slippage")
        if config.slippage > 0.01:
            warnings.append(f"High slippage ({config.slippage}) may impact results significantly")
            
        # Validate commission
        ConfigValidator.validate_range(config.commission, 0.0, 0.1, "commission")
        if config.commission > 0.01:
            warnings.append(f"High commission ({config.commission}) may impact results significantly")
            
        # Validate risk-free rate
        ConfigValidator.validate_range(config.risk_free_rate, 0.0, 0.2, "risk_free_rate")
        
        # Validate max positions
        ConfigValidator.validate_positive(config.max_positions, "max_positions")
        
        # Validate symbols
        ConfigValidator.validate_not_empty(config.symbols, "symbols")
        
        # Validate dates if provided
        if config.start_date and config.end_date:
            if config.start_date >= config.end_date:
                raise ConfigValidationError("start_date must be before end_date")
                
        # Cross-validate with risk config
        if config.risk_config:
            risk_warnings = validate_risk_config(config.risk_config)
            warnings.extend(risk_warnings)
            
    except ConfigValidationError as e:
        raise ConfigValidationError(f"BacktestConfig validation failed: {e}")
        
    return warnings


def validate_constants(constants: Any) -> List[str]:
    """Validate a constants dataclass and return warnings"""
    warnings = []
    class_name = constants.__class__.__name__
    
    try:
        for field in fields(constants):
            value = getattr(constants, field.name)
            field_type = field.type
            
            # Skip None values and complex types
            if value is None or isinstance(value, (dict, list)):
                continue
                
            # Validate based on field name patterns
            if "ratio" in field.name or "threshold" in field.name and isinstance(value, float):
                if not 0 <= value <= 1:
                    warnings.append(
                        f"{class_name}.{field.name} ({value}) should be between 0 and 1"
                    )
                    
            elif "percentage" in field.name or "pct" in field.name:
                if not 0 <= value <= 100:
                    warnings.append(
                        f"{class_name}.{field.name} ({value}) should be between 0 and 100"
                    )
                    
            elif "size" in field.name or "count" in field.name:
                if isinstance(value, (int, float)) and value <= 0:
                    warnings.append(
                        f"{class_name}.{field.name} ({value}) should be positive"
                    )
                    
            elif "multiplier" in field.name or "factor" in field.name:
                if isinstance(value, float) and value < 0:
                    warnings.append(
                        f"{class_name}.{field.name} ({value}) should be non-negative"
                    )
                    
            elif "days" in field.name or "seconds" in field.name or "minutes" in field.name:
                if isinstance(value, (int, float)) and value <= 0:
                    warnings.append(
                        f"{class_name}.{field.name} ({value}) should be positive"
                    )
                    
    except Exception as e:
        logger.error(f"Error validating {class_name}: {e}")
        
    return warnings


def validate_all_constants() -> Dict[str, List[str]]:
    """Validate all constants and return warnings by module"""
    from .constants import (
        RISK_ANALYSIS,
        POSITION_MANAGEMENT,
        CACHE_MANAGEMENT,
        MEMORY_MANAGEMENT,
        RETRY_HANDLER,
        TRANSACTION
    )
    
    all_warnings = {}
    
    # Validate each constants module
    for name, constants in [
        ("RISK_ANALYSIS", RISK_ANALYSIS),
        ("POSITION_MANAGEMENT", POSITION_MANAGEMENT),
        ("CACHE_MANAGEMENT", CACHE_MANAGEMENT),
        ("MEMORY_MANAGEMENT", MEMORY_MANAGEMENT),
        ("RETRY_HANDLER", RETRY_HANDLER),
        ("TRANSACTION", TRANSACTION)
    ]:
        warnings = validate_constants(constants)
        if warnings:
            all_warnings[name] = warnings
            
    # Log all warnings
    if all_warnings:
        logger.warning("Configuration validation warnings found:")
        for module, warnings in all_warnings.items():
            for warning in warnings:
                logger.warning(f"  {module}: {warning}")
                
    return all_warnings