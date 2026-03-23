
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2)
    doctor_id: int = Field(..., gt=0)
    date: str = Field(..., min_length=8)
    reason: str = Field(..., min_length=5)
    appointment_type: str = "in-person"
    senior_citizen: bool = False

class NewDoctor(BaseModel):
    name: str = Field(..., min_length=2)
    specialization: str = Field(..., min_length=2)
    fee: int = Field(..., gt=0)
    experience_years: int = Field(..., gt=0)
    is_available: bool = True

doctors = [
    {"id": 1, "name": "Dr. Sharma", "specialization": "Cardiologist", "fee": 800, "experience_years": 10, "is_available": True},
    {"id": 2, "name": "Dr. Mehta", "specialization": "Dermatologist", "fee": 500, "experience_years": 7, "is_available": True},
    {"id": 3, "name": "Dr. Reddy", "specialization": "Pediatrician", "fee": 600, "experience_years": 8, "is_available": False},
    {"id": 4, "name": "Dr. Khan", "specialization": "General", "fee": 300, "experience_years": 5, "is_available": True},
    {"id": 5, "name": "Dr. Iyer", "specialization": "Cardiologist", "fee": 900, "experience_years": 15, "is_available": True},
    {"id": 6, "name": "Dr. Das", "specialization": "Dermatologist", "fee": 400, "experience_years": 6, "is_available": False}
]

appointments = []
appt_counter = 1

def find_doctor(doctor_id):
    for d in doctors:
        if d["id"] == doctor_id:
            return d
    return None

def find_appointment(appointment_id):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            return a
    return None

def calculate_fee(base_fee, appointment_type, senior):
    if appointment_type == "video":
        fee = base_fee * 0.8
    elif appointment_type == "emergency":
        fee = base_fee * 1.5
    else:
        fee = base_fee

    if senior:
        return int(fee), int(fee * 0.85)

    return int(fee), int(fee)

def filter_doctors_logic(specialization=None, max_fee=None, min_experience=None, is_available=None):
    result = doctors

    if specialization is not None:
        result = [d for d in result if d["specialization"] == specialization]

    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]

    if min_experience is not None:
        result = [d for d in result if d["experience_years"] >= min_experience]

    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]

    return result

@app.get("/")
def home():
    return {"message": "Welcome to MediCare Clinic"}

@app.get("/doctors")
def get_doctors():
    available = [d for d in doctors if d["is_available"]]
    return {"total": len(doctors), "available_count": len(available), "doctors": doctors}

@app.get("/doctors/summary")
def doctors_summary():
    total = len(doctors)
    available = len([d for d in doctors if d["is_available"]])
    most_exp = max(doctors, key=lambda d: d["experience_years"])
    cheapest = min(doctors, key=lambda d: d["fee"])

    spec_count = {}
    for d in doctors:
        spec = d["specialization"]
        spec_count[spec] = spec_count.get(spec, 0) + 1

    return {
        "total_doctors": total,
        "available": available,
        "most_experienced": most_exp["name"],
        "cheapest_fee": cheapest["fee"],
        "specialization_count": spec_count
    }

@app.get("/doctors/filter")
def filter_doctors(
    specialization: str = Query(None),
    max_fee: int = Query(None),
    min_experience: int = Query(None),
    is_available: bool = Query(None)
):
    result = filter_doctors_logic(specialization, max_fee, min_experience, is_available)
    return {"count": len(result), "doctors": result}

@app.get("/doctors/search")
def search_doctors(keyword: str):
    result = [
        d for d in doctors
        if keyword.lower() in d["name"].lower()
        or keyword.lower() in d["specialization"].lower()
    ]
    if not result:
        return {"message": "No doctors found"}
    return {"total_found": len(result), "doctors": result}

