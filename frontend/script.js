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
const carteContainerClimat = document.getElementById("carte-france-climat");
const carteContainerDemographie = document.getElementById("carte-france-demographie");
const carteInfoClimat = document.getElementById("carte-info-climat");
const carteInfoDemographie = document.getElementById("carte-info-demographie");

// Set des noms de départements disponibles via l'API (pour activer les paths SVG)
const nomsDepartements = new Set();
// Map nom → élément path SVG (pour le surlignage), une par carte
const pathsParNomClimat = {};
const pathsParNomDemographie = {};
// Évolution démographique { nom: { evolution, ... } }
let evolutionParDept = {};

// Métriques à afficher (clé, canvas ID, champ valeur, champ normale, unité, libellé axe Y)
const METRIQUES = [
    { canvasId: "chart-temperature",   field: "temperature",     normalField: "normale_temperature",     unit: "°C",   label: "Température (°C)" },
    { canvasId: "chart-precipitation", field: "precipitation",   normalField: "normale_precipitation",   unit: "mm",   label: "Précipitations (mm)" },
    { canvasId: "chart-ensoleillement", field: "ensoleillement", normalField: "normale_ensoleillement", unit: "h",    label: "Ensoleillement (h)" },
    { canvasId: "chart-vent",          field: "vent",            normalField: "normale_vent",            unit: "m/s",  label: "Vent moyen (m/s)" },
];

// Stocke les instances Chart par métrique pour pouvoir les détruire
const chartInstances = {};

// --- Onglets ---

function activerOnglet(nom) {
    document.querySelectorAll(".onglet").forEach(o => {
        o.classList.toggle("actif", o.dataset.onglet === nom);
    });
    document.getElementById("contenu-climat").classList.toggle("hidden", nom !== "climat");
    document.getElementById("contenu-demographie").classList.toggle("hidden", nom !== "demographie");

    // Redimensionner les graphiques visibles (le canvas peut avoir une taille nulle si l'onglet était caché)
    if (nom === "climat") {
        for (const m of METRIQUES) {
            if (chartInstances[m.canvasId]) chartInstances[m.canvasId].resize();
        }
    } else {
        if (chartInstances["chart-population"]) chartInstances["chart-population"].resize();
    }
}

document.querySelectorAll(".onglet").forEach(onglet => {
    onglet.addEventListener("click", () => activerOnglet(onglet.dataset.onglet));
});

// Charger les départements depuis l'API, puis charger les deux cartes SVG
async function chargerDepartements() {
    try {
        const res = await fetch(`${API_BASE}/api/departements`);
        const depts = await res.json();
        depts.forEach(d => {
            nomsDepartements.add(d.nom);
            const opt = document.createElement("option");
            opt.value = d.nom;
            opt.textContent = `${d.code} - ${d.nom}`;
            selectDepartement.appendChild(opt);
        });
        await chargerCarteClimat();
        await chargerCarteDemographie();
        if (selectDepartement.value) selectionnerDepartement(selectDepartement.value);
    } catch (e) {
        afficherGraphErreur("Impossible de charger la liste des départements.");
    }
}

// Charge le SVG pour l'onglet climat (style uniforme, cliquable)
async function chargerCarteClimat() {
    try {
        const res = await fetch("carte-france.svg");
        const svgText = await res.text();
        carteContainerClimat.innerHTML = svgText;
        const svg = carteContainerClimat.querySelector("svg");
        if (!svg) return;

        svg.querySelectorAll("path[data-nom]").forEach(path => {
            const nom = path.dataset.nom.replace(/\u2019/g, "'");
            if (!nomsDepartements.has(nom)) {
                path.classList.add("dept-desactive");
                return;
            }
            pathsParNomClimat[nom] = path;
            path.classList.add("dept-actif");
            path.setAttribute("role", "button");
            path.setAttribute("tabindex", "0");
            path.setAttribute("aria-label", nom);
            path.addEventListener("click", () => selectionnerDepartement(nom));
            path.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    selectionnerDepartement(nom);
                }
            });
        });
    } catch (e) {
        carteInfoClimat.textContent = "Carte indisponible — utilisez la liste déroulante.";
    }
}

