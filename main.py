import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase_client import supabase
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC

app = FastAPI(
    title="Sistem Akademik Cloud Kampus XYZ",
    description="Prototype Sandbox API berbasis Cloud untuk Proof of Concept",
    version="1.0.0"
)

SECRET_KEY = os.getenv("SECRET_KEY", "cloud-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
security = HTTPBearer()

# ----------------------------------------------------------------------
# PYDANTIC SCHEMAS (Memastikan Request berupa JSON Body di Swagger)
# ----------------------------------------------------------------------
class KRSInput(BaseModel):
    mahasiswa_id: str
    semester: int
    kode_matkul: str
    nama_matkul: str
    nama_dosen: str

class NilaiInput(BaseModel):
    mahasiswa_id: str
    kode_matkul: str
    komponen: str
    nilai: float

class PresensiInput(BaseModel):
    mahasiswa_id: str
    kode_matkul: str
    pertemuan: int
    status_hadir: str

class PembayaranInput(BaseModel):
    mahasiswa_id: str
    semester: int
    jumlah: float
    metode: str

# ----------------------------------------------------------------------
# JWT & CORE SECURITY FUNCTIONS
# ----------------------------------------------------------------------
def create_access_token(user_data: dict):
    payload = {
        "sub": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.now(UTC) + timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau telah kedaluwarsa"
        )

def require_role(allowed_roles: list):
    def role_checker(payload: dict = Depends(verify_token)):
        if payload["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak: Role Anda tidak memiliki otoritas"
            )
        return payload
    return role_checker

# ----------------------------------------------------------------------
# ENDPOINTS IMPLEMENTATION
# ----------------------------------------------------------------------

@app.get("/me", tags=["Authentication"])
def get_me(payload: dict = Depends(verify_token)):
    return {"email": payload["sub"], "role": payload["role"]}

@app.post("/login", tags=["Authentication"])
def login(email: str, password: str):
    user = supabase.table("users").select("*").eq("email", email).execute()
    
    if len(user.data) == 0:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan")

    db_password = user.data[0]["password_hash"]
    if db_password.strip() != password.strip():
        raise HTTPException(status_code=401, detail="Password salah")

    token = create_access_token({
        "email": user.data[0]["email"],
        "role": user.data[0]["role"]
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.data[0]["role"]
    }

@app.get("/mahasiswa", tags=["Mahasiswa API"])
def get_mahasiswa(payload: dict = Depends(verify_token)):
    data = supabase.table("mahasiswa").select("*").execute()
    return {"status": "success", "data": data.data}

@app.get("/mahasiswa/{mahasiswa_id}", tags=["Mahasiswa API"])
def get_mahasiswa_by_id(mahasiswa_id: str, payload: dict = Depends(verify_token)):
    data = supabase.table("mahasiswa").select("*").eq("mahasiswa_id", mahasiswa_id).execute()
    if not data.data:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")
    return data.data[0]

@app.post("/krs", status_code=status.HTTP_201_CREATED, tags=["Mahasiswa API"])
def create_krs(body: KRSInput, payload: dict = Depends(require_role(["mahasiswa", "admin"]))):
    # Validasi keberadaan mahasiswa
    cek = supabase.table("mahasiswa").select("*").eq("mahasiswa_id", body.mahasiswa_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    data = supabase.table("krs").insert(body.model_dump()).execute()
    return {"status": "success", "message": "KRS berhasil diajukan", "data": data.data}

@app.post("/nilai", status_code=status.HTTP_201_CREATED, tags=["Dosen API"])
def input_nilai(body: NilaiInput, payload: dict = Depends(require_role(["dosen", "admin"]))):
    cek = supabase.table("mahasiswa").select("*").eq("mahasiswa_id", body.mahasiswa_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    data = supabase.table("nilai").insert(body.model_dump()).execute()
    return {"status": "success", "message": "Nilai akademik berhasil diinput", "data": data.data}

@app.post("/presensi", status_code=status.HTTP_201_CREATED, tags=["Dosen API"])
def input_presensi(body: PresensiInput, payload: dict = Depends(require_role(["dosen", "admin"]))):
    data = supabase.table("presensi").insert(body.model_dump()).execute()
    return {"status": "success", "message": "Data presensi berhasil dicatat", "data": data.data}

@app.get("/presensi", tags=["Dosen API"])
def get_presensi(kode_matkul: str, payload: dict = Depends(verify_token)):
    data = supabase.table("presensi").select("*").eq("kode_matkul", kode_matkul).execute()
    return {"kode_matkul": kode_matkul, "data": data.data}

@app.post("/pembayaran", status_code=status.HTTP_201_CREATED, tags=["Keuangan API"])
def pembayaran(body: PembayaranInput, payload: dict = Depends(require_role(["keuangan", "admin"]))):
    cek = supabase.table("mahasiswa").select("*").eq("mahasiswa_id", body.body.mahasiswa_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    insert_data = body.model_dump()
    insert_data["status"] = "PAID"
    
    data = supabase.table("pembayaran").insert(insert_data).execute()
    return {"status": "success", "message": "Pembayaran UKT berhasil diverifikasi", "data": data.data}

@app.get("/tagihan", tags=["Keuangan API"])
def get_tagihan(mahasiswa_id: str, payload: dict = Depends(require_role(["keuangan", "admin", "mahasiswa"]))):
    data = supabase.table("pembayaran") \
        .select("*") \
        .eq("mahasiswa_id", mahasiswa_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not data.data:
        raise HTTPException(status_code=404, detail="Data tagihan tidak ditemukan")

    tagihan = data.data[0]
    return {
        "mahasiswa_id": tagihan["mahasiswa_id"],
        "total_tagihan": tagihan["jumlah"],
        "status_pembayaran": tagihan["status"],
        "keterangan": "Tagihan sudah lunas" if tagihan["status"] == "PAID" else "Tagihan belum dibayar"
    }