# HC-AI | ticket: MEM-M3-08
"""Telemetry — privacy-safe local usage logging and ROI tracking.

Design decision D-M3-04: Local-only, no cloud sync. SQLite storage.
"""

from knowledge_memory.core.telemetry.logger import TelemetryEvent, TelemetryLogger
from knowledge_memory.core.telemetry.roi import ROICalculator, ROIMetrics, format_roi

__all__ = [
    "TelemetryLogger",
    "TelemetryEvent",
    "ROICalculator",
    "ROIMetrics",
    "format_roi",
]
