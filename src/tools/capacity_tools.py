import json
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class CheckBedInput(BaseModel):
    department: str = Field(
        ...,
        description="Department name in caps, e.g. CARDIOLOGY, ORTHOPEDICS, "
                    "PEDIATRICS, GENERAL_MEDICINE, EMERGENCY",
    )


class CheckBedAvailabilityTool(BaseTool):
    name: str = "check_bed_availability"
    description: str = (
        "Check inpatient bed capacity for one department. Returns total beds, "
        "occupied beds, available beds and a status label. A status of FULL "
        "means no beds are free and admission to that department is NOT "
        "possible — escalate to a human instead of booking. Returns "
        "UNKNOWN_DEPARTMENT if the department does not exist; do not retry "
        "with a guessed name."
    )
    args_schema: Type[BaseModel] = CheckBedInput

    def _run(self, department: str) -> str:
        try:
            beds = json.loads((DATA_DIR / "beds.json").read_text())
        except Exception as e:
            return f"TOOL_ERROR: could not read bed data ({e})"

        dept = department.strip().upper()
        record = beds.get(dept)

        if record is None:
            valid = ", ".join(beds.keys())
            return f"UNKNOWN_DEPARTMENT: {department}. Valid departments: {valid}"

        available = record["total"] - record["occupied"]

        if available <= 0:
            status = "FULL"
        elif available <= 2:
            status = "NEARLY_FULL"
        else:
            status = "AVAILABLE"

        return json.dumps({
            "department": dept,
            "total": record["total"],
            "occupied": record["occupied"],
            "available": available,
            "status": status,
        })
        