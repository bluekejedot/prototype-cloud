from fastapi import FastAPI
from supabase_client import supabase
from jose import jwt
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "cloud-secret"
ALGORITHM = "HS256"

@app.get("/test-users")
def test_users():

    result = supabase.table("users").select("*").execute()

    print(result.data)

    return result.data

# -----------------------
# LOGIN (JWT SIMPLE)
# -----------------------
@app.post("/login")
def login(email: str, password: str):

    user = supabase.table("users") \
        .select("*") \
        .eq("email", email) \
        .execute()

    print("DEBUG USER:", user.data)  #cek data pada tabel user

    if len(user.data) == 0:
        return {"error": "Login gagal"}

    db_password = user.data[0]["password_hash"]

    print("DEBUG PASSWORD INPUT:", password)
    print("DEBUG PASSWORD DB:", db_password)

    if db_password.strip() != password.strip():
        return {"error": "Login gagal"}

    return {"status": "login sukses"}

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