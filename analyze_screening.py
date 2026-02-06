"""
Screening-Analyse: Welche Papers exkludieren?
"""
import pandas as pd

screening = pd.read_csv('docs/screening_results.csv')

# Exklusionskriterien basierend auf Keywords
def should_exclude(row):
    title = str(row['title']).lower() if pd.notna(row['title']) else ''
    keywords = str(row['keywords']).lower() if pd.notna(row['keywords']) else ''
    combined = title + ' ' + keywords
    
    # Andere Industrien (nicht Automotive)
    if any(x in combined for x in ['coal', 'mining', 'mineral', 'mine']):
        return 'EXKLUDIEREN', 'Andere Industrie (Bergbau)'
    if any(x in combined for x in ['welding', 'weld']):
        return 'EXKLUDIEREN', 'Andere Industrie (Schweissen)'
    if any(x in combined for x in ['power policy', 'smart grid', 'power grid']):
        return 'EXKLUDIEREN', 'Andere Industrie (Energie/Netz)'
    if 'construction engineering' in combined:
        return 'EXKLUDIEREN', 'Andere Industrie (Bauwesen)'
    
    # Medizin
    if any(x in combined for x in ['thyroid', 'clinical', 'patient', 'medical']):
        return 'EXKLUDIEREN', 'Andere Domaene (Medizin)'
    
    # Andere Domänen
    if 'biomimicry' in combined or 'biomimetics' in combined:
        return 'EXKLUDIEREN', 'Andere Domaene (Bionik)'
    if 'tourism' in combined:
        return 'EXKLUDIEREN', 'Andere Domaene (Tourismus)'
    
    # Zu generisch
    if 'delving into specialized genai' in combined:
        return 'EXKLUDIEREN', 'Zu allgemein'
    
    return 'INKLUDIEREN', ''

# Anwenden
results = screening.apply(should_exclude, axis=1, result_type='expand')
screening['Empfehlung'] = results[0]
screening['Grund'] = results[1]

# Exportieren
screening.to_csv('docs/screening_mit_empfehlungen.csv', index=False)

# Statistik
print(f"Gesamt: {len(screening)}")
print(f"INKLUDIEREN: {(screening['Empfehlung'] == 'INKLUDIEREN').sum()}")
print(f"EXKLUDIEREN: {(screening['Empfehlung'] == 'EXKLUDIEREN').sum()}")
print()
print("Exkludierte Papers:")
excluded = screening[screening['Empfehlung'] == 'EXKLUDIEREN']
for idx, row in excluded.iterrows():
    title_short = str(row['title'])[:70]
    print(f"  - {title_short}... -> {row['Grund']}")
