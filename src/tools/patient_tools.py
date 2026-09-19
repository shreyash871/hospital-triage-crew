import json
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class LookupPatientInput(BaseModel):
    patient_id: str = Field(..., description="Hospital patient ID, e.g. P1002")


class LookupPatientTool(BaseTool):
    name: str = "lookup_patient"
    description: str = (
        "Look up a patient's record by their hospital ID (format: P####). "
        "Returns name, age, known conditions, last visit date and primary "
        "department. Use ONLY when the message contains an explicit patient ID. "
        "Returns a NOT_FOUND message if the ID does not exist — do not retry "
        "with a guessed ID."
    )
    args_schema: Type[BaseModel] = LookupPatientInput

    def _run(self, patient_id: str) -> str:
        try:
            patients = json.loads((DATA_DIR / "patients.json").read_text())
        except Exception as e:
            return f"TOOL_ERROR: could not read patient records ({e})"

        for p in patients:
            if p["patient_id"].upper() == patient_id.strip().upper():
                return json.dumps(p)

        return f"NOT_FOUND: no patient with ID {patient_id}"