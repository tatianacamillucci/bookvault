import os
import sys
from dotenv import load_dotenv

# 1. Carica le variabili d'ambiente (API Keys)
load_dotenv()

def check_setup():
    print("🤖 BOOKVAULT BRAIN: System Check")
    print("--------------------------------")
    
    # Controlliamo se le chiavi esistono
    keys = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        # Useremo Gemini perché è gratis per gli studenti, OpenAI è a pagamento
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"), 
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY")
    }
    
    all_good = True
    for name, value in keys.items():
        if value:
            print(f"✅ {name}: Trovata")
        else:
            print(f"❌ {name}: MANCANTE!")
            all_good = False
            
    if all_good:
        print("\n🚀 Tutto pronto! Possiamo lanciare gli Agenti.")
    else:
        print("\n⚠️  Attenzione: Crea un file .env e inserisci le chiavi mancanti.")

if __name__ == "__main__":
    check_setup()