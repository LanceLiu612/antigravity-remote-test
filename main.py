"""数据中心 UPS 电力与热损耗计算命令行工具。

支持通过终端参数：
- --kva、--kw、--pf 中的任意两个（或直接传入 --load-ratio 按额定 200kVA/200kW 推算）
- 可选传入 --load-ratio（如 0.25、0.5、0.75、1.0）或 --efficiency
输出完整的电力换算结果以及有功损耗（kW）与发热量（BTU/hr）。
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from ups_calc import (
    RATED_CAPACITY_KVA,
    RATED_POWER_FACTOR,
    calc_active_power,
    calc_apparent_power,
    calc_heat_dissipation,
    calc_power_factor,
    calc_power_loss,
    calc_reactive_power,
    get_spec_efficiency,
)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="数据中心 UPS 电力与热损耗换算命令行工具",
    )
    parser.add_argument(
        "--kva",
        type=float,
        default=None,
        help="视在功率（单位：kVA）",
    )
    parser.add_argument(
        "--kw",
        type=float,
        default=None,
        help="有功功率（单位：kW）",
    )
    parser.add_argument(
        "--pf",
        type=float,
        default=None,
        help="功率因数（取值范围：0.0 ~ 1.0）",
    )
    parser.add_argument(
        "--load-ratio",
        type=float,
        default=None,
        help="UPS 负载率（如 0.25, 0.5, 0.75, 1.0），用于匹配规格效率及默认额定容量负载",
    )
    parser.add_argument(
        "--efficiency",
        type=float,
        default=None,
        help="UPS 系统运行效率（取值范围：(0.0, 1.0]，如 0.96）",
    )
    return parser


def compute_all_metrics(
    kva: float | None = None,
    kw: float | None = None,
    pf: float | None = None,
    load_ratio: float | None = None,
    efficiency: float | None = None,
) -> dict[str, float]:
    """根据输入参数计算完整的 UPS 电力指标及可选的热损耗指标。"""
    provided_power_count = sum(x is not None for x in (kva, kw, pf))

    # 若未显式提供两个电力参数，但提供了 --load-ratio，则基于规格书额定容量 (200 kVA, PF=1.0) 推算
    if provided_power_count == 0 and load_ratio is not None:
        spec_eff = get_spec_efficiency(load_ratio)
        resolved_kva = RATED_CAPACITY_KVA * float(load_ratio)
        resolved_pf = RATED_POWER_FACTOR
        resolved_kw = calc_active_power(resolved_kva, resolved_pf)
        resolved_efficiency = float(efficiency) if efficiency is not None else spec_eff
    elif provided_power_count == 2:
        if kva is not None and pf is not None:
            resolved_kva = float(kva)
            resolved_pf = float(pf)
            resolved_kw = calc_active_power(resolved_kva, resolved_pf)
        elif kw is not None and pf is not None:
            resolved_kw = float(kw)
            resolved_pf = float(pf)
            resolved_kva = calc_apparent_power(resolved_kw, resolved_pf)
        else:
            assert kva is not None and kw is not None
            resolved_kva = float(kva)
            resolved_kw = float(kw)
            resolved_pf = calc_power_factor(resolved_kw, resolved_kva)

        if efficiency is not None and load_ratio is not None:
            raise ValueError("已指定功率参数时，--load-ratio 与 --efficiency 不能同时提供")
        if efficiency is not None:
            resolved_efficiency = float(efficiency)
        elif load_ratio is not None:
            resolved_efficiency = get_spec_efficiency(load_ratio)
        else:
            resolved_efficiency = None
    else:
        raise ValueError(
            "必须且只能提供 --kva、--kw、--pf 中的任意两个参数（或仅提供 --load-ratio 使用额定容量计算）"
        )

    resolved_kvar = calc_reactive_power(resolved_kva, resolved_kw)
    result: dict[str, float] = {
        "kva": resolved_kva,
        "kw": resolved_kw,
        "kvar": resolved_kvar,
        "pf": resolved_pf,
    }

    if resolved_efficiency is not None:
        power_loss_kw = calc_power_loss(resolved_kw, resolved_efficiency)
        heat_btu_hr = calc_heat_dissipation(power_loss_kw)
        result["efficiency"] = resolved_efficiency
        result["power_loss_kw"] = power_loss_kw
        result["heat_btu_hr"] = heat_btu_hr

    return result


def format_report(metrics: dict[str, float]) -> str:
    """将完整电力与热损耗换算结果格式化为终端可读文本。"""
    lines = [
        "=== 数据中心 UPS 电力换算结果 ===",
        f"视在功率 (S)  : {metrics['kva']:.2f} kVA",
        f"有功功率 (P)  : {metrics['kw']:.2f} kW",
        f"无功功率 (Q)  : {metrics['kvar']:.2f} kVAR",
        f"功率因数 (PF) : {metrics['pf']:.4f}",
    ]
    if "power_loss_kw" in metrics and "heat_btu_hr" in metrics:
        lines.extend(
            [
                f"系统效率 (η)  : {metrics['efficiency'] * 100:.2f}%",
                f"有功损耗 (Pl) : {metrics['power_loss_kw']:.4f} kW",
                f"发热量 (Heat) : {metrics['heat_btu_hr']:.2f} BTU/hr",
            ]
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """命令行主入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metrics = compute_all_metrics(
            kva=args.kva,
            kw=args.kw,
            pf=args.pf,
            load_ratio=args.load_ratio,
            efficiency=args.efficiency,
        )
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print(format_report(metrics))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
