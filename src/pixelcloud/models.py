from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PixelCase:
    case_id: str
    wavelength_nm: float
    incident_angle_deg: float
    microlens_decenter_um: float
    pixel_pitch_um: float = 1.0
    absorber_thickness_um: float = 3.0
    absorber_alpha_per_um: float = 1.2
    refractive_index_air: float = 1.0
    refractive_index_stack: float = 1.55

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PixelCase":
        return cls(**value)


@dataclass(frozen=True)
class SimulationResult:
    case_id: str
    wavelength_nm: float
    incident_angle_deg: float
    microlens_decenter_um: float
    surface_transmission: float
    absorber_efficiency: float
    angular_efficiency: float
    effective_response: float
    crosstalk_left: float
    crosstalk_right: float
    model_version: str = "toy-model-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

