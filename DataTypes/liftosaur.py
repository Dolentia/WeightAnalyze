from dataclasses import dataclass, field
from datetime import datetime
from typing import List, TypedDict, Any
import json

@dataclass
class WeightStatRecord:
    date: str
    weight: float

class FileRecord(TypedDict):
    vtype: str
    value: dict[str, Any]
    timestamp: int
    updatedAt: int

class StatsData(TypedDict):
    stats: dict[str, dict[str, List[FileRecord]]]

@dataclass
class LiftosaurStats:
    weight_history: List[WeightStatRecord] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: StatsData) -> "LiftosaurStats":
        weight_history = []
        
        records = data.get("stats", {}).get("weight", {}).get("weight", [])
        
        for record in records:
            timestamp_ms = record.get("timestamp")
            weight_val = record.get("value", {}).get("value")
            
            if timestamp_ms is not None and weight_val is not None:
                try:
                    timestamp_sec = int(timestamp_ms) / 1000.0
                    date_str = datetime.fromtimestamp(timestamp_sec).strftime('%d-%m-%Y')
                except (ValueError, TypeError):
                    date_str = str(timestamp_ms)

                weight_history.append(
                    WeightStatRecord(date=date_str, weight=float(weight_val))
                )

        return cls(weight_history=weight_history)