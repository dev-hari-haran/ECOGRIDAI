"""
api/schemas.py - Pydantic Request & Response Models for EcoGridAI
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConfigModel(BaseModel):
    solarKw: float = Field(default=900.0, description="Solar PV capacity in kW")
    windKw: float = Field(default=650.0, description="Wind capacity in kW")
    batteryKw: float = Field(default=500.0, description="Battery power rating in kW")
    batteryKwh: float = Field(default=1800.0, description="Battery storage capacity in kWh")
    gridLimitKw: float = Field(default=3200.0, description="Substation grid import limit in kW")


class ScenarioModel(BaseModel):
    name: str
    description: str
    load: float
    solar: float
    wind: float
    grid: float
    battery: float


class OptimizeRequest(BaseModel):
    dataset: str = Field(default="Data1.csv", description="Dataset identifier or filename")
    scenario_index: Optional[int] = Field(default=0, ge=0, le=9)
    scenario_name: Optional[str] = None
    config: ConfigModel = Field(default_factory=ConfigModel)
    modifications: Dict[str, List[str]] = Field(default_factory=dict, description="Bus resource additions, e.g. {'18': ['solar']}")
    use_entropy_weights: bool = True
    max_iter: int = Field(default=60, ge=10, le=200, description="Optimizer iterations (default 60 for fast web responsiveness)")
    async_job: bool = False
    custom_load_profile: Optional[List[float]] = None


class ValidateRequest(BaseModel):
    csv_content: Optional[str] = None
    raw_csv: Optional[str] = None
    bus_ratings: Optional[List[Dict[str, Any]]] = None
    load_profile: Optional[List[float]] = None


class RecommendationRequest(BaseModel):
    scenario_name: Optional[str] = None
    scenario_index: Optional[int] = 0
    unmet_kwh: Optional[float] = 0.0
    peak_gap_kw: Optional[float] = 0.0
    load_satisfaction: Optional[float] = 100.0
    grid_available: bool = True
    current_vector: Optional[List[float]] = None
