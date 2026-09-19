import json
from datetime import datetime
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"


class CreateBookingInput(BaseModel):
    doctor_id: str = Field(..., description="Doctor ID, e.g. D03")
    slot_time: str = Field(..., description="Exact slot string from get_doctor_schedule")
    patient_name: str = Field(..., description="Patient name, or 'UNKNOWN' if not given")


class CreateBookingTool(BaseTool):
    name: str = "create_booking"
    description: str = (
        "Book one appointment slot. The slot_time MUST be copied exactly from "
        "a get_doctor_schedule result — never invent a time. Returns a booking "
        "reference on success. Returns SLOT_UNAVAILABLE if that doctor does not "
        "have that slot free; if so, pick a different slot from the schedule "
        "rather than retrying the same one."
    )
    args_schema: Type[BaseModel] = CreateBookingInput

    def _run(self, doctor_id: str, slot_time: str, patient_name: str) -> str:
        try:
            doctors = json.loads((DATA_DIR / "doctors.json").read_text())
        except Exception as e:
            return f"TOOL_ERROR: could not read doctor schedules ({e})"

        doctor = next(
            (d for d in doctors if d["doctor_id"].upper() == doctor_id.strip().upper()),
            None,
        )
        if doctor is None:
            return f"NOT_FOUND: no doctor with ID {doctor_id}"

        if slot_time not in doctor["available_slots"]:
            free = doctor["available_slots"] or "none"
            return (f"SLOT_UNAVAILABLE: {doctor['name']} has no slot at "
                    f"{slot_time}. Free slots: {free}")

        ref = f"BK{datetime.now().strftime('%y%m%d%H%M%S')}"
        booking = {
            "booking_ref": ref,
            "doctor_id": doctor["doctor_id"],
            "doctor_name": doctor["name"],
            "department": doctor["department"],
            "slot_time": slot_time,
            "patient_name": patient_name,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(OUTPUT_DIR / "bookings.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(booking) + "\n")

        return json.dumps({"status": "CONFIRMED", **booking})