@app.get("/doctors/sort")
def sort_doctors(sort_by: str = "fee", order: str = "asc"):
    if sort_by not in ["fee", "name", "experience_years"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    reverse = order == "desc"
    return {"doctors": sorted(doctors, key=lambda d: d[sort_by], reverse=reverse)}

@app.get("/doctors/page")
def paginate_doctors(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit
    return {
        "page": page,
        "limit": limit,
        "total": len(doctors),
        "total_pages": -(-len(doctors) // limit),
        "doctors": doctors[start:end]
    }

@app.post("/doctors")
def add_doctor(data: NewDoctor):
    names = [d["name"].lower() for d in doctors]
    if data.name.lower() in names:
        raise HTTPException(status_code=400, detail="Doctor already exists")

    new_id = max(d["id"] for d in doctors) + 1
    doctor = {
        "id": new_id,
        "name": data.name,
        "specialization": data.specialization,
        "fee": data.fee,
        "experience_years": data.experience_years,
        "is_available": data.is_available
    }

    doctors.append(doctor)
    return {"doctor": doctor}

@app.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: int, fee: int = Query(None), is_available: bool = Query(None)):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if fee is not None:
        doctor["fee"] = fee
    if is_available is not None:
        doctor["is_available"] = is_available

    return {"doctor": doctor}
@app.get("/doctors/browse")
def browse_doctors(
    keyword: str = Query(None),
    sort_by: str = "fee",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = doctors

    if keyword is not None:
        result = [
            d for d in result
            if keyword.lower() in d["name"].lower()
            or keyword.lower() in d["specialization"].lower()
        ]

    if sort_by not in ["fee", "name", "experience_years"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    reverse = order == "desc"
    result = sorted(result, key=lambda d: d[sort_by], reverse=reverse)

    start = (page - 1) * limit
    end = start + limit

    return {
        "total_results": len(result),
        "page": page,
        "total_pages": -(-len(result) // limit),
        "doctors": result[start:end]
    }
@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    for a in appointments:
        if a["doctor_id"] == doctor_id and a["status"] == "scheduled":
            raise HTTPException(status_code=400, detail="Doctor has active appointments")

    doctors.remove(doctor)
    return {"message": "Doctor deleted"}
@app.get("/appointments")
def get_appointments():
    return {"total": len(appointments), "appointments": appointments}

@app.post("/appointments")
def create_appointment(data: AppointmentRequest):
    global appt_counter

    doctor = find_doctor(data.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not doctor["is_available"]:
        raise HTTPException(status_code=400, detail="Doctor not available")

    original_fee, final_fee = calculate_fee(
        doctor["fee"],
        data.appointment_type,
        data.senior_citizen
    )

    appointment = {
        "appointment_id": appt_counter,
        "patient": data.patient_name,
        "doctor_id": doctor["id"],
        "doctor_name": doctor["name"],
        "date": data.date,
        "type": data.appointment_type,
        "original_fee": original_fee,
        "final_fee": final_fee,
        "status": "scheduled"
    }

    appointments.append(appointment)
    appt_counter += 1

    return {"appointment": appointment}

@app.post("/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt["status"] = "confirmed"
    return {"appointment": appt}

@app.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt["status"] = "cancelled"

    doctor = find_doctor(appt["doctor_id"])
    if doctor:
        doctor["is_available"] = True

    return {"message": "Appointment cancelled"}

@app.post("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt["status"] = "completed"
    return {"message": "Appointment completed"}

@app.get("/appointments/active")
def get_active_appointments():
    result = [a for a in appointments if a["status"] in ["scheduled", "confirmed"]]
    return {"appointments": result}

@app.get("/appointments/by-doctor/{doctor_id}")
def get_appointments_by_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    result = [a for a in appointments if a["doctor_id"] == doctor_id]
    return {"appointments": result}

@app.get("/appointments/search")
def search_appointments(patient_name: str):
    result = [
        a for a in appointments
        if patient_name.lower() in a["patient"].lower()
    ]
    return {"results": result}

@app.get("/appointments/sort")
def sort_appointments(sort_by: str = "final_fee"):
    if sort_by not in ["final_fee", "date"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    return {"appointments": sorted(appointments, key=lambda a: a[sort_by])}

@app.get("/appointments/page")
def paginate_appointments(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "total_pages": -(-len(appointments) // limit),
        "appointments": appointments[start:end]
    }

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"doctor": doctor}
