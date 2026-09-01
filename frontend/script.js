// Configuration de l'API
// En local : http://localhost:5000
// En production : remplacer par l'URL de l'API déployée
const API_BASE = "http://localhost:5000";

const MOIS_NOMS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
];

// Références DOM
const selectDepartement = document.getElementById("departement");
const selectMois = document.getElementById("mois");
const selectAnnee = document.getElementById("annee");
const form = document.getElementById("form-anomalie");
const btnCalculer = document.getElementById("btn-calculer");
const resultat = document.getElementById("resultat");
const erreur = document.getElementById("erreur");
const chargement = document.getElementById("chargement");

// Remplir le sélecteur de mois
function remplirMois() {
    MOIS_NOMS.forEach((nom, i) => {
        const opt = document.createElement("option");
        opt.value = i + 1;
        opt.textContent = nom;
        selectMois.appendChild(opt);
    });
}

// Charger les départements depuis l'API
async function chargerDepartements() {
    try {
        const res = await fetch(`${API_BASE}/api/departements`);
        const depts = await res.json();
        depts.forEach(d => {
            const opt = document.createElement("option");
            opt.value = d.nom;
            opt.textContent = `${d.code} - ${d.nom}`;
            selectDepartement.appendChild(opt);
        });
    } catch (e) {
        afficherErreur("Impossible de charger la liste des départements.");
    }
}

// Charger les années depuis l'API
async function chargerAnnees() {
    try {
        const res = await fetch(`${API_BASE}/api/annees`);
        const annees = await res.json();
        annees.forEach(a => {
            const opt = document.createElement("option");
            opt.value = a;
            opt.textContent = a;
            selectAnnee.appendChild(opt);
        });
    } catch (e) {
        afficherErreur("Impossible de charger la liste des années.");
    }
}

// Afficher une erreur
function afficherErreur(msg) {
    resultat.classList.add("hidden");
    erreur.textContent = msg;
    erreur.classList.remove("hidden");
}

// Afficher le résultat
function afficherResultat(data) {
    erreur.classList.add("hidden");

    const moisNom = MOIS_NOMS[data.mois - 1] || `Mois ${data.mois}`;
    document.getElementById("r-departement").textContent =
        `${data.departement} - ${moisNom} ${data.annee}`;

    const elAnomalie = document.getElementById("r-anomalie");
    const signe = data.anomalie > 0 ? "+" : "";
    elAnomalie.textContent = `${signe}${data.anomalie.toFixed(1)}°C`;

    // Couleur selon le signe
    elAnomalie.classList.remove("positive", "negative", "neutre");
    if (data.anomalie > 0.2) {
        elAnomalie.classList.add("positive");
    } else if (data.anomalie < -0.2) {
        elAnomalie.classList.add("negative");
    } else {
        elAnomalie.classList.add("neutre");
    }

    document.getElementById("r-detail").textContent =
        `Température observée : ${data.temperature_moyenne.toFixed(1)}°C | ` +
        `Normale 1991-2020 : ${data.normale_1991_2020.toFixed(1)}°C`;

    resultat.classList.remove("hidden");
}

// Soumettre le formulaire
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const departement = selectDepartement.value;
    const mois = selectMois.value;
    const annee = selectAnnee.value;

    if (!departement || !mois || !annee) {
        afficherErreur("Veuillez sélectionner un département, un mois et une année.");
        return;
    }

    btnCalculer.disabled = true;
    chargement.classList.remove("hidden");
    resultat.classList.add("hidden");
    erreur.classList.add("hidden");

    try {
        const res = await fetch(
            `${API_BASE}/api/anomalie?departement=${encodeURIComponent(departement)}&mois=${mois}&annee=${annee}`
        );
        const data = await res.json();

        if (!res.ok) {
            afficherErreur(data.error || "Données non trouvées.");
        } else {
            afficherResultat(data);
        }
    } catch (e) {
        afficherErreur("Erreur de connexion à l'API.");
    } finally {
        btnCalculer.disabled = false;
        chargement.classList.add("hidden");
    }
});

// Initialisation
remplirMois();
chargerDepartements();
chargerAnnees();
