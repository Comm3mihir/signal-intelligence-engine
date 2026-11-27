from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EventAssessment(StrictModel):
    title: str = Field(min_length=3, max_length=240)
    actors: list[str] = Field(max_length=12)
    regions: list[str] = Field(max_length=12)
    date: str = Field(max_length=50)
    classification: str = Field(max_length=80)
    reported_developments: list[str] = Field(min_length=1, max_length=8)
    unverified_claims: list[str] = Field(max_length=8)
    article_ids: list[str] = Field(min_length=1, max_length=8)


class Prediction(StrictModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,19}$")
    parent: str | None
    title: str = Field(min_length=8, max_length=200)
    domain: Literal["policy", "trade", "technology", "finance", "energy", "diplomacy", "security", "other"]
    scenario: Literal["consequence", "alternative"]
    probability: float = Field(gt=0, lt=1, allow_inf_nan=False)
    horizon_days: int = Field(ge=1, le=180)
    reasoning: str = Field(min_length=12, max_length=1000)
    assumptions: list[str] = Field(min_length=1, max_length=5)
    alternatives: list[str] = Field(max_length=5)
    weaknesses: list[str] = Field(min_length=1, max_length=5)
    confirm_if: str = Field(min_length=15, max_length=600)
    refute_if: str = Field(min_length=15, max_length=600)
    support_ids: list[str] = Field(max_length=8)
    contradict_ids: list[str] = Field(max_length=8)
    precedent_ids: list[str] = Field(max_length=5)
    exclusive_group: str | None


class Draft(StrictModel):
    predictions: list[Prediction] = Field(min_length=3, max_length=10)

    @model_validator(mode="after")
    def validate_graph(self):
        by_id = {item.key: item for item in self.predictions}
        if len(by_id) != len(self.predictions):
            raise ValueError("Prediction keys must be unique")
        roots = [item for item in self.predictions if item.parent is None]
        if not 3 <= len(roots) <= 5:
            raise ValueError("Generate three to five first-order forecasts")
        if not any(item.scenario == "alternative" for item in roots):
            raise ValueError("Include at least one first-order alternative scenario")
        groups = {}
        titles = set()
        for item in self.predictions:
            if item.confirm_if.casefold() == item.refute_if.casefold():
                raise ValueError("Confirmation and refutation need distinct criteria")
            if item.title.casefold() in titles:
                raise ValueError("Forecasts must describe distinct developments")
            titles.add(item.title.casefold())
            if item.parent:
                parent = by_id.get(item.parent)
                if parent is None or parent.parent is not None or item.horizon_days < parent.horizon_days:
                    raise ValueError("Second-order forecasts need a first-order parent and a compatible horizon")
            if set(item.support_ids) & set(item.contradict_ids):
                raise ValueError("Citations cannot be simultaneously supporting and contradictory")
            if item.exclusive_group:
                group = (item.parent, item.exclusive_group)
                groups[group] = groups.get(group, 0) + item.probability
        if any(total > 1.000000001 for total in groups.values()):
            raise ValueError("A mutually exclusive group exceeds 100%")
        return self


class Verification(StrictModel):
    stance: Literal["irrelevant", "supports", "contradicts", "partial", "resolution_candidate"]
    reasoning: str = Field(min_length=10, max_length=700)
    probability: float | None = Field(ge=0.01, le=0.99, allow_inf_nan=False)


class AnalystReview(StrictModel):
    status: Literal["confirmed", "refuted", "expired_inconclusive"]
    article_id: str | None = Field(default=None, max_length=32)
    criteria_verified: bool = False
    reasoning: str = Field(min_length=20, max_length=1500)
    credibility: str = Field(min_length=5, max_length=600)
