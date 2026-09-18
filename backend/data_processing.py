"""
Télécharge et traite les vraies données climatologiques mensuelles de Météo-France.

Produit dans /data :
  - normales_climat.csv        : normale 1991-2020 par département et mois (4 métriques)
  - observations_mensuelles.csv : observations 2018-2026 par département, mois, année
  - anomalies.json             : anomalies pré-calculées (observation - normale)
  - departements.json          : liste des départements disponibles

Source : Météo-France, données climatologiques de base mensuelles (Licence Ouverte 2.0).
Les fichiers bruts sont mis en cache dans data/raw/ (cf. .gitignore).

Métriques extraites :
  - TM  : température moyenne (°C)
  - RR  : cumul mensuel des précipitations (mm)
  - FFM : vitesse moyenne du vent à 10 m (m/s)
  - INST : durée d'insolation (minutes → convertie en heures)
"""

import gzip
import json
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Dossier du frontend servi en statique (GitHub Pages).
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DATA_DIR = FRONTEND_DIR / "data"
FRONTEND_DEPARTEMENTS_DIR = FRONTEND_DATA_DIR / "departements"

# Base URL des fichiers mensuels Météo-France sur le S3 OVH.
# Deux fenêtres temporelles :
#   - previous : archive figée 1950-2024 (toutes stations, dont fermées)
#   - latest   : 2 dernières années, stations actives uniquement, mise à jour quotidienne
MENS_URL_PREVIOUS = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net"
    "/data/synchro_ftp/BASE/MENS/MENSQ_{code}_previous-1950-2024.csv.gz"
)
MENS_URL_LATEST = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net"
    "/data/synchro_ftp/BASE/MENS/MENSQ_{code}_latest-2025-2026.csv.gz"
)

# Codes de départements à télécharger (01-95, 20 pour la Corse, 971-975).
# Mayotte (976) n'a pas de fichier mensuel Météo-France.
CODES_FICHIER = (
    [f"{n:02d}" for n in range(1, 96)]
    + [f"{n:03d}" for n in range(971, 976)]
)

# Noms et codes des départements du projet (correspondance code fichier → nom).
# La Corse (fichier 20) est splitée en 2A (sud, LAT < 42.35°) et 2B (nord).
DEPARTEMENTS_NOMS = {
    "01": ("Ain", "01"), "02": ("Aisne", "02"), "03": ("Allier", "03"),
    "04": ("Alpes-de-Haute-Provence", "04"), "05": ("Hautes-Alpes", "05"),
    "06": ("Alpes-Maritimes", "06"), "07": ("Ardèche", "07"), "08": ("Ardennes", "08"),
    "09": ("Ariège", "09"), "10": ("Aube", "10"), "11": ("Aude", "11"),
    "12": ("Aveyron", "12"), "13": ("Bouches-du-Rhône", "13"), "14": ("Calvados", "14"),
    "15": ("Cantal", "15"), "16": ("Charente", "16"), "17": ("Charente-Maritime", "17"),
    "18": ("Cher", "18"), "19": ("Corrèze", "19"),
    "20": ("Corse", "20"),  # split 2A/2B par latitude
    "21": ("Côte-d'Or", "21"), "22": ("Côtes-d'Armor", "22"), "23": ("Creuse", "23"),
    "24": ("Dordogne", "24"), "25": ("Doubs", "25"), "26": ("Drôme", "26"),
    "27": ("Eure", "27"), "28": ("Eure-et-Loir", "28"), "29": ("Finistère", "29"),
    "30": ("Gard", "30"), "31": ("Haute-Garonne", "31"), "32": ("Gers", "32"),
    "33": ("Gironde", "33"), "34": ("Hérault", "34"), "35": ("Ille-et-Vilaine", "35"),
    "36": ("Indre", "36"), "37": ("Indre-et-Loire", "37"), "38": ("Isère", "38"),
    "39": ("Jura", "39"), "40": ("Landes", "40"), "41": ("Loir-et-Cher", "41"),
    "42": ("Loire", "42"), "43": ("Haute-Loire", "43"), "44": ("Loire-Atlantique", "44"),
    "45": ("Loiret", "45"), "46": ("Lot", "46"), "47": ("Lot-et-Garonne", "47"),
    "48": ("Lozère", "48"), "49": ("Maine-et-Loire", "49"), "50": ("Manche", "50"),
    "51": ("Marne", "51"), "52": ("Haute-Marne", "52"), "53": ("Mayenne", "53"),
    "54": ("Meurthe-et-Moselle", "54"), "55": ("Meuse", "55"), "56": ("Morbihan", "56"),
    "57": ("Moselle", "57"), "58": ("Nièvre", "58"), "59": ("Nord", "59"),
    "60": ("Oise", "60"), "61": ("Orne", "61"), "62": ("Pas-de-Calais", "62"),
    "63": ("Puy-de-Dôme", "63"), "64": ("Pyrénées-Atlantiques", "64"),
    "65": ("Hautes-Pyrénées", "65"), "66": ("Pyrénées-Orientales", "66"),
    "67": ("Bas-Rhin", "67"), "68": ("Haut-Rhin", "68"), "69": ("Rhône", "69"),
    "70": ("Haute-Saône", "70"), "71": ("Saône-et-Loire", "71"), "72": ("Sarthe", "72"),
    "73": ("Savoie", "73"), "74": ("Haute-Savoie", "74"), "75": ("Paris", "75"),
    "76": ("Seine-Maritime", "76"), "77": ("Seine-et-Marne", "77"), "78": ("Yvelines", "78"),
    "79": ("Deux-Sèvres", "79"), "80": ("Somme", "80"), "81": ("Tarn", "81"),
    "82": ("Tarn-et-Garonne", "82"), "83": ("Var", "83"), "84": ("Vaucluse", "84"),
    "85": ("Vendée", "85"), "86": ("Vienne", "86"), "87": ("Haute-Vienne", "87"),
    "88": ("Vosges", "88"), "89": ("Yonne", "89"), "90": ("Territoire de Belfort", "90"),
    "91": ("Essonne", "91"), "92": ("Hauts-de-Seine", "92"),
    "93": ("Seine-Saint-Denis", "93"), "94": ("Val-de-Marne", "94"),
    "95": ("Val-d'Oise", "95"),
    "971": ("Guadeloupe", "971"), "972": ("Martinique", "972"),
    "973": ("Guyane", "973"), "974": ("La Réunion", "974"),
    "975": ("Saint-Pierre-et-Miquelon", "975"),
}

