"""ups_calc 与 main 模块的 pytest 单元测试用例。"""

import math
import pytest

from main import compute_all_metrics, main
from ups_calc import (
    BTU_PER_KW_HR,
    RATED_ACTIVE_POWER_KW,
    RATED_CAPACITY_KVA,
    RATED_POWER_FACTOR,
    SPEC_EFFICIENCY_BY_LOAD_RATIO,
    calc_active_power,
    calc_apparent_power,
    calc_heat_dissipation,
    calc_power_factor,
    calc_power_loss,
    calc_reactive_power,
    get_spec_efficiency,
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


class TestSpecThermalAndEfficiency:
    """基于《UPS_Technical_Spec》(KSTAR HPM3300E-200kVA) 规格数据的热损耗与效率测试。"""

    def test_rated_constants(self) -> None:
        assert RATED_CAPACITY_KVA == 200.0
        assert RATED_ACTIVE_POWER_KW == 200.0
        assert RATED_POWER_FACTOR == 1.0
        assert BTU_PER_KW_HR == 3412.142
        assert SPEC_EFFICIENCY_BY_LOAD_RATIO == {
            0.25: 0.950,
            0.50: 0.965,
            0.75: 0.962,
            1.00: 0.960,
        }

    @pytest.mark.parametrize(
        "load_ratio, expected_eff, expected_kw, expected_loss_kw, expected_btu_hr",
        [
            # 25% 负载: 50 kW, eff=95.0%, P_loss = 50 * (1/0.95 - 1) = 2.631578947... kW
            (0.25, 0.950, 50.0, 50.0 * (1.0 / 0.950 - 1.0), 50.0 * (1.0 / 0.950 - 1.0) * 3412.142),
            # 50% 负载: 100 kW, eff=96.5%, P_loss = 100 * (1/0.965 - 1) = 3.626943005... kW
            (0.50, 0.965, 100.0, 100.0 * (1.0 / 0.965 - 1.0), 100.0 * (1.0 / 0.965 - 1.0) * 3412.142),
            # 75% 负载: 150 kW, eff=96.2%, P_loss = 150 * (1/0.962 - 1) = 5.925155925... kW
            (0.75, 0.962, 150.0, 150.0 * (1.0 / 0.962 - 1.0), 150.0 * (1.0 / 0.962 - 1.0) * 3412.142),
            # 100% 负载: 200 kW, eff=96.0%, P_loss = 200 * (1/0.960 - 1) = 8.333333333... kW
            (1.00, 0.960, 200.0, 200.0 * (1.0 / 0.960 - 1.0), 200.0 * (1.0 / 0.960 - 1.0) * 3412.142),
        ],
    )
    def test_spec_load_points(
        self,
        load_ratio: float,
        expected_eff: float,
        expected_kw: float,
        expected_loss_kw: float,
        expected_btu_hr: float,
    ) -> None:
        eff = get_spec_efficiency(load_ratio)
        assert math.isclose(eff, expected_eff, rel_tol=1e-9)

        active_kw = calc_active_power(RATED_CAPACITY_KVA * load_ratio, RATED_POWER_FACTOR)
        assert math.isclose(active_kw, expected_kw, rel_tol=1e-9)

        loss_kw = calc_power_loss(active_kw, eff)
        assert math.isclose(loss_kw, expected_loss_kw, rel_tol=1e-9)

        heat_btu = calc_heat_dissipation(loss_kw)
        assert math.isclose(heat_btu, expected_btu_hr, rel_tol=1e-9)

    def test_invalid_efficiency_and_load_ratio(self) -> None:
        with pytest.raises(ValueError):
            get_spec_efficiency(0.60)
        with pytest.raises(ValueError):
            calc_power_loss(100.0, 0.0)
        with pytest.raises(ValueError):
            calc_power_loss(100.0, 1.05)
        with pytest.raises(ValueError):
            calc_power_loss(-10.0, 0.96)
        with pytest.raises(ValueError):
            calc_heat_dissipation(-1.0)


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

    def test_cli_with_load_ratio_only(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--load-ratio", "0.5"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "视在功率 (S)  : 100.00 kVA" in captured.out
        assert "有功功率 (P)  : 100.00 kW" in captured.out
        assert "系统效率 (η)  : 96.50%" in captured.out
        assert "有功损耗 (Pl) : 3.6269 kW" in captured.out
        assert "发热量 (Heat) : 12375.64 BTU/hr" in captured.out

    def test_cli_with_power_and_load_ratio(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--kva", "200", "--pf", "1.0", "--load-ratio", "1.0"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "有功功率 (P)  : 200.00 kW" in captured.out
        assert "系统效率 (η)  : 96.00%" in captured.out
        assert "有功损耗 (Pl) : 8.3333 kW" in captured.out
        assert "发热量 (Heat) : 28434.52 BTU/hr" in captured.out

    def test_cli_with_power_and_efficiency(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--kw", "150", "--pf", "1.0", "--efficiency", "0.962"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "系统效率 (η)  : 96.20%" in captured.out
        assert "有功损耗 (Pl) : 5.9252 kW" in captured.out
        assert "发热量 (Heat) : 20217.47 BTU/hr" in captured.out

    @pytest.mark.parametrize(
        "argv",
        [
            [],
            ["--kva", "500"],
            ["--kva", "500", "--kw", "450", "--pf", "0.9"],
            ["--kva", "500", "--pf", "1.2"],
            ["--kva", "400", "--kw", "500"],
            ["--kva", "200", "--pf", "1.0", "--load-ratio", "0.5", "--efficiency", "0.965"],
            ["--load-ratio", "0.33"],
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