// Charge le SVG pour l'onglet démographie (coloré par évolution de population)
async function chargerCarteDemographie() {
    try {
        // Récupérer les données d'évolution pour tous les départements
        const resEvol = await fetch(`${API_BASE}/api/population/evolution`);
        const evolData = await resEvol.json();
        evolData.forEach(d => {
            evolutionParDept[d.departement] = d;
        });

        const res = await fetch("carte-france.svg");
        const svgText = await res.text();
        carteContainerDemographie.innerHTML = svgText;
        const svg = carteContainerDemographie.querySelector("svg");
        if (!svg) return;

        svg.querySelectorAll("path[data-nom]").forEach(path => {
            const nom = path.dataset.nom.replace(/\u2019/g, "'");
            if (!nomsDepartements.has(nom)) {
                path.classList.add("dept-desactive");
                return;
            }
            pathsParNomDemographie[nom] = path;
            path.setAttribute("role", "button");
            path.setAttribute("tabindex", "0");
            path.setAttribute("aria-label", nom);

            const evol = evolutionParDept[nom];
            if (evol) {
                path.style.fill = couleurEvolution(evol.evolution);
                path.classList.add("dept-demo");
                // Tooltip natif avec l'évolution
                const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
                title.textContent = `${nom} : ${evol.evolution > 0 ? "+" : ""}${evol.evolution}% (${evol.annee_reference}→${evol.annee_recente})`;
                path.appendChild(title);
            } else {
                path.classList.add("dept-desactive");
                return;
            }

            path.addEventListener("click", () => selectionnerDepartement(nom));
            path.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    selectionnerDepartement(nom);
                }
            });
        });
    } catch (e) {
        carteInfoDemographie.textContent = "Carte indisponible — utilisez la liste déroulante.";
    }
}

// Map une valeur d'évolution (en %) vers une couleur (rouge = recul, bleu = croissance)
function couleurEvolution(evolution) {
    const clamped = Math.max(-5, Math.min(5, evolution));
    const intensity = Math.abs(clamped) / 5;  // 0 à 1
    if (intensity < 0.02) {
        return "#4a5560";  // gris neutre pour stable
    }
    const hue = evolution < 0 ? 0 : 210;
    const lightness = 48 - intensity * 18;  // 48% (léger) à 30% (fort)
    return `hsl(${hue}, 65%, ${lightness}%)`;
}

// Point d'entrée unique : met à jour le select, surligne les cartes, reconstruit les graphiques
function selectionnerDepartement(nom) {
    selectDepartement.value = nom;
    surlignerDepartement(nom);
    construireGraphiques(nom);
}

// Met en évidence le département cliqué sur les deux cartes
function surlignerDepartement(nom) {
    // Carte climat
    Object.values(pathsParNomClimat).forEach(p => p.classList.remove("dept-selectionne"));
    const pathClimat = pathsParNomClimat[nom];
    if (pathClimat) {
        pathClimat.classList.add("dept-selectionne");
        carteInfoClimat.textContent = `Département sélectionné : ${nom}`;
    } else {
        carteInfoClimat.textContent = `Département sélectionné : ${nom} (hors carte métropolitaine)`;
    }

    // Carte démographie
    Object.values(pathsParNomDemographie).forEach(p => p.classList.remove("dept-selectionne"));
    const pathDemo = pathsParNomDemographie[nom];
    if (pathDemo) {
        pathDemo.classList.add("dept-selectionne");
        const evol = evolutionParDept[nom];
        if (evol) {
            const signe = evol.evolution > 0 ? "+" : "";
            carteInfoDemographie.textContent =
                `${nom} : ${signe}${evol.evolution}% sur 5 ans ` +
                `(${evol.population_reference.toLocaleString("fr-FR")} → ` +
                `${evol.population_recente.toLocaleString("fr-FR")} hab)`;
        } else {
            carteInfoDemographie.textContent = `Département sélectionné : ${nom}`;
        }
    } else {
        carteInfoDemographie.textContent = `Département sélectionné : ${nom} (hors carte métropolitaine)`;
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
        await construireGraphiquePopulation(departement);
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

// Met à jour les graphiques dès qu'on change de département via la liste déroulante
selectDepartement.addEventListener("change", () => {
    if (selectDepartement.value) selectionnerDepartement(selectDepartement.value);
});

// --- Graphique de population (INSEE) ---

async function construireGraphiquePopulation(departement) {
    try {
        const res = await fetch(
            `${API_BASE}/api/population?departement=${encodeURIComponent(departement)}`
        );
        const data = await res.json();
        if (!res.ok) {
            return;
        }

        const annees = data.map(d => d.annee);
        const populations = data.map(d => d.population);

        const canvas = document.getElementById("chart-population");
        if (chartInstances["chart-population"]) {
            chartInstances["chart-population"].destroy();
        }

        chartInstances["chart-population"] = new Chart(canvas, {
            type: "line",
            data: {
                labels: annees,
                datasets: [{
                    label: "Population",
                    data: populations,
                    borderColor: "#4ecca3",
                    backgroundColor: "rgba(78, 204, 163, 0.1)",
                    fill: true,
                    tension: 0.2,
                    pointRadius: 2,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#e8eef2", usePointStyle: true, boxWidth: 12 }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) =>
                                `${ctx.dataset.label} : ${ctx.parsed.y.toLocaleString("fr-FR")} hab`
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: "Année", color: "#8a9ba8" },
                        ticks: { color: "#8a9ba8", maxTicksLimit: 12 },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    },
                    y: {
                        title: { display: true, text: "Population (habitants)", color: "#8a9ba8" },
                        ticks: {
                            color: "#8a9ba8",
                            callback: (val) => val.toLocaleString("fr-FR")
                        },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    }
                }
            }
        });
    } catch (e) {
        // Données de population indisponibles : on ignore silencieusement
    }
}
