"""
T60: Multiple-imputation sensitivity check for missing gdp_growth_pc.

This script addresses the Round-2 reviewer request for a brief
multiple-imputation check under Rubin's rules. It imputes the main growth
outcome under a conditional MAR design using the existing covariate set,
treatment indicators, fiscal observables, region indicators, and year
indicators. It then re-estimates the two-way fixed-effects TWFE specification
on each imputed dataset and pools the D2 coefficient and variance using
Rubin's rules.

The goal is sensitivity analysis, not a missing-not-at-random correction.
"""

from __future__ import annotations

import os
import warnings
from math import erf
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge


ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)

Y = "gdp_growth_pc"
REGRESSORS = ["D2", "D1", "primary_ratio", "secondary_ratio", "ln_pop", "gov_scale"]
IMPUTATION_FEATURES = [
    Y,
    "D2",
    "D1",
    "primary_ratio",
    "secondary_ratio",
    "ln_pop",
    "gov_scale",
    "ln_fiscal_exp_pc",
    "ln_fiscal_rev_pc",
    "fiscal_autonomy",
    "transfer_dependence",
    "region_east",
    "region_central",
    "region_west",
    "high_development",
    "high_agriculture",
    "is_county_city",
]
M = 20
BASE_SEED = 20260519


def within_transform_iterative(
    df: pd.DataFrame,
    values: np.ndarray,
    tol: float = 1e-10,
    max_iter: int = 500,
) -> np.ndarray:
    """Two-way FE residualization by alternating county and year demeaning."""
    y = np.asarray(values, dtype=float).copy()
    county = df["county_code"]
    year = df["year"]
    for _ in range(max_iter):
        old = y.copy()
        y -= pd.Series(y, index=df.index).groupby(county).transform("mean").to_numpy()
        y -= pd.Series(y, index=df.index).groupby(year).transform("mean").to_numpy()
        if np.max(np.abs(y - old)) < tol:
            break
    return y


def twfe_clustered(
    df: pd.DataFrame,
    y_col: str,
    x_cols: list[str],
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """TWFE OLS after within transformation, clustered by county."""
    data = df.dropna(subset=[y_col, *x_cols]).copy().reset_index(drop=True)
    y_w = within_transform_iterative(data, data[y_col].to_numpy())
    x_w = np.column_stack(
        [within_transform_iterative(data, data[col].to_numpy()) for col in x_cols]
    )

    xtx = x_w.T @ x_w
    xtx_inv = np.linalg.inv(xtx)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        beta = xtx_inv @ (x_w.T @ y_w)
        resid = y_w - x_w @ beta

    meat = np.zeros((len(x_cols), len(x_cols)))
    for idx in data.groupby("county_code").indices.values():
        x_g = x_w[idx]
        u_g = resid[idx]
        score_g = x_g.T @ u_g
        meat += np.outer(score_g, score_g)

    n = len(data)
    k = len(x_cols)
    g = data["county_code"].nunique()
    finite_sample = (g / (g - 1)) * ((n - 1) / (n - k))
    variance = finite_sample * xtx_inv @ meat @ xtx_inv
    return beta, np.diag(variance), n, g


def main() -> None:
    df = pd.read_csv("data/analysis/panel_analysis_public.csv")

    # Growth is mechanically unavailable in the first and final differenced
    # years, so the imputation check follows the usable growth window.
    panel = df.loc[df["year"].between(2001, 2022)].copy()
    panel = panel.dropna(subset=REGRESSORS).reset_index(drop=True)

    complete_beta, complete_var, complete_n, complete_g = twfe_clustered(
        panel, Y, REGRESSORS
    )

    year_dummies = pd.get_dummies(
        panel["year"].astype(int), prefix="year", drop_first=False, dtype=float
    )
    imputation_matrix = pd.concat([panel[IMPUTATION_FEATURES], year_dummies], axis=1)
    missing_y = panel[Y].isna().to_numpy()

    coefs = []
    variances = []
    rows = []
    for m in range(M):
        imputer = IterativeImputer(
            estimator=BayesianRidge(),
            max_iter=10,
            sample_posterior=True,
            skip_complete=True,
            random_state=BASE_SEED + m,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            imputed = imputer.fit_transform(imputation_matrix)

        imputed_panel = panel.copy()
        imputed_y = panel[Y].to_numpy(dtype=float).copy()
        imputed_y[missing_y] = imputed[missing_y, 0]
        imputed_panel["gdp_growth_pc_mi"] = imputed_y

        beta, var, n, g = twfe_clustered(imputed_panel, "gdp_growth_pc_mi", REGRESSORS)
        coefs.append(beta)
        variances.append(var)
        rows.append(
            {
                "imputation": m + 1,
                "d2_estimate": beta[0],
                "d2_se": np.sqrt(var[0]),
                "N": n,
                "clusters": g,
            }
        )

    coef_arr = np.vstack(coefs)
    var_arr = np.vstack(variances)
    pooled_beta = coef_arr.mean(axis=0)
    within_var = var_arr.mean(axis=0)
    between_var = coef_arr.var(axis=0, ddof=1)
    total_var = within_var + (1 + 1 / M) * between_var

    out_dir = Path("outputs/tables")
    out_dir.mkdir(parents=True, exist_ok=True)

    detail = pd.DataFrame(rows)
    detail.to_csv(out_dir / "table_t60_multiple_imputation_draws.csv", index=False)

    pooled = pd.DataFrame(
        [
            {
                "check": "Complete-case TWFE",
                "estimate": complete_beta[0],
                "se": np.sqrt(complete_var[0]),
                "p_value": 2
                * (1 - normal_cdf(abs(complete_beta[0] / np.sqrt(complete_var[0])))),
                "N": complete_n,
                "clusters": complete_g,
                "note": "Observed outcomes only; same TWFE specification as baseline.",
            },
            {
                "check": "Multiple-imputation TWFE",
                "estimate": pooled_beta[0],
                "se": np.sqrt(total_var[0]),
                "p_value": 2
                * (1 - normal_cdf(abs(pooled_beta[0] / np.sqrt(total_var[0])))),
                "N": len(panel),
                "clusters": panel["county_code"].nunique(),
                "note": (
                    f"{M} imputations; IterativeImputer/BayesianRidge; "
                    "Rubin pooled variance; conditional MAR sensitivity only."
                ),
            },
            {
                "check": "Rubin within variance",
                "estimate": within_var[0],
                "se": np.nan,
                "p_value": np.nan,
                "N": len(panel),
                "clusters": panel["county_code"].nunique(),
                "note": "Average complete-data variance for D2 across imputations.",
            },
            {
                "check": "Rubin between variance",
                "estimate": between_var[0],
                "se": np.nan,
                "p_value": np.nan,
                "N": len(panel),
                "clusters": panel["county_code"].nunique(),
                "note": "Between-imputation variance for D2.",
            },
        ]
    )
    pooled.to_csv(out_dir / "table_t60_multiple_imputation.csv", index=False)

    print("T60 SUMMARY")
    print(f"Complete-case: D2 = {complete_beta[0]:.3f} (SE {np.sqrt(complete_var[0]):.3f})")
    print(f"MI pooled:     D2 = {pooled_beta[0]:.3f} (SE {np.sqrt(total_var[0]):.3f})")
    print(f"Saved: {out_dir / 'table_t60_multiple_imputation.csv'}")


def normal_cdf(x: float) -> float:
    """Standard normal CDF without scipy dependency."""
    return 0.5 * (1 + erf(x / np.sqrt(2)))


if __name__ == "__main__":
    main()
