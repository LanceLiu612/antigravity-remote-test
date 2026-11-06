"""ups_calc 与 main 模块的 pytest 单元测试用例。"""

import math
import pytest

from main import compute_all_metrics, main
from ups_calc import (
    calc_active_power,
    calc_apparent_power,
    calc_power_factor,
    calc_reactive_power,
)


class TestCalcActivePower:
    """测试有功功率（kW）计算函数。"""

    @pytest.mark.parametrize(
        "kva, pf, expected_kw",
        [
            (500.0, 0.9, 450.0),
            (400.0, 0.8, 320.0),
            (600.0, 1.0, 600.0),
            (500.0, 0.0, 0.0),
            (0.0, 0.9, 0.0),
        ],
    )
    def test_valid_inputs(self, kva: float, pf: float, expected_kw: float) -> None:
        assert math.isclose(calc_active_power(kva, pf), expected_kw, rel_tol=1e-9)

    @pytest.mark.parametrize(
        "kva, pf",
        [
            (-100.0, 0.9),
            (500.0, -0.1),
            (500.0, 1.05),
            (float("nan"), 0.9),
            (500.0, float("inf")),
        ],
    )
    def test_invalid_values(self, kva: float, pf: float) -> None:
        with pytest.raises(ValueError):
            calc_active_power(kva, pf)

    def test_invalid_types(self) -> None:
        with pytest.raises(TypeError):
            calc_active_power("500", 0.9)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            calc_active_power(True, 0.9)  # type: ignore[arg-type]


class TestCalcApparentPower:
    """测试视在功率（kVA）计算函数。"""

    @pytest.mark.parametrize(
        "kw, pf, expected_kva",
        [
            (450.0, 0.9, 500.0),
            (320.0, 0.8, 400.0),
            (600.0, 1.0, 600.0),
            (0.0, 0.9, 0.0),
        ],
    )
    def test_valid_inputs(self, kw: float, pf: float, expected_kva: float) -> None:
        assert math.isclose(calc_apparent_power(kw, pf), expected_kva, rel_tol=1e-9)

    @pytest.mark.parametrize(
        "kw, pf",
        [
            (450.0, 0.0),
            (-10.0, 0.9),
            (450.0, -0.5),
            (450.0, 1.2),
        ],
    )
    def test_invalid_values(self, kw: float, pf: float) -> None:
        with pytest.raises(ValueError):
            calc_apparent_power(kw, pf)


class TestCalcPowerFactor:
    """测试功率因数（PF）计算函数。"""

    @pytest.mark.parametrize(
        "kw, kva, expected_pf",
        [
            (450.0, 500.0, 0.9),
            (320.0, 400.0, 0.8),
            (600.0, 600.0, 1.0),
            (0.0, 500.0, 0.0),
        ],
    )
    def test_valid_inputs(self, kw: float, kva: float, expected_pf: float) -> None:
        assert math.isclose(calc_power_factor(kw, kva), expected_pf, rel_tol=1e-9)

    @pytest.mark.parametrize(
        "kw, kva",
        [
            (450.0, 0.0),
            (550.0, 500.0),
            (-10.0, 500.0),
            (450.0, -500.0),
        ],
    )
    def test_invalid_values(self, kw: float, kva: float) -> None:
        with pytest.raises(ValueError):
            calc_power_factor(kw, kva)


class TestCalcReactivePower:
    """测试无功功率（kVAR）计算函数。"""

    def test_valid_inputs(self) -> None:
        assert math.isclose(calc_reactive_power(500.0, 400.0), 300.0, rel_tol=1e-9)
        assert math.isclose(calc_reactive_power(500.0, 500.0), 0.0, rel_tol=1e-9)

    def test_invalid_values(self) -> None:
        with pytest.raises(ValueError):
            calc_reactive_power(400.0, 500.0)
        with pytest.raises(ValueError):
            calc_reactive_power(-500.0, 400.0)


class TestMainCLI:
    """测试 main.py 命令行工具及完整换算逻辑。"""

    def test_cli_kva_and_pf(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--kva", "500", "--pf", "0.9"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "视在功率 (S)  : 500.00 kVA" in captured.out
        assert "有功功率 (P)  : 450.00 kW" in captured.out
        assert "无功功率 (Q)  : 217.94 kVAR" in captured.out
        assert "功率因数 (PF) : 0.9000" in captured.out

    def test_cli_kw_and_pf(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--kw", "320", "--pf", "0.8"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "视在功率 (S)  : 400.00 kVA" in captured.out
        assert "有功功率 (P)  : 320.00 kW" in captured.out
        assert "无功功率 (Q)  : 240.00 kVAR" in captured.out
        assert "功率因数 (PF) : 0.8000" in captured.out

    def test_cli_kva_and_kw(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--kva", "500", "--kw", "400"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "视在功率 (S)  : 500.00 kVA" in captured.out
        assert "有功功率 (P)  : 400.00 kW" in captured.out
        assert "无功功率 (Q)  : 300.00 kVAR" in captured.out
        assert "功率因数 (PF) : 0.8000" in captured.out

    @pytest.mark.parametrize(
        "argv",
        [
            [],
            ["--kva", "500"],
            ["--kva", "500", "--kw", "450", "--pf", "0.9"],
            ["--kva", "500", "--pf", "1.2"],
            ["--kva", "400", "--kw", "500"],
        ],
    )
    def test_cli_invalid_args(
        self, argv: list[str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(argv)
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "错误:" in captured.err

    def test_compute_all_metrics_direct(self) -> None:
        metrics = compute_all_metrics(kva=500.0, pf=0.8)
        assert math.isclose(metrics["kva"], 500.0)
        assert math.isclose(metrics["kw"], 400.0)
        assert math.isclose(metrics["kvar"], 300.0)
        assert math.isclose(metrics["pf"], 0.8)
