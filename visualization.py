"""
可视化模块：敏感性分析图和临界投资回报率图。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_sensitivity(
    sensitivity_results: dict[str, tuple[list, list, list]],
    output_dir: str = "output",
) -> list[Path]:
    """将敏感性分析结果绘图并保存。

    Args:
        sensitivity_results: analysis.sensitivity_analysis 的返回值
        output_dir:          图片输出目录

    Returns:
        保存的图片路径列表
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    saved = []
    for param, (values, buy_costs, rent_costs) in sensitivity_results.items():
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(values, buy_costs, marker="o", label="buy_total_cost")
        ax.plot(values, rent_costs, marker="o", label="rent_total_cost")
        ax.set_xlabel(param)
        ax.set_ylabel("total_cost")
        ax.set_title(f"Sensitivity: {param}")
        ax.legend()
        ax.grid(True)
        fig.tight_layout()

        png_file = path / f"sensitivity_{param}.png"
        fig.savefig(png_file)
        plt.close(fig)
        saved.append(png_file)

    return saved


def plot_critical_invest_return(
    critical_results: dict[str, pd.DataFrame],
    output_dir: str = "output",
    years: int = 300,
) -> list[Path]:
    """将临界投资回报率分析结果绘图并保存。

    Args:
        critical_results: analysis.critical_invest_return_analysis 的返回值
        output_dir:       图片输出目录
        years:            分析时间跨度（用于标题）

    Returns:
        保存的图片路径列表
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    saved = []
    for param, df in critical_results.items():
        valid = df.dropna(subset=["critical_invest_return"])
        if valid.empty:
            continue

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(
            valid[param],
            valid["critical_invest_return"] * 100,
            marker="o",
            color="darkorange",
        )
        ax.set_xlabel(param)
        ax.set_ylabel("critical invest_return (%)")
        ax.set_title(f"Critical invest_return vs {param} ({years}yr)")
        ax.grid(True)
        fig.tight_layout()

        png_file = path / f"critical_invest_return_{param}.png"
        fig.savefig(png_file)
        plt.close(fig)
        saved.append(png_file)

    return saved
