// Chemin de base des données statiques (site statique, pas d'API).
const DATA_BASE = "data";

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

// Set des noms de départements disponibles (pour activer les paths SVG)
const nomsDepartements = new Set();
// Map nom → code de département (pour charger le bon fichier de données)
const codeParNom = {};
// Map nom → élément path SVG (pour le surlignage), une par carte
const pathsParNomClimat = {};
const pathsParNomDemographie = {};
// Données de population chargées en mémoire { nom: [{annee, population}, ...] }
let populationData = {};
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

// Charger les départements et la population depuis les données statiques, puis charger les cartes
async function chargerDepartements() {
    try {
        const [resDepts, resPop] = await Promise.all([
            fetch(`${DATA_BASE}/departements.json`),
            fetch(`${DATA_BASE}/population.json`),
        ]);
        const depts = await resDepts.json();
        populationData = await resPop.json();

        depts.forEach(d => {
            nomsDepartements.add(d.nom);
            codeParNom[d.nom] = d.code;
            const opt = document.createElement("option");
            opt.value = d.nom;
            opt.textContent = `${d.code} - ${d.nom}`;
            selectDepartement.appendChild(opt);
        });

        calculerEvolution();
        await chargerCarteClimat();
        await chargerCarteDemographie();
        if (selectDepartement.value) selectionnerDepartement(selectDepartement.value);
    } catch (e) {
        afficherGraphErreur("Impossible de charger la liste des départements.");
    }
}

// Calcule l'évolution de la population sur 5 ans pour chaque département
function calculerEvolution() {
    for (const [dept, serie] of Object.entries(populationData)) {
        if (serie.length < 6) continue;
        const recent = serie[serie.length - 1];
        const ref = serie[serie.length - 6];
        const evolution = Math.round(
            (recent.population - ref.population) / ref.population * 100 * 100
        ) / 100;
        evolutionParDept[dept] = {
            evolution,
            annee_recente: recent.annee,
            annee_reference: ref.annee,
            population_recente: recent.population,
            population_reference: ref.population,
        };
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
                const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
                title.textContent = `${nom} : ${evol.evolution > 0 ? "+" : ""}${evol.evolution}% (${evol.annee_reference}\u2192${evol.annee_recente})`;
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
    const intensity = Math.abs(clamped) / 5;
    if (intensity < 0.02) {
        return "#4a5560";
    }
    const hue = evolution < 0 ? 0 : 210;
    const lightness = 48 - intensity * 18;
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
                `(${evol.population_reference.toLocaleString("fr-FR")} \u2192 ` +
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
        const code = codeParNom[departement];
        if (!code) {
            afficherGraphErreur("Code de département introuvable.");
            return;
        }
        const res = await fetch(`${DATA_BASE}/departements/${code}.json`);
        if (!res.ok) {
            afficherGraphErreur("Données non trouvées.");
            return;
        }
        const data = await res.json();

        for (const m of METRIQUES) {
            construireUnGraphique(data, m);
        }
        construireGraphiquePopulation(departement);
    } catch (e) {
        afficherGraphErreur("Erreur de chargement des données.");
    } finally {
        graphChargement.classList.add("hidden");
    }
}

function construireUnGraphique(data, metric) {
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
                            `${ctx.dataset.label} : ${ctx.parsed.y !== null ? ctx.parsed.y.toFixed(1) : "\u2014"} ${metric.unit}`
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

selectDepartement.addEventListener("change", () => {
    if (selectDepartement.value) selectionnerDepartement(selectDepartement.value);
});

// --- Graphique de population (INSEE) ---

function construireGraphiquePopulation(departement) {
    try {
        const data = populationData[departement];
        if (!data) return;

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