# Seuil de latitude (en degrés) pour séparer Corse-du-Sud (2A) et Haute-Corse (2B).
CORS_SEUIL_LAT = 42.35

# Codes officiels des départements corses (non présents dans DEPARTEMENTS_NOMS
# car le fichier Météo-France utilise le code 20 pour la Corse entière).
CODES_CORSE = {"Corse-du-Sud": "2A", "Haute-Corse": "2B"}

# Colonnes à extraire et leur renommage.
COLONNES = {
    "NUM_POSTE": "num_poste",
    "NOM_USUEL": "nom_usuel",
    "LAT": "lat",
    "LON": "lon",
    "AAAAMM": "aaaamm",
    "TM": "temperature",
    "QTM": "q_temperature",
    "RR": "precipitation",
    "QRR": "q_precipitation",
    "FFM": "vent",
    "QFFM": "q_vent",
    "INST": "ensoleillement_min",
    "QINST": "q_ensoleillement",
}

# Codes qualité acceptés (0=validé, 1=validé auto, 9=filtré). On exclut 2 (douteux) et vide.
QCODES_VALIDES = {"0", "1", "9"}

PERIODE_NORMALE = (1991, 2020)
PERIODE_OBSERVATION = (2018, 2026)

METRIQUES = ["temperature", "precipitation", "vent", "ensoleillement"]


