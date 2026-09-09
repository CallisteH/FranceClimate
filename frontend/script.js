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
const graphChargement = document.getElementById("graph-chargement");
const graphErreur = document.getElementById("graph-erreur");

// Métriques à afficher (clé, canvas ID, champ valeur, champ normale, unité, libellé axe Y)
const METRIQUES = [
    { canvasId: "chart-temperature",   field: "temperature",     normalField: "normale_temperature",     unit: "°C",   label: "Température (°C)" },
    { canvasId: "chart-precipitation", field: "precipitation",   normalField: "normale_precipitation",   unit: "mm",   label: "Précipitations (mm)" },
    { canvasId: "chart-ensoleillement", field: "ensoleillement", normalField: "normale_ensoleillement", unit: "h",    label: "Ensoleillement (h)" },
    { canvasId: "chart-vent",          field: "vent",            normalField: "normale_vent",            unit: "m/s",  label: "Vent moyen (m/s)" },
];

// Stocke les instances Chart par métrique pour pouvoir les détruire
const chartInstances = {};

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
        if (selectDepartement.value) construireGraphiques(selectDepartement.value);
    } catch (e) {
        afficherGraphErreur("Impossible de charger la liste des départements.");
    }
}

// Initialisation
chargerDepartements();

// --- Graphiques mensuels par département ---

// Génère une couleur HSL répartie sur le cercle pour n couleurs distinctes.
function paletteCouleurs(n) {
    const couleurs = [];
    for (let i = 0; i < n; i++) {
        const hue = Math.round((i * 360) / n);
        couleurs.push(`hsl(${hue}, 70%, 60%)`);
    }
    return couleurs;
}

function afficherGraphErreur(msg) {
    graphErreur.textContent = msg;
    graphErreur.classList.remove("hidden");
}

async function construireGraphiques(departement) {
    graphErreur.classList.add("hidden");
    graphChargement.classList.remove("hidden");

    try {
        const res = await fetch(
            `${API_BASE}/api/anomalies?departement=${encodeURIComponent(departement)}`
        );
        const data = await res.json();
        if (!res.ok) {
            afficherGraphErreur(data.error || "Données non trouvées.");
            return;
        }

        for (const m of METRIQUES) {
            construireUnGraphique(data, m);
        }
    } catch (e) {
        afficherGraphErreur("Erreur de connexion à l'API.");
    } finally {
        graphChargement.classList.add("hidden");
    }
}

function construireUnGraphique(data, metric) {
    // Reshape : seriesParAnnee[annee][mois-1] = valeur
    // normale[mois-1] = normale (constante par mois)
    const annees = [];
    const seriesParAnnee = {};
    const normale = new Array(12).fill(null);

    for (const a of data) {
        const idx = a.mois - 1;
        if (!seriesParAnnee[a.annee]) {
            seriesParAnnee[a.annee] = new Array(12).fill(null);
            annees.push(a.annee);
        }
        const val = a[metric.field];
        seriesParAnnee[a.annee][idx] = val;
        if (normale[idx] === null) normale[idx] = a[metric.normalField];
    }

    annees.sort();
    const couleurs = paletteCouleurs(annees.length);

    const datasets = annees.map((annee, i) => ({
        label: String(annee),
        data: seriesParAnnee[annee],
        borderColor: couleurs[i],
        backgroundColor: couleurs[i],
        tension: 0.25,
        pointRadius: 3,
        borderWidth: 2
    }));

    // Normale 1991-2020 en pointillés, en dernier (référence)
    datasets.push({
        label: "Normale 1991-2020",
        data: normale,
        borderColor: "#e8eef2",
        backgroundColor: "#e8eef2",
        borderDash: [6, 6],
        tension: 0.25,
        pointRadius: 2,
        borderWidth: 2
    });

    const canvas = document.getElementById(metric.canvasId);

    // Détruire l'instance précédente si elle existe
    if (chartInstances[metric.canvasId]) {
        chartInstances[metric.canvasId].destroy();
    }

    chartInstances[metric.canvasId] = new Chart(canvas, {
        type: "line",
        data: { labels: MOIS_NOMS, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#e8eef2", usePointStyle: true, boxWidth: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) =>
                            `${ctx.dataset.label} : ${ctx.parsed.y !== null ? ctx.parsed.y.toFixed(1) : "—"} ${metric.unit}`
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "Mois", color: "#8a9ba8" },
                    ticks: { color: "#8a9ba8" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                y: {
                    title: { display: true, text: metric.label, color: "#8a9ba8" },
                    ticks: { color: "#8a9ba8" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                }
            }
        }
    });
}

// Met à jour les graphiques dès qu'on change de département
selectDepartement.addEventListener("change", () => {
    if (selectDepartement.value) construireGraphiques(selectDepartement.value);
});
