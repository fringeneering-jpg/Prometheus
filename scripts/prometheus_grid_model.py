#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
prometheus_grid_model.py — End-to-End Planetary Solar-Thermal & Desalination Verification
Repository : https://github.com/fringeneering-jpg/Prometheus
Core Import: https://github.com/fringeneering-jpg/Caloricum (../Caloricum)
Master DOI : https://doi.org/10.5281/zenodo.24281039
Dependencies: Python 3 standard library (+ optional numpy check)

Verifies:
  1. Mercury perihelion/mean solar flux, 116-183 modular 30 km^2 gossamer collectors,
     and passive solar-sail orbit-trim authority
  2. 1.06 um diffraction-limited beam waist across 0.5-1.0 AU (130 m transmitter)
  3. 50 TW -> 30 TW primary + 10 TW Caloricum-cooled cryo-TPV recovery = 40 TW (80%)
     power balance and imported Caloricum tungsten reject ledger
  4. GEO/EML1 gatekeeper (0.12-1.09 s) & 10,000 km MEO switchboard (33 ms) pass timing
  5. Twin 100 m x 300 m basalt/magnetite thermal storage & 1.2 GWe supercritical steam cycle
  6. Condenser-driven MED seawater desalination & weekly zero-brine NaCl/KCl/Mg/Li harvest
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False

from prometheus.grid import (
    CALORICUM_IMPORT_SOURCE,
    basalt_bay_and_steam_cycle,
    diffraction_beam_budget,
    meo_and_gatekeeper_timing,
    mercury_collector_ring_budget,
    stage1_power_and_caloricum_balance,
    weekly_zero_brine_mineral_yield,
)


