"""Explainable planning rules, not spoilage predictions or agricultural shelf-life advice."""
from dataclasses import asdict, dataclass
from math import isfinite
from numbers import Real
import numpy as np
import pandas as pd
from .analytics import crop_balances


@dataclass(frozen=True)
class RiskPolicy:
    """Demo planning defaults; caller must show them and allow editing."""
    high_surplus_ratio: float = 0.25
    age_review_days: float = 3.0

    def __post_init__(self):
        for value in (self.high_surplus_ratio, self.age_review_days):
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                raise ValueError('Planning thresholds must be finite numbers.')
        if not 0 < self.high_surplus_ratio <= 1 or self.age_review_days <= 0:
            raise ValueError('Surplus threshold must be in (0, 1]; age threshold must be positive.')

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, values=None):
        if values is None:
            return cls()
        if not isinstance(values, dict) or set(values) - {'high_surplus_ratio', 'age_review_days'}:
            raise ValueError('Invalid planning policy fields.')
        return cls(**values)


def analyse_risk(data, policy=None):
    """Return independent balances, review flags and rank among surplus crops only.

    Rank: surplus kg DESC, harvest age DESC, crop name CASEFOLD ASC.
    Review score = high-surplus flag + age-review flag, only with positive surplus.
    Rank and review score answer different questions and are intentionally distinct.
    """
    policy = RiskPolicy() if policy is None else policy
    if not isinstance(policy, RiskPolicy):
        raise ValueError('Expected a RiskPolicy.')
    result = crop_balances(data)
    available = result.available_kg.to_numpy(dtype=float)
    surplus = result.potential_surplus_kg.to_numpy(dtype=float)
    result['surplus_ratio'] = np.divide(surplus, available, out=np.zeros_like(surplus), where=available > 0)
    result['balance_status'] = np.select([result.potential_surplus_kg > 0, result.shortage_kg > 0],
                                        ['Potential surplus', 'Shortage'], default='Balanced')
    result['high_surplus_flag'] = (result.potential_surplus_kg > 0) & (result.surplus_ratio >= policy.high_surplus_ratio)
    result['age_review_flag'] = (result.available_kg > 0) & (result.harvest_age_days >= policy.age_review_days)
    result['review_score'] = ((result.high_surplus_flag.astype(int) + result.age_review_flag.astype(int))
                              .where(result.potential_surplus_kg > 0, 0))
    result['review_level'] = np.select(
        [result.potential_surplus_kg <= 0, result.review_score == 2, result.review_score == 1],
        ['No surplus', 'High', 'Moderate'], default='Low')
    result['priority_rank'] = pd.Series(pd.NA, index=result.index, dtype='Int64')
    ranked = result.loc[result.potential_surplus_kg > 0].assign(_name=lambda df: df.crop.str.casefold())
    ranked = ranked.sort_values(['potential_surplus_kg', 'harvest_age_days', '_name'], ascending=[False, False, True])
    for rank, index in enumerate(ranked.index, 1):
        result.loc[index, 'priority_rank'] = rank
    result['reason'] = [explain_row(row, policy) for row in result.itertuples()]
    return result


def explain_row(row, policy):
    balance = (f'Available {row.available_kg:g} kg − estimated demand {row.estimated_demand_kg:g} kg; '
               f'positive surplus {row.potential_surplus_kg:g} kg; shortage {row.shortage_kg:g} kg.')
    age = (f'Age review: {row.harvest_age_days:g} days '
           f'{">=" if row.age_review_flag else "below threshold or no stock; threshold"} {policy.age_review_days:g} days.')
    if row.potential_surplus_kg <= 0:
        return f'{balance} No surplus-selling rank. {age} No surplus review score applies.'
    return (f'{balance} Surplus share {row.surplus_ratio:.2%}; large-surplus flag {bool(row.high_surplus_flag)} '
            f'at >= {policy.high_surplus_ratio:.2%}. {age} Review score {row.review_score}/2; '
            f'level {row.review_level}. Selling rank {row.priority_rank} by surplus kg, then age, then crop name.')


def prioritise_crop(data, policy=None):
    """Reusable recommendation for the later assistant; never uses constant crop names."""
    report = analyse_risk(data, policy)
    candidates = report.loc[report.priority_rank.notna()].sort_values('priority_rank')
    if candidates.empty:
        return None
    top = candidates.iloc[0]
    return {'crop': top.crop, 'potential_surplus_kg': float(top.potential_surplus_kg),
            'harvest_age_days': float(top.harvest_age_days), 'review_level': top.review_level,
            'reason': top.reason, 'ranking_rule': 'Largest positive surplus kg; ties: older harvest, then crop name.'}