def telecharger_fichier(code: str, fenetre: str = "previous", force: bool = False) -> Path | None:
    """Télécharge le fichier mensuel d'un département si absent du cache.

    Args:
        code: code département (ex : "01", "971").
        fenetre: "previous" (archive 1950-2024) ou "latest" (2025-2026, récent).
        force: si True, retélécharge même si le fichier est déjà en cache.
    """
    suffixe = "previous-1950-2024" if fenetre == "previous" else "latest-2025-2026"
    chemin = RAW_DIR / f"MENSQ_{code}_{suffixe}.csv.gz"
    if chemin.exists() and not force:
        return chemin
    url = MENS_URL_PREVIOUS if fenetre == "previous" else MENS_URL_LATEST
    try:
        resp = requests.get(url.format(code=code), timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ! Téléchargement échoué pour {code} ({fenetre}) : {e}")
        return None
    chemin.write_bytes(resp.content)
    return chemin


def code_qualite_valide(val) -> bool:
    """Vérifie qu'un code qualité est valide (non douteux)."""
    if pd.isna(val) or val == "":
        return False
    try:
        return str(int(float(val))) in QCODES_VALIDES
    except (ValueError, TypeError):
        return False


def parser_fichier(chemin: Path, code_fichier: str) -> pd.DataFrame:
    """Parse un fichier CSV gzippé et retourne un DataFrame filtré."""
    with gzip.open(chemin, "rt", encoding="utf-8", errors="replace") as f:
        df = pd.read_csv(f, sep=";", dtype=str, low_memory=False)

    # Garder uniquement les colonnes d'intérêt
    cols_presentes = [c for c in COLONNES if c in df.columns]
    df = df[cols_presentes].rename(
        columns={k: v for k, v in COLONNES.items() if k in cols_presentes}
    )

    # Extraire année et mois depuis AAAAMM
    df["aaaamm"] = df["aaaamm"].astype(str).str.zfill(6)
    df["annee"] = pd.to_numeric(df["aaaamm"].str[:4], errors="coerce")
    df["mois"] = pd.to_numeric(df["aaaamm"].str[4:6], errors="coerce")
    df = df.dropna(subset=["annee", "mois"])
    df["annee"] = df["annee"].astype(int)
    df["mois"] = df["mois"].astype(int)

    # Filtrer sur la période utile (1991-2026)
    df = df[(df["annee"] >= 1991) & (df["annee"] <= 2026)]

    # Latitude : Météo-France utilise des millionièmes de degré, négatifs au sud.
    # La Corse est au nord (positive). On prend la valeur absolue pour le seuil.
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce").abs()

    # Convertir les métriques en numérique et filtrer par code qualité
    paires_q = [
        ("temperature", "q_temperature"),
        ("precipitation", "q_precipitation"),
        ("vent", "q_vent"),
        ("ensoleillement_min", "q_ensoleillement"),
    ]
    for col, qcol in paires_q:
        if col not in df.columns:
            df[col] = pd.NA
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if qcol in df.columns:
            masque = df[qcol].apply(code_qualite_valide)
            df[col] = df[col].where(masque)

    # Convertir l'insolation de minutes en heures
    df["ensoleillement"] = pd.to_numeric(df["ensoleillement_min"], errors="coerce") / 60.0
    df = df.drop(columns=["ensoleillement_min"], errors="ignore")

    # Assigner le nom de département (split Corse)
    if code_fichier == "20":
        df["departement"] = df["lat"].apply(
            lambda lat: "Corse-du-Sud" if pd.notna(lat) and lat < CORS_SEUIL_LAT
            else "Haute-Corse"
        )
    else:
        nom, _ = DEPARTEMENTS_NOMS[code_fichier]
        df["departement"] = nom

    return df


def generer_donnees_statiques(depts_list: list[dict], anomalies: list[dict]) -> None:
    """Génère les fichiers de données statiques pour le frontend (site statique).

    Produit dans frontend/data :
      - departements.json          : liste des départements (copie de data/departements.json)
      - departements/<code>.json   : anomalies d'un département (série 2018-2026)

    Args:
        depts_list: liste des départements (nom, code).
        anomalies: liste complète des anomalies (tous départements confondus).
    """
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DEPARTEMENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Liste des départements pour le frontend
    (FRONTEND_DATA_DIR / "departements.json").write_text(
        json.dumps(depts_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Index nom → code pour le découpage par département
    code_par_nom = {d["nom"]: d["code"] for d in depts_list}

    # Regrouper les anomalies par département
    par_departement: dict[str, list[dict]] = {}
    for a in anomalies:
        par_departement.setdefault(a["departement"], []).append(a)

    nb = 0
    for nom, serie in par_departement.items():
        code = code_par_nom.get(nom, nom)
        chemin = FRONTEND_DEPARTEMENTS_DIR / f"{code}.json"
        chemin.write_text(
            json.dumps(serie, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        nb += 1

    print(f"  {nb} fichiers départementaux écrits dans frontend/data/departements/\n")


def main() -> None:
    print("=== FranceClimate — Pipeline de données réelles Météo-France ===\n")

    # 1. Télécharger les fichiers (previous + latest)
    print(f"Téléchargement des fichiers mensuels (cache : {RAW_DIR})")
    chemins = {}
    for code in CODES_FICHIER:
        nom = DEPARTEMENTS_NOMS.get(code, ("?", code))[0]
        c_prev = telecharger_fichier(code, fenetre="previous")
        c_latest = telecharger_fichier(code, fenetre="latest")
        if c_prev is not None:
            chemins[code] = (c_prev, c_latest)
            detail = "previous"
            if c_latest is not None:
                detail += " + latest"
            print(f"  OK {code} ({nom}) [{detail}]")
        elif c_latest is not None:
            # latest only (rare : previous indisponible)
            chemins[code] = (None, c_latest)
            print(f"  OK {code} ({nom}) [latest seulement]")
    print(f"  {len(chemins)} fichiers disponibles\n")

    # 2-3. Parser et concaténer tous les fichiers (previous + latest)
    print("Parsing et agrégation des données par station…")
    frames = []
    for code, (c_prev, c_latest) in chemins.items():
        frames_code = []
        if c_prev is not None:
            df_prev = parser_fichier(c_prev, code)
            frames_code.append(df_prev)
        if c_latest is not None:
            df_latest = parser_fichier(c_latest, code)
            frames_code.append(df_latest)
        df = pd.concat(frames_code, ignore_index=True)
        frames.append(df)
        print(f"  {code} ({DEPARTEMENTS_NOMS[code][0]}): {len(df)} lignes")
    df_all = pd.concat(frames, ignore_index=True)
    print(f"  Total : {len(df_all)} lignes\n")

    # 4. Agréger par département × mois × année (moyenne des stations)
    print("Agrégation par département, mois, année…")
    df_agg = (
        df_all.groupby(["departement", "annee", "mois"])[METRIQUES]
        .mean()
        .reset_index()
    )
    for c in METRIQUES:
        df_agg[c] = df_agg[c].round(1)
    print(f"  {len(df_agg)} enregistrements agrégés\n")

    # 5. Calculer les normales 1991-2020 (moyenne par département × mois)
    print("Calcul des normales 1991-2020…")
    mask_norm = (df_agg["annee"] >= PERIODE_NORMALE[0]) & (df_agg["annee"] <= PERIODE_NORMALE[1])
    normales = (
        df_agg[mask_norm]
        .groupby(["departement", "mois"])[METRIQUES]
        .mean()
        .reset_index()
    )
    normales = normales.rename(columns={
        "temperature": "normale_temperature",
        "precipitation": "normale_precipitation",
        "vent": "normale_vent",
        "ensoleillement": "normale_ensoleillement",
    })
    for c in ["normale_temperature", "normale_precipitation", "normale_vent", "normale_ensoleillement"]:
        normales[c] = normales[c].round(1)
    normales.to_csv(DATA_DIR / "normales_climat.csv", index=False)
    print(f"  {len(normales)} normales écrites dans normales_climat.csv\n")

    # 6. Extraire les observations 2018-2024
    mask_obs = (df_agg["annee"] >= PERIODE_OBSERVATION[0]) & (df_agg["annee"] <= PERIODE_OBSERVATION[1])
    observations = df_agg[mask_obs].copy()
    observations.to_csv(DATA_DIR / "observations_mensuelles.csv", index=False)
    print(f"  {len(observations)} observations écrites dans observations_mensuelles.csv\n")

    # 7. Calculer les anomalies et générer anomalies.json
    print("Calcul des anomalies…")
    merged = pd.merge(
        observations,
        normales,
        on=["departement", "mois"],
        how="left",
    )
    merged["anomalie_temperature"] = (merged["temperature"] - merged["normale_temperature"]).round(1)
    merged["anomalie_precipitation"] = (merged["precipitation"] - merged["normale_precipitation"]).round(1)
    merged["anomalie_vent"] = (merged["vent"] - merged["normale_vent"]).round(1)
    merged["anomalie_ensoleillement"] = (merged["ensoleillement"] - merged["normale_ensoleillement"]).round(1)

    anomalies = merged[[
        "departement", "mois", "annee",
        "temperature", "normale_temperature", "anomalie_temperature",
        "precipitation", "normale_precipitation", "anomalie_precipitation",
        "ensoleillement", "normale_ensoleillement", "anomalie_ensoleillement",
        "vent", "normale_vent", "anomalie_vent",
    ]]
    anomalies.to_json(DATA_DIR / "anomalies.json", orient="records", force_ascii=False, indent=2)
    print(f"  {len(anomalies)} anomalies écrites dans anomalies.json\n")

    # 8. Liste des départements pour le frontend
    depts_disponibles = sorted(anomalies["departement"].unique())
    depts_list = []
    for nom in depts_disponibles:
        if nom in CODES_CORSE:
            code = CODES_CORSE[nom]
        else:
            code = "?"
            for _, (n, c) in DEPARTEMENTS_NOMS.items():
                if n == nom:
                    code = c
                    break
        depts_list.append({"nom": nom, "code": code})
    (DATA_DIR / "departements.json").write_text(
        json.dumps(depts_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  {len(depts_list)} départements écrits dans departements.json\n")

    # 9. Générer les fichiers statiques pour le frontend (site statique GitHub Pages)
    print("Génération des fichiers statiques pour le frontend…")
    generer_donnees_statiques(depts_list, anomalies.to_dict("records"))

    print("=== Résumé ===")
    print(f"Départements : {len(depts_list)}")
    print(f"Normales     : {len(normales)} lignes")
    print(f"Observations : {len(observations)} lignes")
    print(f"Anomalies    : {len(anomalies)} entrées")
    print(f"Période obs  : {PERIODE_OBSERVATION[0]}-{PERIODE_OBSERVATION[1]}")
    print(f"Période norm : {PERIODE_NORMALE[0]}-{PERIODE_NORMALE[1]}")
    print("Fichiers générés dans /data")


if __name__ == "__main__":
    main()
