import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def project_buy_cost(
    purchase_price: float,
    annual_appreciation: float,
    annual_maintenance_rate: float,
    annual_property_tax_rate: float,
    years: int,
    opportunity_cost_rate: float,
    buy_discount_rate: float = 0.08,
):
    """计算买房持有期间每年成本、价值和总成本。"""
    records = []
    home_value = purchase_price * (1 - buy_discount_rate)  # 买入时扣除损耗
    cumulative_maintenance = 0.0
    cumulative_tax = 0.0
    cumulative_opp_cost = 0.0

    for year in range(1, int(years) + 1):
        home_value *= 1 + annual_appreciation
        maintenance = home_value * annual_maintenance_rate
        prop_tax = home_value * annual_property_tax_rate
        opp_cost = home_value * opportunity_cost_rate

        cumulative_maintenance += maintenance
        cumulative_tax += prop_tax
        cumulative_opp_cost += opp_cost

        records.append({
            "year": year,
            "home_value": home_value,
            "maintenance": maintenance,
            "property_tax": prop_tax,
            "opportunity_cost": opp_cost,
            "cumulative_maintenance": cumulative_maintenance,
            "cumulative_property_tax": cumulative_tax,
            "cumulative_opportunity_cost": cumulative_opp_cost,
        })

    total_cost = purchase_price + cumulative_maintenance + cumulative_tax + cumulative_opp_cost - home_value
    return pd.DataFrame(records), total_cost


def compute_costs(
    purchase_price: float,
    initial_rent: float,
    years: int,
    annual_appreciation: float,
    annual_maintenance_rate: float,
    annual_property_tax_rate: float,
    annual_rent_growth: float,
    opportunity_cost_rate: float,
    invest_return: float,
    buy_discount_rate: float = 0.08,
):
    df_buy, buy_total_cost = project_buy_cost(
        purchase_price,
        annual_appreciation,
        annual_maintenance_rate,
        annual_property_tax_rate,
        years,
        opportunity_cost_rate,
        buy_discount_rate,
    )
    df_rent, rent_total_cost, rent_portfolio = project_rent_cost(
        initial_rent,
        annual_rent_growth,
        years,
        investable_capital=purchase_price,
        invest_return=invest_return,
    )
    return buy_total_cost, rent_total_cost


