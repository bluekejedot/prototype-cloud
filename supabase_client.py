from supabase import create_client


SUPABASE_URL = "https://ximofkofzzpwucoyszdm.supabase.co" #link supabase project
SUPABASE_KEY = "sb_publishable_cdi0yNMdE_mX3mvTIjsfjA_uGBDPMtw" #public key project supabasenya

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)