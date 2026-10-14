import os
import sys
import time
import googlemaps
from dotenv import load_dotenv
from supabase import create_client, Client

# Carica le chiavi
load_dotenv()

class AgentScout:
    def __init__(self):
        gmaps_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not gmaps_key:
            raise ValueError("Manca GOOGLE_MAPS_API_KEY!")
        self.gmaps = googlemaps.Client(key=gmaps_key)
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Manca SUPABASE_URL o KEY!")
        self.supabase: Client = create_client(url, key)

    def determine_type(self, gmaps_types):
        if 'library' in gmaps_types:
            return 'library'
        elif 'book_store' in gmaps_types:
            return 'book_store'
        elif 'cafe' in gmaps_types:
            return 'cafe'
        return 'other'

    def fetch_all_pages(self, location, radius, type=None, keyword=None):
        """
        Scarica TUTTE le pagine di risultati (fino a 60 per categoria), 
        non solo i primi 20.
        """
        all_results = []
        
        # 1. Prima chiamata
        print(f"   ...Chiamo Google (Pagina 1) per {type or keyword}...")
        response = self.gmaps.places_nearby(
            location=location, 
            radius=radius, 
            type=type, 
            keyword=keyword
        )
        results = response.get('results', [])
        all_results.extend(results)
        
        # 2. Controlla se c'è una "Next Page"
        next_token = response.get('next_page_token')
        
        while next_token:
            print("   ...Trovata altra pagina! Attendo 2 secondi (regola Google)...")
            time.sleep(2) # OBBLIGATORIO: Google richiede una pausa
            
            try:
                response = self.gmaps.places_nearby(
                    page_token=next_token
                )
                results = response.get('results', [])
                all_results.extend(results)
                next_token = response.get('next_page_token')
            except Exception as e:
                print(f"⚠️ Errore paginazione: {e}")
                break
                
        return all_results

    def save_place(self, place):
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']
        place_type = self.determine_type(place.get('types', []))
        
        data = {
            "google_place_id": place['place_id'],
            "name": place['name'],
            "address": place.get('vicinity', ''),
            "type": place_type,
            "location": f"POINT({lng} {lat})"
        }

        try:
            self.supabase.table("reading_points").upsert(
                data, on_conflict="google_place_id"
            ).execute()
            # Stampa un puntino per non intasare la console, fa molto "hacker"
            print(".", end="", flush=True) 
        except Exception as e:
            print(f"x", end="", flush=True)

    def run_mission(self, lat, lng, radius=2000):
        print(f"🕵️ SCOUT MAX: Nuova missione a coordinate {lat}, {lng} (Raggio: {radius}m)...")
        
        # Cerchiamo con la paginazione
        places_books = self.fetch_all_pages((lat, lng), radius, type='book_store')
        places_libs = self.fetch_all_pages((lat, lng), radius, type='library')
        places_cafes = self.fetch_all_pages((lat, lng), radius, type='cafe', keyword='study')

        # Uniamo tutto
        all_raw = places_books + places_libs + places_cafes
        
        # Deduplica
        unique_places = {p['place_id']: p for p in all_raw}.values()
        
        print(f"\n✅ Trovati {len(unique_places)} luoghi unici (prima erano limitati a ~60).")
        print("Inizio salvataggio rapido:", end=" ")
        
        count = 0
        for p in unique_places:
            self.save_place(p)
            count += 1
            
        print(f"\n🏁 Missione completata. Database aggiornato con {count} luoghi.")

if __name__ == "__main__":
    # Default: Bologna
    user_lat = 44.4938
    user_lng = 11.3426
    
    # Se passi coordinate da terminale
    if len(sys.argv) == 3:
        user_lat = float(sys.argv[1])
        user_lng = float(sys.argv[2])
    
    scout = AgentScout()
    scout.run_mission(user_lat, user_lng, radius=2000)