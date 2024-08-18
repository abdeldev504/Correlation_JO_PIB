# Installer les bibliothèques nécessaires
!pip install matplotlib seaborn pandas numpy pillow

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Lire les tableaux HTML depuis les pages Wikipedia
medals_url = "https://en.wikipedia.org/wiki/2024_Summer_Olympics_medal_table"
gdp_url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"

# Charger les données des médailles et du PIB
medals_df = pd.read_html(medals_url)[3]  # Sélection du tableau correct pour les médailles
gdp_df = pd.read_html(gdp_url)[2]        # Sélection du tableau correct pour le PIB

# Aplatir les colonnes du DataFrame du PIB
gdp_df.columns = ['_'.join(col).strip() for col in gdp_df.columns.values]

# Sélection des colonnes pertinentes pour le PIB
gdp_df = gdp_df[['Country/Territory_Country/Territory', 'IMF[1][13]_Forecast']]
gdp_df.columns = ['Pays', 'PIB']

# Ajouter manuellement le PIB de Cuba
cuba_gdp = pd.DataFrame({
    'Pays': ['Cuba'],
    'PIB': [147193]  # PIB de Cuba 
})
# Ajouter Cuba au DataFrame du PIB en utilisant pd.concat
gdp_df = pd.concat([gdp_df, cuba_gdp], ignore_index=True)



# Conversion des données en types numériques appropriés
medals_df['Rank'] = pd.to_numeric(medals_df['Rank'], errors='coerce')
gdp_df['Pays'] = gdp_df['Pays'].astype(str)

# Gestion des pays manquants (avec 0 médailles)
medals_countries = set(medals_df['NOC'])
gdp_countries = set(gdp_df['Pays'])
missing_countries = gdp_countries - medals_countries

# Création d'un DataFrame pour les pays manquants
max_rank = medals_df['Rank'].max()
missing_df = pd.DataFrame({
    'NOC': list(missing_countries),
    'Rank': max_rank + 1, 
    'Gold': 0,
    'Silver': 0,
    'Bronze': 0,
    'Total': 0
})

# Ajout des pays manquants au DataFrame des médailles
medals_df_complete = pd.concat([medals_df, missing_df], ignore_index=True)
medals_df_complete.rename(columns={'NOC': 'Pays'}, inplace=True)

# Correction des noms de pays
corrections = {
    'Great Britain': 'United Kingdom',
    'France*': 'France',
    'Chinese Taipei': 'Taiwan'
}
medals_df_complete['Pays'] = medals_df_complete['Pays'].replace(corrections)

# Fusion des données sur les pays
merged_df = pd.merge(medals_df_complete, gdp_df, on='Pays', how='inner')


# Conversion des colonnes en types numériques
merged_df['PIB'] = pd.to_numeric(merged_df['PIB'], errors='coerce')
merged_df['Total'] = pd.to_numeric(merged_df['Total'], errors='coerce')

# Suppression des lignes avec des valeurs manquantes
merged_df = merged_df.dropna(subset=['PIB', 'Total'])

# Exclusion de "World"
merged_df = merged_df[merged_df['Pays'] != 'World'].reset_index(drop=True)

# Calcul des rangs pour les médailles et le PIB
merged_df['Medals Rank Total'] = merged_df['Total'].rank(ascending=False)
merged_df['GDP Rank'] = merged_df['PIB'].rank(ascending=False)

# Chargement du fichier CSV des codes ISO
iso_csv_path = "/content/wikipedia-iso-country-codes.csv"  
iso_df = pd.read_csv(iso_csv_path)
iso_dict = pd.Series(iso_df['Alpha-2 code'].str.lower().values, index=iso_df['English short name lower case']).to_dict()

# Ajout de la colonne 'ISO_Code' à merged_df en utilisant le mappage
merged_df['ISO_Code'] = merged_df['Pays'].map(iso_dict)

