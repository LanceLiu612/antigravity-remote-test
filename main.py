"""数据中心 UPS 电力计算命令行工具。

支持通过终端参数（--kva、--kw、--pf 中的任意两个）计算并输出完整的电力换算结果：
- 视在功率 S (kVA)
- 有功功率 P (kW)
- 无功功率 Q (kVAR)
- 功率因数 PF
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from ups_calc import (
    calc_active_power,
    calc_apparent_power,
    calc_power_factor,
    calc_reactive_power,
)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="数据中心 UPS 电力换算命令行工具（请提供 --kva、--kw、--pf 中的任意两个参数）",
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
    return parser


def compute_all_metrics(
    kva: float | None = None,
    kw: float | None = None,
    pf: float | None = None,
) -> dict[str, float]:
    """根据任意两个已知参数计算完整的 UPS 电力指标。

    Args:
        kva: 视在功率（kVA）
        kw: 有功功率（kW）
        pf: 功率因数（PF）

    Returns:
        包含 kva、kw、kvar、pf 的字典。

    Raises:
        ValueError: 当提供的参数数量不为 2，或数值不满足物理约束时抛出。
    """
    provided_count = sum(x is not None for x in (kva, kw, pf))
    if provided_count != 2:
        raise ValueError("必须且只能提供 --kva、--kw、--pf 中的任意两个参数")

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

    resolved_kvar = calc_reactive_power(resolved_kva, resolved_kw)
    return {
        "kva": resolved_kva,
        "kw": resolved_kw,
        "kvar": resolved_kvar,
        "pf": resolved_pf,
    }


def format_report(metrics: dict[str, float]) -> str:
    """将完整电力换算结果格式化为终端可读文本。"""
    lines = [
        "=== 数据中心 UPS 电力换算结果 ===",
        f"视在功率 (S)  : {metrics['kva']:.2f} kVA",
        f"有功功率 (P)  : {metrics['kw']:.2f} kW",
        f"无功功率 (Q)  : {metrics['kvar']:.2f} kVAR",
        f"功率因数 (PF) : {metrics['pf']:.4f}",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """命令行主入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metrics = compute_all_metrics(kva=args.kva, kw=args.kw, pf=args.pf)
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print(format_report(metrics))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
