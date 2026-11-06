"""数据中心 UPS 电力与暖通热损耗计算工具库。

提供视在功率（kVA）、有功功率（kW）、无功功率（kVAR）、功率因数（PF）之间的换算函数，
以及基于《UPS_Technical_Spec》（KSTAR HPM3300E-200kVA）的有功热损耗（kW）与空调制冷负荷（BTU/hr）计算函数。
"""

from __future__ import annotations

import math

# 《UPS_Technical_Spec》(KSTAR HPM3300E-200kVA) 规格常量
DEVICE_MODEL: str = "KSTAR HPM3300E-200kVA"
RATED_CAPACITY_KVA: float = 200.0
RATED_ACTIVE_POWER_KW: float = 200.0
RATED_POWER_FACTOR: float = 1.0
BTU_PER_KW_HR: float = 3412.142

# 不同负载率（25%, 50%, 75%, 100%）下的系统效率（Efficiency）
SPEC_EFFICIENCY_BY_LOAD_RATIO: dict[float, float] = {
    0.25: 0.950,
    0.50: 0.965,
    0.75: 0.962,
    1.00: 0.960,
}


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


def _validate_efficiency(efficiency: float) -> None:
    """校验系统效率（efficiency）范围，必须在 (0.0, 1.0] 之间。"""
    _validate_non_negative(efficiency, "efficiency")
    if efficiency == 0.0 or efficiency > 1.0:
        raise ValueError(f"系统效率 (efficiency) 必须在 (0.0, 1.0] 范围内: {efficiency}")


def get_spec_efficiency(load_ratio: float) -> float:
    """根据《UPS_Technical_Spec》规格表获取指定负载率下的系统效率。

    支持负载率: 0.25 (25%), 0.50 (50%), 0.75 (75%), 1.00 (100%)。
    """
    _validate_non_negative(load_ratio, "load_ratio")
    for ratio_key, eff in SPEC_EFFICIENCY_BY_LOAD_RATIO.items():
        if math.isclose(load_ratio, ratio_key, rel_tol=1e-9, abs_tol=1e-9):
            return eff
    supported = ", ".join(f"{k:.2f}" for k in sorted(SPEC_EFFICIENCY_BY_LOAD_RATIO))
    raise ValueError(f"不支持的负载率 {load_ratio}，规格表支持的负载率为: {supported}")


def calc_active_power(apparent_power_kva: float, power_factor: float) -> float:
    """根据视在功率（kVA）和功率因数（PF）计算有功功率（kW）。

    公式: P (kW) = S (kVA) * PF
    """
    _validate_non_negative(apparent_power_kva, "apparent_power_kva")
    _validate_power_factor(power_factor, allow_zero=True)
    return float(apparent_power_kva * power_factor)


def calc_apparent_power(active_power_kw: float, power_factor: float) -> float:
    """根据有功功率（kW）和功率因数（PF）计算视在功率（kVA）。

    公式: S (kVA) = P (kW) / PF
    """
    _validate_non_negative(active_power_kw, "active_power_kw")
    _validate_power_factor(power_factor, allow_zero=False)
    return float(active_power_kw / power_factor)


def calc_power_factor(active_power_kw: float, apparent_power_kva: float) -> float:
    """根据有功功率（kW）和视在功率（kVA）计算功率因数（PF）。

    公式: PF = P (kW) / S (kVA)
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
    """
    _validate_non_negative(apparent_power_kva, "apparent_power_kva")
    _validate_non_negative(active_power_kw, "active_power_kw")
    if active_power_kw > apparent_power_kva:
        raise ValueError(
            f"有功功率 ({active_power_kw} kW) 不能大于视在功率 ({apparent_power_kva} kVA)"
        )
    return float(math.sqrt(apparent_power_kva**2 - active_power_kw**2))


def calc_power_loss(active_power_kw: float, efficiency: float) -> float:
    """计算 UPS 损耗有功功率（单位：kW）。

    公式: P_loss = P_out * (1 / efficiency - 1)

    Args:
        active_power_kw: 输出有功功率 P_out（单位：kW），需 >= 0。
        efficiency: 系统运行效率（无量纲），取值范围 (0.0, 1.0]。

    Returns:
        损耗有功功率 P_loss（单位：kW）。
    """
    _validate_non_negative(active_power_kw, "active_power_kw")
    _validate_efficiency(efficiency)
    return float(active_power_kw * (1.0 / efficiency - 1.0))


def calc_heat_dissipation(power_loss_kw: float) -> float:
    """将 UPS 有功功率损耗（kW）转换为数据中心空调制冷负荷（单位：BTU/hr）。

    公式: Q_heat (BTU/hr) = P_loss (kW) * 3412.142

    Args:
        power_loss_kw: 损耗有功功率 P_loss（单位：kW），需 >= 0。

    Returns:
        热负荷 / 发热量（单位：BTU/hr）。
    """
    _validate_non_negative(power_loss_kw, "power_loss_kw")
    return float(power_loss_kw * BTU_PER_KW_HR)
