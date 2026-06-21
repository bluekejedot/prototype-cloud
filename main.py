import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_client import supabase
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "cloud-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
security = HTTPBearer()

# -----------------------
# MEMBUAT TOKEN LOGIN
# -----------------------
def create_access_token(user_data: dict):

    payload = {
        "sub": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.now(UTC) + timedelta(hours=2)
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token

# -----------------------
# VERIFIKASI TOKEN
# -----------------------
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Token tidak valid"
        )

# -----------------------
# CEK ROLE
# -----------------------

def require_role(allowed_roles: list):

    def role_checker(
        payload: dict = Depends(verify_token)
    ):

        if payload["role"] not in allowed_roles:

            raise HTTPException(
                status_code=403,
                detail="Akses ditolak"
            )

        return payload

    return role_checker

# -----------------------
# TEST JWT
# -----------------------
@app.get("/me")
def get_me(payload: dict = Depends(verify_token)):

    return {
        "email": payload["sub"],
        "role": payload["role"]
    }

# -----------------------
# TEST (CEK DATA USERS)
# -----------------------
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

    if len(user.data) == 0:
        raise HTTPException(
            status_code=401,
            detail="email tidak ditemukan"
        )

    db_password = user.data[0]["password_hash"]

    if db_password.strip() != password.strip():
        raise HTTPException(
            status_code=401,
            detail="Password salah"
        )

    token = create_access_token({
        "email": user.data[0]["email"],
        "role": user.data[0]["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.data[0]["role"]
    }

# -----------------------
# GET MAHASISWA
# -----------------------
@app.get("/mahasiswa")
def get_mahasiswa():
    data = supabase.table("mahasiswa").select("*").execute()
    return {
       "status": "success",
       "data": data.data
    }

# -----------------------
# GET MAHASISWA{ID}
# -----------------------
@app.get("/mahasiswa/{mahasiswa_id}")
def get_mahasiswa_by_id(mahasiswa_id: str):

    data = supabase.table("mahasiswa") \
        .select("*") \
        .eq("mahasiswa_id", mahasiswa_id) \
        .execute()

    if not data.data:
        return {
            "error": "Mahasiswa tidak ditemukan"
        }

    return data.data[0]

# -----------------------
# POST KRS
# -----------------------
@app.post("/krs")
def create_krs(
    mahasiswa_id: str,
    semester: int,
    kode_matkul: str,
    nama_matkul: str,
    nama_dosen: str,
    payload: dict = Depends(
        require_role(["mahasiswa", "admin"])
    )
):

    # validasi mahasiswa ada
    cek = supabase.table("mahasiswa") \
        .select("*") \
        .eq("mahasiswa_id", mahasiswa_id) \
        .execute()

    if not cek.data:
        return {"error": "Mahasiswa tidak ditemukan"}

    data = supabase.table("krs").insert({
        "mahasiswa_id": mahasiswa_id,
        "semester": semester,
        "kode_matkul": kode_matkul,
        "nama_matkul": nama_matkul,
        "nama_dosen": nama_dosen
    }).execute()

    return {"status": "success", "data": data.data}

# -----------------------
# POST NILAI
# -----------------------
@app.post("/nilai")
def input_nilai(
    mahasiswa_id: str,
    kode_matkul: str,
    komponen: str,
    nilai: float,
    payload: dict = Depends(
        require_role(["dosen", "admin"])
    )
):

    cek = supabase.table("mahasiswa") \
        .select("*") \
        .eq("mahasiswa_id", mahasiswa_id) \
        .execute()

    if not cek.data:
        return {"error": "Mahasiswa tidak ditemukan"}

    data = supabase.table("nilai").insert({
        "mahasiswa_id": mahasiswa_id,
        "kode_matkul": kode_matkul,
        "komponen": komponen,
        "nilai": nilai
    }).execute()

    return {"status": "success", "data": data.data}

# -----------------------
# POST PRESENSI
# -----------------------
@app.post("/presensi")
def input_presensi(
    mahasiswa_id: str,
    kode_matkul: str,
    pertemuan: int,
    status_hadir: str,
    payload: dict = Depends(
        require_role(["dosen", "admin"])
    )
):

    data = supabase.table("presensi").insert({
        "mahasiswa_id": mahasiswa_id,
        "kode_matkul": kode_matkul,
        "pertemuan": pertemuan,
        "status_hadir": status_hadir
    }).execute()

    return {
        "status": "success",
        "data": data.data
    }    

# -----------------------
# GET PRESENSI
# -----------------------
@app.get("/presensi")
def get_presensi(kode_matkul: str):

    data = supabase.table("presensi") \
        .select("*") \
        .eq("kode_matkul", kode_matkul) \
        .execute()

    return {
        "kode_matkul": kode_matkul,
        "data": data.data
    }

# -----------------------
# POST PEMBAYARAN
# -----------------------
@app.post("/pembayaran")
def pembayaran(
    mahasiswa_id: str,
    semester: int,
    jumlah: float,
    metode: str,
    payload: dict = Depends(
        require_role(["keuangan", "admin"])
    )
):

    cek = supabase.table("mahasiswa") \
        .select("*") \
        .eq("mahasiswa_id", mahasiswa_id) \
        .execute()

    if not cek.data:
        return {"error": "Mahasiswa tidak ditemukan"}

    data = supabase.table("pembayaran").insert({
        "mahasiswa_id": mahasiswa_id,
        "semester": semester,
        "jumlah": jumlah,
        "metode": metode,
        "status": "PAID"
    }).execute()

    return {"status": "success", "data": data.data}

# -----------------------
# GET TAGIHAN
# -----------------------
@app.get("/tagihan")
def get_tagihan(
    mahasiswa_id: str,
    payload: dict = Depends(require_role(["keuangan", "admin"]))
):
    data = supabase.table("pembayaran") \
        .select("*") \
        .eq("mahasiswa_id", mahasiswa_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not data.data:
        return {
            "status": "not_found",
            "message": "Data tagihan tidak ditemukan"
        }

    tagihan = data.data[0]

    return {
        "mahasiswa_id": tagihan["mahasiswa_id"],
        "total_tagihan": tagihan["jumlah"],
        "status_pembayaran": tagihan["status"],
        "keterangan": (
            "Tagihan sudah lunas"
            if tagihan["status"] == "PAID"
            else "Tagihan belum dibayar"
        )
    }