def main() -> int:
    banner = "=" * 88
    print(banner)
    print(" PROMETHEUS PLANETARY SOLAR-THERMAL & ZERO-BRINE DESALINATION GRID — AUDIT SUITE")
    print(" Foundational Theory DOI : https://doi.org/10.5281/zenodo.24281039")
    print(f" Caloricum Core Binding  : {CALORICUM_IMPORT_SOURCE}")
    print(f" Runtime Backend         : Python {sys.version.split()[0]} "
          f"({'NumPy ' + np.__version__ if HAS_NUMPY else 'Pure Stdlib'})")
    print(banner)

    # ------------------------------------------------------------------
    # 1. Stage 1A: Mercury Polar Terminator Collector Ring & Solar Flux
    # ------------------------------------------------------------------
    merc = mercury_collector_ring_budget()
    print("\n[1] STAGE 1A — MERCURY DAWN-DUSK POLAR TERMINATOR GOSSAMER COLLECTOR RING")
    print("-" * 88)
    print(f"Mercury perihelion / mean / aphelion  : {merc['r_peri_au']:.4f} / "
          f"{merc['r_sma_au']:.4f} / {merc['r_aph_au']:.4f} AU")
    print(f"Solar irradiance (perihelion)         : {merc['flux_peri_w_m2']:,.1f} W/m^2")
    print(f"Solar irradiance (SMA / time-mean)    : {merc['flux_sma_w_m2']:,.1f} / "
          f"{merc['flux_time_mean_w_m2']:,.1f} W/m^2")
    print(f"Single 30 km^2 parabola (D={merc['unit_diameter_km']:.2f} km) : "
          f"{merc['unit_power_mean_gw']:.1f} GW (mean) to {merc['unit_power_peri_gw']:.1f} GW (perihelion)")
    print(f"Active collectors for 50 TW input     : {int(merc['n_collectors_peri'])} (perihelion) "
          f"to {int(merc['n_collectors_mean'])} (mean flux)")
    print(f"Passive solar-sail trim thrust/unit   : {merc['sail_force_mean_kn']:.2f} - "
          f"{merc['sail_force_peri_kn']:.2f} kN (precession {merc['precession_deg_day']:.3f} deg/day)")

    assert int(merc["n_collectors_peri"]) == 116
    assert int(merc["n_collectors_mean"]) == 183

    # ------------------------------------------------------------------
    # 2. Stage 1B: 50 TW -> 40 TW Power Balance & Caloricum Thermal Core
    # ------------------------------------------------------------------
    pwr = stage1_power_and_caloricum_balance()
    dif = diffraction_beam_budget()
    print("\n[2] STAGE 1B — 50 TW -> 40 TW COHERENT CONVERSION & CALORICUM REJECT LEDGER")
    print("-" * 88)
    print(f"Intercepted Mercury solar input       : {pwr['solar_input_tw']:.1f} TW")
    print(f"Primary 1.06 um solar-pumped laser    : {pwr['primary_laser_tw']:.1f} TW (60.0% direct)")
    print(f"Caloricum cryo-TPV @ 60 K efficiency  : {pwr['tpv_cell_raw_eff'] * 100:.2f}% cell "
          f"(Carnot {pwr['tpv_carnot_eff'] * 100:.2f}%) -> 50.0% diode-laser recovery")
    print(f"Cryo-TPV diode-laser recovery         : {pwr['tpv_laser_recovery_tw']:.1f} TW "
          f"(from {pwr['primary_thermal_tw']:.1f} TW primary heat)")
    print(f"Total coherent 1.06 um output         : {pwr['coherent_output_tw']:.1f} TW "
          f"({pwr['net_efficiency_pct']:.1f}% net solar-to-laser efficiency)")
    print(f"Caloricum continuous waste-heat sink  : {pwr['final_reject_tw']:.1f} TW -> "
          f"{pwr['caloricum_mdot_min_mg_s']:.2f}-{pwr['caloricum_mdot_max_mg_s']:.2f} mg/s W "
          f"({pwr['caloricum_annual_min_kg']:,.0f}-{pwr['caloricum_annual_max_kg']:,.0f} kg/yr, "
          f"{pwr['caloricum_vol_min_l']:.1f}-{pwr['caloricum_vol_max_l']:.1f} L/yr)")
    print(f"Avoided classical radiator mass       : {pwr['radiator_750k_mt']:.2f} Mt (750 K) to "
          f"{pwr['radiator_500k_mt']:.2f} Mt (500 K)")
    print(f"130 m Tx @ 1.06 um Gaussian waist     : {dif['gaussian_waist_05au_m']:.1f} m (0.5 AU hop) | "
          f"{dif['gaussian_waist_1au_m']:.1f} m (1.0 AU, Airy r={dif['airy_radius_1au_m']:.0f} m)")
    print(f"10,000 km MEO diffraction spot limit  : {dif['meo_diffraction_spot_m']:.2f} m "
          f"(easily paints 100 m x 300 m ground bay)")

    assert abs(pwr["coherent_output_tw"] - 40.0) < 1e-9
    assert abs(pwr["net_efficiency_pct"] - 80.0) < 1e-9

    # ------------------------------------------------------------------
    # 3. Stage 2: GEO/EML1 Gatekeeper & 10,000 km MEO Switchboard Timing
    # ------------------------------------------------------------------
    meo = meo_and_gatekeeper_timing()
    print("\n[3] STAGE 2 — ROUTING LATENCIES, MEO PASS TIMING & INHERENT SAFETY BUDGET")
    print("-" * 88)
    print(f"Upstream Gatekeeper one-way latency   : {meo['latency_geo_s']:.3f} s (GEO) to "
          f"{meo['latency_eml1_s']:.3f} s (EML1) [spec: 0.12-1.09 s]")
    print(f"10,000 km MEO Switchboard latency     : {meo['latency_meo_ms']:.2f} ms [spec: ~33 ms]")
    print(f"10,000 km MEO orbital speed & period  : {meo['orbital_velocity_km_s']:.2f} km/s | "
          f"{meo['orbital_period_hr']:.2f} hours")
    print(f"High-elevation pass (>= 30 deg)       : {meo['pass_above_30deg_inertial_min']:.1f} min (inertial) | "
          f"{meo['pass_above_30deg_prograde_min']:.1f} min (prograde ground track)")
    print(f"Horizon-to-horizon visibility         : {meo['horizon_to_horizon_prograde_min']:.1f} min "
          f"({int(meo['sats_per_plane_continuous'])} orbiters/plane for 100% overlap)")
    print(f"1 ppm approach-deterrence tap         : {pwr['deterrence_1ppm_mw']:.1f} MW "
          f"(1e-6 of 40 TW trunk; cold-shutdown + air-gapped ROM + Jiba phase lock)")

    assert 33.0 <= meo["latency_meo_ms"] <= 34.0
    assert 0.115 <= meo["latency_geo_s"] <= 0.125
    assert 1.08 <= meo["latency_eml1_s"] <= 1.10

    # ------------------------------------------------------------------
    # 4. Stage 3: Twin Basalt Bays, 1.2 GWe Steam & Zero-Brine Minerals
    # ------------------------------------------------------------------
    bay = basalt_bay_and_steam_cycle()
    brine = weekly_zero_brine_mineral_yield(condenser_reject_gw=bay["q_condenser_reject_gw"])
    global_stations = int((pwr["coherent_output_tw"] * 1_000.0) // bay["q_thermal_in_gw"])
    global_electric_tw = (global_stations * 1.20) / 1_000.0

    print("\n[4] STAGE 3 — TWIN 100m x 300m BASALT BAYS, 1.2 GWe STEAM & ZERO-BRINE HARVEST")
    print("-" * 88)
    print(f"Single basalt/magnetite bay (3 m bed) : {bay['bay_area_m2']:,.0f} m^2 | "
          f"{bay['bay_mass_tonnes']:,.0f} tonnes | {bay['storage_single_gwh_th']:.1f} GWh_th (1,000-1,300 C)")
    print(f"Twin-bay sensible thermal buffer      : {bay['storage_twin_gwh_th']:.1f} GWh_th "
          f"({bay['twin_bay_autonomy_hr']:.1f} hours full-load 1.2 GWe autonomy)")
    print(f"Dry rock floor upward radiant flux    : {bay['radiant_flux_min_kw_m2']:.1f} - "
          f"{bay['radiant_flux_max_kw_m2']:.1f} kW/m^2 (flashes roof mist in mid-air)")
    print(f"1.20 GWe supercritical steam cycle    : {bay['q_thermal_in_gw']:.2f} GW_th in | "
          f"{bay['steam_mass_flow_kg_s']:.1f} kg/s (>374 C, >22.1 MPa) | "
          f"{bay['q_condenser_reject_gw']:.2f} GW_th condenser")
    print(f"Condenser MED freshwater production   : {brine['freshwater_m3_day']:,.0f} m^3/day "
          f"({brine['freshwater_kg_s']:,.0f} kg/s potable distillate, ZERO marine brine)")
    print(f"Weekly lined brine-pit mineral yield  : "
          f"NaCl {brine['nacl_tonnes_week']:,.0f} t | "
          f"Mg {brine['mg_tonnes_week']:,.0f} t | "
          f"KCl {brine['kcl_tonnes_week']:,.0f} t | "
          f"Li2CO3 {brine['li2co3_tonnes_week']:.2f} t/wk ({brine['li2co3_tonnes_year']:.0f} t/yr)")
    print(f"Planetary capacity (40 TW optical)    : {global_stations:,d} twin-bay 1.2 GWe stations = "
          f"{global_electric_tw:.2f} TWe synchronous 50/60 Hz baseload")
    print("Tariff architecture                   : Industrial @ 30% incumbent grid | Residential @ $0.00/kWh")

    assert bay["storage_twin_gwh_th"] > 40.0
    assert 900.0 <= bay["steam_mass_flow_kg_s"] <= 1_000.0
    assert brine["freshwater_m3_day"] > 500_000.0
    assert brine["li2co3_tonnes_week"] > 7.0

    print("\n" + banner)
    print(" ALL PROMETHEUS PLANETARY GRID & ZERO-BRINE CHECKS PASSED (EXIT 0)")
    print(banner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
