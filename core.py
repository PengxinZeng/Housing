"""
核心计算模块：买房和租房的逐年成本投影。
所有函数均为无副作用的纯计算函数。
"""

import pandas as pd


def project_buy_cost(
    purchase_price: float,
    annual_appreciation: float,
    annual_maintenance_rate: float,
    annual_property_tax_rate: float,
    years: int,
    opportunity_cost_rate: float,
    buy_discount_rate: float = 0.08,
) -> tuple[pd.DataFrame, float]:
    """计算买房持有期间每年成本、价值和总成本。

    Returns:
        (逐年明细 DataFrame, 总成本)

    总成本定义：
        purchase_price + 累积持有成本 - 期末房产价值
    """
    records = []
    home_value = purchase_price * (1 - buy_discount_rate)
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

        records.append(
            {
                "year": year,
                "home_value": home_value,
                "maintenance": maintenance,
                "property_tax": prop_tax,
                "opportunity_cost": opp_cost,
                "cumulative_maintenance": cumulative_maintenance,
                "cumulative_property_tax": cumulative_tax,
                "cumulative_opportunity_cost": cumulative_opp_cost,
            }
        )

    total_cost = (
        purchase_price
        + cumulative_maintenance
        + cumulative_tax
        + cumulative_opp_cost
        - home_value
    )
    return pd.DataFrame(records), total_cost


def project_rent_cost(
    initial_rent: float,
    annual_rent_growth: float,
    years: int,
    investable_capital: float,
    invest_return: float,
) -> tuple[pd.DataFrame, float, float]:
    """计算租房期间每年开销、投资收益和总成本。

    投资组合每年增值后扣除当年租金：
        portfolio_t = portfolio_{t-1} * (1 + invest_return) - rent_t

    Returns:
        (逐年明细 DataFrame, 总成本, 期末投资组合价值)

    总成本定义：
        investable_capital - portfolio_years  （净资本减少量）
    """
    records = []
    rent = initial_rent
    cumulative_rent = 0.0
    portfolio = investable_capital

    for year in range(1, int(years) + 1):
        rent *= 1 + annual_rent_growth
        portfolio = portfolio * (1 + invest_return) - rent
        cumulative_rent += rent

        records.append(
            {
                "year": year,
                "rent": rent,
                "portfolio_value": portfolio,
                "cumulative_rent": cumulative_rent,
            }
        )

    total_cost = investable_capital - portfolio
    return pd.DataFrame(records), total_cost, portfolio


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
) -> tuple[float, float]:
    """计算给定参数下买房和租房的总成本。

    Returns:
        (buy_total_cost, rent_total_cost)
    """
    _, buy_total_cost = project_buy_cost(
        purchase_price,
        annual_appreciation,
        annual_maintenance_rate,
        annual_property_tax_rate,
        years,
        opportunity_cost_rate,
        buy_discount_rate,
    )
    _, rent_total_cost, _ = project_rent_cost(
        initial_rent,
        annual_rent_growth,
        years,
        investable_capital=purchase_price,
        invest_return=invest_return,
    )
    return buy_total_cost, rent_total_cost
