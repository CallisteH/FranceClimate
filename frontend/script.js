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
const chartCanvas = document.getElementById("chart-temp");
let chartInstance = null;

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
        // Rendu initial du graphique sur le premier département chargé
        if (selectDepartement.value) construireGraphique(selectDepartement.value);
    } catch (e) {
        afficherGraphErreur("Impossible de charger la liste des départements.");
    }
}

// Initialisation
chargerDepartements();

// --- Graphique mensuel par département ---

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

async function construireGraphique(departement) {
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

        // Reshape : seriesParAnnee[annee][mois-1] = temperature_moyenne
        // normale[mois-1] = normale_1991_2020 (constante par mois)
        const annees = [];
        const seriesParAnnee = {};
        const normale = new Array(12).fill(null);

        for (const a of data) {
            const idx = a.mois - 1;
            if (!seriesParAnnee[a.annee]) {
                seriesParAnnee[a.annee] = new Array(12).fill(null);
                annees.push(a.annee);
            }
            seriesParAnnee[a.annee][idx] = a.temperature_moyenne;
            if (normale[idx] === null) normale[idx] = a.normale_1991_2020;
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

        // Normale 1991-2020 en pointillés, en dernier ( référence )
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

        if (chartInstance) chartInstance.destroy();
        chartInstance = new Chart(chartCanvas, {
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
                                `${ctx.dataset.label} : ${ctx.parsed.y.toFixed(1)}°C`
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
                        title: { display: true, text: "Température (°C)", color: "#8a9ba8" },
                        ticks: { color: "#8a9ba8" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    }
                }
            }
        });
    } catch (e) {
        afficherGraphErreur("Erreur de connexion à l'API.");
    } finally {
        graphChargement.classList.add("hidden");
    }
}

// Met à jour le graphique dès qu'on change de département
selectDepartement.addEventListener("change", () => {
    if (selectDepartement.value) construireGraphique(selectDepartement.value);
});
