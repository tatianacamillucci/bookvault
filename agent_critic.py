import os
import json
import time
import googlemaps
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAZIONE ---
load_dotenv()

# Recupera le chiavi
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GMAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Controlli di sicurezza
if not all([SUPABASE_URL, SUPABASE_KEY, GMAPS_KEY, GEMINI_KEY]):
    raise ValueError("❌ Manca una delle chiavi nel file .env (Controlla GEMINI_API_KEY, GMAPS_KEY, SUPABASE_URL/KEY)")

# Inizializza i Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
gmaps = googlemaps.Client(key=GMAPS_KEY)
genai.configure(api_key=GEMINI_KEY)

def get_place_details(place_id):
    """Scarica recensioni e orari da Google Maps"""
    try:
        # Chiediamo solo i campi che ci servono (risparmiamo banda)
        details = gmaps.place(
            place_id=place_id, 
            fields=['name', 'rating', 'reviews', 'opening_hours', 'website']
        )
        return details.get('result', {})
    except Exception as e:
        print(f"⚠️ Errore Google Maps per {place_id}: {e}")
        return None

def analyze_with_ai(place_name, place_data):
    """Chiede a Gemini di giudicare il posto"""
    
    # Mettiamo insieme le ultime 5 recensioni
    reviews_text = ""
    if 'reviews' in place_data:
        for r in place_data['reviews'][:5]: 
            reviews_text += f"- {r['text']}\n"
            
    # Il Prompt per l'AI
    prompt = f"""
    Sei un analista per l'app BookVault. Valuta questo luogo: "{place_name}".
    
    DATI:
    Rating Google: {place_data.get('rating', 'N/A')}
    Recensioni Utenti:
    {reviews_text}
    
    COMPITO:
    Analizza il testo per capire se è un buon posto per studiare, lavorare o leggere.
    Sii onesto e critico. Se le recensioni dicono che è rumoroso, segnalalo.
    
    Rispondi ESCLUSIVAMENTE con un JSON valido con questa struttura esatta:
    {{
        "studability_score": (numero intero 0-10, sii severo),
        "noise_avg": (scegli solo tra: "silent", "quiet", "moderate", "noisy"),
        "has_wifi": (booleano true/false basato sulle recensioni o dedotto),
        "has_plugs": (booleano true/false),
        "comfy_seats": (booleano true/false),
        "good_coffee": (booleano true/false),
        "cheap_eats": (booleano true/false),
        "ai_summary": (una frase riassuntiva in italiano, max 15 parole)
    }}
    """
    
    try:
        # Usiamo Gemini Flash perché è veloce ed economico
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Puliamo la risposta per essere sicuri che sia JSON puro
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"💀 Errore AI su {place_name}: {e}")
        return None

def run_critic():
    print("🧠 CRITIC: Inizio il turno. Cerco posti non ancora valutati...")
    
    # 1. CERCA I POSTI VUOTI
    # Seleziona tutti i posti dove 'studability_score' è ancora NULL (vuoto)
    response = supabase.table("reading_points")\
        .select("*")\
        .is_("studability_score", "null")\
        .execute()
    
    places_to_review = response.data
    
    if not places_to_review:
        print("✅ Nessun posto nuovo da recensire. Tutto aggiornato!")
        return

    print(f"📝 Trovati {len(places_to_review)} posti da analizzare. Inizio lavoro...\n")

    count = 0
    for place in places_to_review:
        print(f"[{count+1}/{len(places_to_review)}] 👉 Analizzo: {place['name']}...")
        
        # 2. Ottieni dettagli da Google
        details = get_place_details(place['google_place_id'])
        if not details:
            print("   -> Saltato (dettagli non trovati)")
            continue
            
        # 3. Chiedi all'AI
        ai_verdict = analyze_with_ai(place['name'], details)
        
        if ai_verdict:
            # 4. Salva il verdetto su Supabase
            try:
                supabase.table("reading_points").update(ai_verdict).eq("id", place['id']).execute()
                print(f"   ⭐ Voto: {ai_verdict['studability_score']}/10 - {ai_verdict['noise_avg']}")
                print(f"   💬 {ai_verdict['ai_summary']}")
                print("   💾 Salvato!")
            except Exception as e:
                print(f"   ❌ Errore salvataggio DB: {e}")
        
        count += 1
        # Pausa etica per non spammare (1 secondo)
        time.sleep(1)

if __name__ == "__main__":
    run_critic()