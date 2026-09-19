import json
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class DoctorScheduleInput(BaseModel):
    department: str = Field(
        ...,
        description="Department in caps, e.g. CARDIOLOGY, ORTHOPEDICS, "
                    "PEDIATRICS, GENERAL_MEDICINE",
    )


class GetDoctorScheduleTool(BaseTool):
    name: str = "get_doctor_schedule"
    description: str = (
        "List doctors in a department and their free appointment slots. "
        "Returns each doctor's id, name and available slot times. "
        "If every doctor has an empty slot list, NO booking is possible in "
        "that department — add the patient to the waitlist instead. "
        "Returns NO_DOCTORS if the department has no doctors at all."
    )
    args_schema: Type[BaseModel] = DoctorScheduleInput

    def _run(self, department: str) -> str:
        try:
            doctors = json.loads((DATA_DIR / "doctors.json").read_text())
        except Exception as e:
            return f"TOOL_ERROR: could not read doctor schedules ({e})"

        dept = department.strip().upper()
        matches = [d for d in doctors if d["department"] == dept]

        if not matches:
            valid = sorted({d["department"] for d in doctors})
            return (f"NO_DOCTORS: no doctors in {department}. "
                    f"Departments with doctors: {', '.join(valid)}")

        total_slots = sum(len(d["available_slots"]) for d in matches)

        return json.dumps({
            "department": dept,
            "doctors": [
                {
                    "doctor_id": d["doctor_id"],
                    "name": d["name"],
                    "available_slots": d["available_slots"],
                }
                for d in matches
            ],
            "total_free_slots": total_slots,
            "booking_possible": total_slots > 0,
        })