# Ajout manuel des codes ISO manquants
iso_codes = {
    'Hong Kong': 'hk',
    'Ivory Coast': 'ci',
    'Dr Congo': 'cd',
    'Macau': 'mo',
    'Libya': 'ly',
    'Bosnia And Herzegovina': 'ba',
    'Trinidad And Tobago': 'tt',
    'Palestine': 'ps',
    'Moldova': 'md',
    'North Macedonia': 'mk',
    'Brunei': 'bn',
    'Congo': 'cg',
    'Laos': 'la',
    'North Korea': 'kp',
    'Namibia': 'na',
    'Kosovo': 'xk',
    'Syria': 'sy',
    'South Sudan': 'ss',
    'Eswatini': 'sz',
    'Curaçao': 'cw',
    'Zanzibar': 'tz',
    'Antigua And Barbuda': 'ag',
    'East Timor': 'tl',
    'Sint Maarten': 'sx',
    'Turks And Caicos Islands': 'tc',
    'Saint Kitts And Nevis': 'kn',
    'Saint Vincent And The Grenadines': 'vc',
    'São Tomé And Príncipe': 'st',
    'Micronesia': 'fm'
}

# Mise à jour des codes ISO dans merged_df
for country, iso_code in iso_codes.items():
    merged_df.loc[merged_df['Pays'] == country, 'ISO_Code'] = iso_code

# Exclusion de la Russie
merged_df = merged_df[merged_df['ISO_Code'] != 'ru']

# Filtrage des données pour exclure les erreurs (France et Royaume-Uni)
filtered_df = merged_df[~(((merged_df['Pays'] == 'France') & (merged_df['Total'] == 0)) |
                          ((merged_df['Pays'] == 'United Kingdom') & (merged_df['Total'] == 0)) |
                          ((merged_df['Pays'] == 'Taiwan') & (merged_df['Total'] == 0)))]

# Filtrage pour exclure les pays sans code ISO
filtered_df = filtered_df.dropna(subset=['ISO_Code'])

import matplotlib.image as mpimg

# Initialisation du graphique
fig, ax = plt.subplots(figsize=(12, 8))

# Tracé des points pour chaque pays
for idx, row in filtered_df.iterrows():
    img_path = f"/content/{row['ISO_Code']}.png"  # Chemin d'accès aux drapeaux
    try:
        img = mpimg.imread(img_path)
        imagebox = OffsetImage(img, zoom=1.1)  # Ajustement du zoom selon la taille souhaitée
        ab = AnnotationBbox(imagebox, (row['GDP Rank'], row['Rank']), frameon=False)
        ax.add_artist(ab)
    except FileNotFoundError:
        print(f"Drapeau introuvable pour {row['Pays']} au chemin {img_path}")

# Définir les limites de l'axe des ordonnées pour afficher tous les rangs
min_rank = filtered_df['Rank'].min()
max_rank = filtered_df['Rank'].max()
ax.set_ylim(max_rank + 5, min_rank - 5)

# Tracer la courbe de régression
sns.regplot(data=filtered_df, x='GDP Rank', y='Rank', scatter=False, color='black', line_kws={"linewidth": 1.5}, ax=ax)

# Configurer les axes
ax.set_xlabel("Rang du PIB")
ax.set_ylabel("Rang des Médailles")
ax.set_title("Corrélation entre le Rang du PIB et le Rang des Médailles Olympiques")

# Définir les limites de l'axe des abscisses pour afficher toutes les valeurs de GDP Rank
ax.set_xlim(filtered_df['GDP Rank'].min() - 5, filtered_df['GDP Rank'].max() + 5)

# Inverser l'axe des abscisses
ax.invert_xaxis()

# Ajouter une légende pour la courbe de régression
plt.legend(['Ligne de Régression'], loc='upper left')

# Ajouter une grille légère pour faciliter la lecture
ax.grid(True, linestyle='--', alpha=0.7)

# Ajouter un fond coloré au graphique
ax.set_facecolor('#f0f0f0')

plt.show()
