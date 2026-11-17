# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Prometheus — Planetary Solar-Thermal & Zero-Brine Desalination Grid
Software licensed under GNU AGPLv3 (see LICENSE-AGPLv3.txt).
Hardware geometries licensed under CERN-OHL-S v2 (see LICENSE-CERN-OHL-S-v2.txt).
Master Theory DOI: https://doi.org/10.5281/zenodo.24281039
"""

from .grid import (
    AU_M,
    C0_M_S,
    CALORICUM_IMPORT_SOURCE,
    basalt_bay_and_steam_cycle,
    diffraction_beam_budget,
    meo_and_gatekeeper_timing,
    mercury_collector_ring_budget,
    stage1_power_and_caloricum_balance,
    weekly_zero_brine_mineral_yield,
)

__all__ = [
    "AU_M",
    "C0_M_S",
    "CALORICUM_IMPORT_SOURCE",
    "basalt_bay_and_steam_cycle",
    "diffraction_beam_budget",
    "meo_and_gatekeeper_timing",
    "mercury_collector_ring_budget",
    "stage1_power_and_caloricum_balance",
    "weekly_zero_brine_mineral_yield",
]
