"""数据中心 UPS 电力计算工具库。

提供视在功率（kVA）、有功功率（kW）、无功功率（kVAR）与功率因数（PF）之间的换算函数。
"""

from __future__ import annotations

import math


def _validate_non_negative(value: float, name: str) -> None:
    """校验数值必须为非负实数。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} 必须为数值类型")
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{name} 不能为 NaN 或无穷大")
    if value < 0:
        raise ValueError(f"{name} 不能为负数: {value}")


def _validate_power_factor(power_factor: float, allow_zero: bool = True) -> None:
    """校验功率因数（PF）范围。"""
    _validate_non_negative(power_factor, "power_factor")
    if power_factor > 1.0:
        raise ValueError(f"功率因数 (PF) 不能大于 1.0: {power_factor}")
    if not allow_zero and power_factor == 0.0:
        raise ValueError("计算视在功率时，功率因数 (PF) 不能为 0")


def calc_active_power(apparent_power_kva: float, power_factor: float) -> float:
    """根据视在功率（kVA）和功率因数（PF）计算有功功率（kW）。

    公式: P (kW) = S (kVA) * PF

    Args:
        apparent_power_kva: 视在功率（单位：kVA），需 >= 0。
        power_factor: 功率因数（无量纲），取值范围 [0.0, 1.0]。

    Returns:
        有功功率（单位：kW）。
    """
    _validate_non_negative(apparent_power_kva, "apparent_power_kva")
    _validate_power_factor(power_factor, allow_zero=True)
    return float(apparent_power_kva * power_factor)


def calc_apparent_power(active_power_kw: float, power_factor: float) -> float:
    """根据有功功率（kW）和功率因数（PF）计算视在功率（kVA）。

    公式: S (kVA) = P (kW) / PF

    Args:
        active_power_kw: 有功功率（单位：kW），需 >= 0。
        power_factor: 功率因数（无量纲），取值范围 (0.0, 1.0]。

    Returns:
        视在功率（单位：kVA）。
    """
    _validate_non_negative(active_power_kw, "active_power_kw")
    _validate_power_factor(power_factor, allow_zero=False)
    return float(active_power_kw / power_factor)


def calc_power_factor(active_power_kw: float, apparent_power_kva: float) -> float:
    """根据有功功率（kW）和视在功率（kVA）计算功率因数（PF）。

    公式: PF = P (kW) / S (kVA)

    Args:
        active_power_kw: 有功功率（单位：kW），需 >= 0。
        apparent_power_kva: 视在功率（单位：kVA），需 > 0 且 >= active_power_kw。

    Returns:
        功率因数（无量纲），取值范围 [0.0, 1.0]。
    """
    _validate_non_negative(active_power_kw, "active_power_kw")
    _validate_non_negative(apparent_power_kva, "apparent_power_kva")
    if apparent_power_kva == 0.0:
        raise ValueError("视在功率 (apparent_power_kva) 不能为 0")
    if active_power_kw > apparent_power_kva:
        raise ValueError(
            f"有功功率 ({active_power_kw} kW) 不能大于视在功率 ({apparent_power_kva} kVA)"
        )
    return float(active_power_kw / apparent_power_kva)


def calc_reactive_power(apparent_power_kva: float, active_power_kw: float) -> float:
    """根据视在功率（kVA）和有功功率（kW）计算无功功率（kVAR）。

    公式: Q (kVAR) = sqrt(S^2 - P^2)

    Args:
        apparent_power_kva: 视在功率（单位：kVA），需 >= 0。
        active_power_kw: 有功功率（单位：kW），需 >= 0 且 <= apparent_power_kva。

    Returns:
        无功功率（单位：kVAR）。
    """
    _validate_non_negative(apparent_power_kva, "apparent_power_kva")
    _validate_non_negative(active_power_kw, "active_power_kw")
    if active_power_kw > apparent_power_kva:
        raise ValueError(
            f"有功功率 ({active_power_kw} kW) 不能大于视在功率 ({apparent_power_kva} kVA)"
        )
    return float(math.sqrt(apparent_power_kva**2 - active_power_kw**2))
