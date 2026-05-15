"""
分析模块：敏感性分析和临界投资回报率分析。

参数约定
--------
base_params 可以包含以下两种形式之一：
  - 传统形式：显式 initial_rent + annual_rent_growth
  - 租售比形式：rent_price_ratio（年租金/房价），此时：
      initial_rent      = purchase_price * rent_price_ratio
      annual_rent_growth = annual_appreciation  （租金与房价同步）

调用 resolve_params() 可将两种形式统一转换为 compute_costs 所需的参数。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from core import compute_costs


# ---------------------------------------------------------------------------
# 参数归一化
# ---------------------------------------------------------------------------

def resolve_params(params: dict) -> dict:
    """将含 rent_price_ratio 的参数字典归一化为 compute_costs 所需的完整参数。

    规则：
      - 若含 rent_price_ratio，则派生 initial_rent = purchase_price * rent_price_ratio
      - annual_rent_growth 始终强制等于 annual_appreciation（租金与房价同步涨跌）

    Args:
        params: 原始参数字典，不会被修改

    Returns:
        可直接传入 compute_costs 的参数字典
    """
    p = params.copy()
    if "rent_price_ratio" in p:
        p["initial_rent"] = p["purchase_price"] * p.pop("rent_price_ratio")
    # 租金增长率始终与房价增长率联动
    p["annual_rent_growth"] = p["annual_appreciation"]
    return p


# ---------------------------------------------------------------------------
# 敏感性分析
# ---------------------------------------------------------------------------

def sensitivity_analysis(
    base_params: dict,
    param_ranges: dict[str, np.ndarray],
) -> dict[str, tuple[list, list, list]]:
    """对每个参数做一维敏感性扫描。

    Args:
        base_params:  基准参数字典（支持 rent_price_ratio 形式）
        param_ranges: {参数名: 取值数组}

    Returns:
        {参数名: (values, buy_costs, rent_costs)}
    """
    results = {}
    for param, values in param_ranges.items():
        buy_costs, rent_costs = [], []
        for value in values:
            params = base_params.copy()
            params[param] = value
            resolved = resolve_params(params)
            buy_cost, rent_cost = compute_costs(**resolved)
            buy_costs.append(buy_cost)
            rent_costs.append(rent_cost)
        results[param] = (list(values), buy_costs, rent_costs)
    return results


# ---------------------------------------------------------------------------
# 临界投资回报率分析
# ---------------------------------------------------------------------------

def find_critical_invest_return(
    base_params: dict,
    search_low: float = 0.0,
    search_high: float = 0.20,
    tol: float = 1e-7,
) -> float | None:
    """用二分法求使 rent_total_cost == buy_total_cost 的 invest_return。

    在 [search_low, search_high] 区间内搜索。若区间端点的大小关系不满足
    二分条件（即两端买租优劣相同），返回 None。

    Args:
        base_params: 支持 rent_price_ratio 形式，invest_return 字段会被覆盖

    Returns:
        临界 invest_return，或 None（无解）
    """
    def diff(r):
        params = base_params.copy()
        params["invest_return"] = r
        resolved = resolve_params(params)
        buy, rent = compute_costs(**resolved)
        return rent - buy  # >0 买房更优, <0 租房更优

    d_low = diff(search_low)
    d_high = diff(search_high)

    if d_low * d_high > 0:
        return None  # 区间内无符号变化，无法二分

    lo, hi = search_low, search_high
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if diff(lo) * diff(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def critical_invest_return_analysis(
    base_params: dict,
    param_ranges: dict[str, np.ndarray],
    years: int = 300,
) -> dict[str, pd.DataFrame]:
    """在不同参数取值下，计算临界 invest_return。

    对 param_ranges 中的每个参数，固定其他参数为 base_params，
    逐步变化该参数，求各取值对应的临界 invest_return。

    Args:
        base_params:  基准参数（支持 rent_price_ratio 形式，会覆盖 years）
        param_ranges: {参数名: 取值数组}
        years:        分析时间跨度（年），默认 300

    Returns:
        {参数名: DataFrame(columns=[param, critical_invest_return])}
    """
    results = {}

    for param, values in param_ranges.items():
        rows = []
        for value in values:
            params = base_params.copy()
            params["years"] = years
            params[param] = value
            params["invest_return"] = 0.0  # 占位，由二分法覆盖
            critical = find_critical_invest_return(params)
            rows.append(
                {
                    param: value,
                    "critical_invest_return": critical,
                }
            )
        results[param] = pd.DataFrame(rows)

    return results