def sensitivity_analysis(
    base_params: dict,
    param_ranges: dict,
    output_dir: str = "output",
):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    for param, values in param_ranges.items():
        buy_costs = []
        rent_costs = []

        for value in values:
            params = base_params.copy()
            params[param] = value
            buy_cost, rent_cost = compute_costs(**params)
            buy_costs.append(buy_cost)
            rent_costs.append(rent_cost)

        plt.figure(figsize=(8, 5))
        plt.plot(values, buy_costs, marker="o", label="buy_total_cost")
        plt.plot(values, rent_costs, marker="o", label="rent_total_cost")
        plt.xlabel(param)
        plt.ylabel("total_cost")
        plt.title(f"Sensitivity: {param}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        png_file = path / f"sensitivity_{param}.png"
        plt.savefig(png_file)
        plt.close()

    return [path / f"sensitivity_{p}.png" for p in param_ranges.keys()]


def project_rent_cost(
    initial_rent: float,
    annual_rent_growth: float,
    years: int,
    investable_capital: float,
    invest_return: float,
):
    """计算租房期间每年开销、投资收益和总成本。"""
    records = []
    rent = initial_rent
    cumulative_rent = 0.0
    portfolio = investable_capital

    for year in range(1, int(years) + 1):
        rent *= 1 + annual_rent_growth
        portfolio = portfolio * (1 + invest_return) - rent
        cumulative_rent += rent

        records.append({
            "year": year,
            "rent": rent,
            "portfolio_value": portfolio,
            "cumulative_rent": cumulative_rent,
        })

    total_cost = investable_capital - portfolio  # 总开销=本金-可投资金额（净资本减少）
    return pd.DataFrame(records), total_cost, portfolio


def generate_comparison_report(
    purchase_price: float,
    initial_rent: float,
    years: int,
    annual_appreciation: float,
    annual_maintenance_rate: float,
    annual_property_tax_rate: float,
    annual_rent_growth: float,
    opportunity_cost_rate: float,
    invest_return: float,
    buy_discount_rate: float = 0.08,
    output_dir: str = "output",
    filename: str = "housing_rent_comparison.xlsx",
):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    df_buy, buy_total_cost = project_buy_cost(
        purchase_price,
        annual_appreciation,
        annual_maintenance_rate,
        annual_property_tax_rate,
        years,
        opportunity_cost_rate,
        buy_discount_rate,
    )

    # 租金和房价“同波动”时，rent growth == apprec
    df_rent, rent_total_cost, rent_portfolio = project_rent_cost(
        initial_rent,
        annual_rent_growth,
        years,
        investable_capital=purchase_price,
        invest_return=invest_return,
    )

    summary = pd.DataFrame(
        [
            {
                "scenario": "buy",
                "purchase_price": purchase_price,
                "years": years,
                "total_cost": buy_total_cost,
                "end_value_or_portfolio": df_buy.loc[years - 1, "home_value"],
            },
            {
                "scenario": "rent",
                "initial_rent": initial_rent,
                "years": years,
                "total_cost": rent_total_cost,
                "end_value_or_portfolio": rent_portfolio,
            },
        ]
    )

    summary_file = path / "housing_rent_summary.csv"
    buy_file = path / "housing_rent_buy_details.csv"
    rent_file = path / "housing_rent_rent_details.csv"

    summary.to_csv(summary_file, index=False)
    df_buy.to_csv(buy_file, index=False)
    df_rent.to_csv(rent_file, index=False)

    return {
        "summary_file": str(summary_file),
        "buy_file": str(buy_file),
        "rent_file": str(rent_file),
        "summary": summary,
        "buy_total_cost": buy_total_cost,
        "rent_total_cost": rent_total_cost,
    }


if __name__ == "__main__":
    annual_appreciation = 0.02
    base_params = {
        "purchase_price": 3_000_000,
        "initial_rent": 30_000,
        "years": 40,
        "annual_appreciation": annual_appreciation,
        "annual_maintenance_rate": 0.0175,
        "annual_property_tax_rate": 0.00,
        "annual_rent_growth": annual_appreciation,
        "opportunity_cost_rate": 0.00,
        "invest_return": 0.04,
        "buy_discount_rate": 0.20,
    }
    # base_params = {
    #     "purchase_price": 3_000_000,
    #     "initial_rent": 50_000,
    #     "years": 30,
    #     "annual_appreciation": -0.01,
    #     "annual_maintenance_rate": 0.0175,
    #     "annual_property_tax_rate": 0.00,
    #     "annual_rent_growth": -0.01,
    #     "opportunity_cost_rate": 0.00,
    #     "invest_return": 0.02,
    #     "buy_discount_rate": 0.20,
    # }
    result = generate_comparison_report(**base_params)

    print("生成完成：", result["summary_file"], result["buy_file"], result["rent_file"])
    print(result["summary"])

    param_ranges = {
        "purchase_price": np.linspace(1_000_000, 100_000_000, 10),
        "initial_rent": np.linspace(20_000, 100_000, 9),
        "years": np.linspace(0, 120, 51),
        "annual_appreciation": np.linspace(-0.10, 0.10, 21),
        "annual_maintenance_rate": np.linspace(0.01, 0.03, 13),
        "annual_rent_growth": np.linspace(0.0, 0.06, 13),
        "invest_return": np.linspace(0.0, 0.08, 13),
        "buy_discount_rate": np.linspace(0.0, 0.50, 26),
    }

    png_files = sensitivity_analysis(base_params, param_ranges, output_dir="output")
    print("敏感性分析图已保存：", png_files)
