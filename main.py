from supabase import create_client, Client

url = "https://ximofkofzzpwucoyszdm.supabase.co"
key = "sb_publishable_cdi0yNMdE_mX3mvTIjsfjA_uGBDPMtw"

supabase: Client = create_client(url, key)

# Insert data contoh
data = supabase.table("logs").insert({
    "message": "Hello from cloud project"
}).execute()

print(data)