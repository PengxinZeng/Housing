"""
入口文件：配置参数、运行敏感性分析和临界投资回报率分析。

参数说明
--------
base_params 使用租售比形式：
  - rent_price_ratio: 年租金 / 房价（如 0.01 = 1%）
  - annual_rent_growth 不再单独配置，始终等于 annual_appreciation（联动）
"""

import numpy as np

from analysis import (
    critical_invest_return_analysis,
    resolve_params,
    sensitivity_analysis,
)
from core import project_buy_cost, project_rent_cost
from visualization import plot_critical_invest_return, plot_sensitivity

OUTPUT_DIR = "output"
CRITICAL_YEARS = 300  # 临界投资回报率分析的时间跨度


def main():
    # ------------------------------------------------------------------
    # 基准参数（租售比形式）
    # ------------------------------------------------------------------
    base_params = {
        "purchase_price": 3_000_000,
        "rent_price_ratio": 0.01,       # 年租售比 1%（即年租金 = 房价 × 1%）
        "years": 70,
        "annual_appreciation": 0.03,    # annual_rent_growth 自动等于此值
        "annual_maintenance_rate": 0.0175,
        "annual_property_tax_rate": 0.00,
        "opportunity_cost_rate": 0.00,
        "invest_return": 0.05,
        "buy_discount_rate": 0.20,
    }

    # ------------------------------------------------------------------
    # 生成对比报告（CSV）
    # ------------------------------------------------------------------
    from pathlib import Path
    import pandas as pd
    from core import compute_costs

    path = Path(OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)

    resolved = resolve_params(base_params)

    df_buy, buy_total_cost = project_buy_cost(
        resolved["purchase_price"],
        resolved["annual_appreciation"],
        resolved["annual_maintenance_rate"],
        resolved["annual_property_tax_rate"],
        resolved["years"],
        resolved["opportunity_cost_rate"],
        resolved["buy_discount_rate"],
    )
    df_rent, rent_total_cost, rent_portfolio = project_rent_cost(
        resolved["initial_rent"],
        resolved["annual_rent_growth"],
        resolved["years"],
        investable_capital=resolved["purchase_price"],
        invest_return=resolved["invest_return"],
    )

    summary = pd.DataFrame(
        [
            {
                "scenario": "buy",
                "purchase_price": resolved["purchase_price"],
                "years": resolved["years"],
                "total_cost": buy_total_cost,
                "end_value_or_portfolio": df_buy.loc[resolved["years"] - 1, "home_value"],
            },
            {
                "scenario": "rent",
                "initial_rent": resolved["initial_rent"],
                "rent_price_ratio": base_params["rent_price_ratio"],
                "years": resolved["years"],
                "total_cost": rent_total_cost,
                "end_value_or_portfolio": rent_portfolio,
            },
        ]
    )

    summary.to_csv(path / "housing_rent_summary.csv", index=False)
    df_buy.to_csv(path / "housing_rent_buy_details.csv", index=False)
    df_rent.to_csv(path / "housing_rent_rent_details.csv", index=False)

    print("=== 对比摘要 ===")
    print(summary.to_string(index=False))

    # ------------------------------------------------------------------
    # 敏感性分析
    # ------------------------------------------------------------------
    sensitivity_param_ranges = {
        "purchase_price": np.linspace(1_000_000, 100_000_000, 10),
        "rent_price_ratio": np.linspace(0.005, 0.03, 11),   # 0.5% ~ 3%
        "years": np.linspace(1, 300, 51),
        "annual_appreciation": np.linspace(-0.10, 0.10, 21),  # rent_growth 自动联动
        "annual_maintenance_rate": np.linspace(0.01, 0.03, 13),
        "invest_return": np.linspace(0.0, 0.08, 13),
        "buy_discount_rate": np.linspace(0.0, 0.50, 26),
    }

    sensitivity_results = sensitivity_analysis(base_params, sensitivity_param_ranges)
    sensitivity_pngs = plot_sensitivity(sensitivity_results, output_dir=OUTPUT_DIR)
    print(f"\n敏感性分析图已保存（{len(sensitivity_pngs)} 张）：")
    for p in sensitivity_pngs:
        print(f"  {p}")

    # ------------------------------------------------------------------
    # 临界投资回报率分析（CRITICAL_YEARS 年）
    # ------------------------------------------------------------------
    critical_param_ranges = {
        "annual_appreciation": np.linspace(-0.02, 0.06, 17),  # rent_growth 自动联动
        "rent_price_ratio": np.linspace(0.005, 0.025, 14),    # 0.5% ~ 2.5%
        "annual_maintenance_rate": np.linspace(0.005, 0.04, 15),
        "buy_discount_rate": np.linspace(0.0, 0.50, 26),
        "purchase_price": np.linspace(1_000_000, 10_000_000, 10),
    }

    critical_results = critical_invest_return_analysis(
        base_params, critical_param_ranges, years=CRITICAL_YEARS
    )
    critical_pngs = plot_critical_invest_return(
        critical_results, output_dir=OUTPUT_DIR, years=CRITICAL_YEARS
    )

    print(f"\n临界投资回报率分析图已保存（{len(critical_pngs)} 张）：")
    for p in critical_pngs:
        print(f"  {p}")

    # 打印汇总表
    print(f"\n=== 临界投资回报率摘要（{CRITICAL_YEARS} 年）===")
    for param, df in critical_results.items():
        valid = df.dropna(subset=["critical_invest_return"])
        if valid.empty:
            continue
        lo = valid["critical_invest_return"].min() * 100
        hi = valid["critical_invest_return"].max() * 100
        print(f"  {param:30s}: {lo:.2f}% ~ {hi:.2f}%")


if __name__ == "__main__":
    main()
