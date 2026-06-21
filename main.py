from fastapi import FastAPI
from supabase_client import supabase
from jose import jwt
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "cloud-secret"
ALGORITHM = "HS256"

# -----------------------
# LOGIN (JWT SIMPLE)
# -----------------------
@app.post("/login")
def login(email: str, password: str):

    user = supabase.table("users") \
        .select("*") \
        .eq("email", email) \
        .eq("password_hash", password) \
        .execute()

    if len(user.data) == 0:
        return {"error": "Login gagal"}

    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "token": token,
        "role": user.data[0]["role"]
    }

# -----------------------
# GET MAHASISWA
# -----------------------
@app.get("/mahasiswa")
def get_mahasiswa():
    data = supabase.table("mahasiswa").select("*").execute()
    return data.data

# -----------------------
# POST KRS
# -----------------------
@app.post("/krs")
def create_krs(mahasiswa_id: str, semester: int, kode_matkul: str, nama_matkul: str):

    data = supabase.table("krs").insert({
        "mahasiswa_id": mahasiswa_id,
        "semester": semester,
        "kode_matkul": kode_matkul,
        "nama_matkul": nama_matkul
    }).execute()

    return {
        "status": "success",
        "data": data.data
    }

# -----------------------
# POST NILAI
# -----------------------
@app.post("/nilai")
def input_nilai(mahasiswa_id: str, kode_matkul: str, komponen: str, nilai: float):

    data = supabase.table("nilai").insert({
        "mahasiswa_id": mahasiswa_id,
        "kode_matkul": kode_matkul,
        "komponen": komponen,
        "nilai": nilai
    }).execute()

    return {"status": "success", "data": data.data}

# -----------------------
# POST PEMBAYARAN
# -----------------------
@app.post("/pembayaran")
def pembayaran(mahasiswa_id: str, semester: int, jumlah: float, metode: str):

    data = supabase.table("pembayaran").insert({
        "mahasiswa_id": mahasiswa_id,
        "semester": semester,
        "jumlah": jumlah,
        "metode": metode,
        "status": "PAID"
    }).execute()

    return {"status": "success", "data": data.data}