// =====================================================================
// docs/volcanes.js -- AUTO-GENERADO desde config_sentinel2.py
// NO EDITAR A MANO. Para modificar coordenadas, editar config_sentinel2.py
// y re-correr:
//     python scripts/generar_volcanes_js.py
//
// Single source of truth: config_sentinel2.VOLCANES
// Generado: 2026-08-19T18:48:16.454374+00:00
// Total entidades: 51 (43 volcanes + 8 vistas zoom)
// =====================================================================

// Mapa nombre -> { lat, lon, buffer_km, zona, id, activo, [vista_zoom_de, motivo] }
window.VOLCANES_CONFIG = {
  "Taapaca": {
    "lat": -18.10922,
    "lon": -69.50584,
    "buffer_km": 5.0,
    "zona": "Norte",
    "id": "354010",
    "activo": true
  },
  "Parinacota": {
    "lat": -18.17126,
    "lon": -69.14534,
    "buffer_km": 2.5,
    "zona": "Norte",
    "id": "354020",
    "activo": true
  },
  "Guallatiri": {
    "lat": -18.42781,
    "lon": -69.085,
    "buffer_km": 2.5,
    "zona": "Norte",
    "id": "354030",
    "activo": true
  },
  "Isluga": {
    "lat": -19.155746,
    "lon": -68.834406,
    "buffer_km": 1.0,
    "zona": "Norte",
    "id": "355030",
    "activo": true
  },
  "Irruputuncu": {
    "lat": -20.73329,
    "lon": -68.56041,
    "buffer_km": 1.4,
    "zona": "Norte",
    "id": "355040",
    "activo": true
  },
  "Ollague": {
    "lat": -21.30685,
    "lon": -68.17941,
    "buffer_km": 3.5,
    "zona": "Norte",
    "id": "355050",
    "activo": true
  },
  "San Pedro": {
    "lat": -21.88485,
    "lon": -68.40706,
    "buffer_km": 4.5,
    "zona": "Norte",
    "id": "355080",
    "activo": true
  },
  "Lascar": {
    "lat": -23.36726,
    "lon": -67.73611,
    "buffer_km": 1.5,
    "zona": "Norte",
    "id": "355100",
    "activo": true
  },
  "Tupungatito": {
    "lat": -33.40849,
    "lon": -69.82181,
    "buffer_km": 3.5,
    "zona": "Centro",
    "id": "357010",
    "activo": true
  },
  "San Jose": {
    "lat": -33.78682,
    "lon": -69.89732,
    "buffer_km": 2.5,
    "zona": "Centro",
    "id": "357020",
    "activo": true
  },
  "Tinguiririca": {
    "lat": -34.80794,
    "lon": -70.34917,
    "buffer_km": 2.8,
    "zona": "Centro",
    "id": "357030",
    "activo": true
  },
  "Planchon-Peteroa": {
    "lat": -35.24212,
    "lon": -70.57189,
    "buffer_km": 1.3,
    "zona": "Centro",
    "id": "357040",
    "activo": true
  },
  "Descabezado Grande": {
    "lat": -35.60431,
    "lon": -70.7483,
    "buffer_km": 7.0,
    "zona": "Centro",
    "id": "357050",
    "activo": true
  },
  "Tatara-San Pedro": {
    "lat": -35.99755,
    "lon": -70.84533,
    "buffer_km": 3.5,
    "zona": "Centro",
    "id": "357055",
    "activo": true
  },
  "Laguna del Maule": {
    "lat": -36.071,
    "lon": -70.49828,
    "buffer_km": 9.0,
    "zona": "Centro",
    "id": "357058",
    "activo": true
  },
  "Nevado de Longavi": {
    "lat": -36.20001,
    "lon": -71.1701,
    "buffer_km": 5.0,
    "zona": "Centro",
    "id": "357065",
    "activo": true
  },
  "Nevados de Chillan": {
    "lat": -36.87,
    "lon": -71.38,
    "buffer_km": 3.3,
    "zona": "Centro",
    "id": "357070",
    "activo": true
  },
  "Antuco": {
    "lat": -37.41093,
    "lon": -71.351307,
    "buffer_km": 3.0,
    "zona": "Sur",
    "id": "357080",
    "activo": true
  },
  "Copahue": {
    "lat": -37.858693,
    "lon": -71.16832,
    "buffer_km": 1.1,
    "zona": "Sur",
    "id": "357090",
    "activo": true
  },
  "Callaqui": {
    "lat": -37.92554,
    "lon": -71.46113,
    "buffer_km": 5.0,
    "zona": "Sur",
    "id": "357095",
    "activo": true
  },
  "Lonquimay": {
    "lat": -38.38216,
    "lon": -71.5853,
    "buffer_km": 3.0,
    "zona": "Sur",
    "id": "357100",
    "activo": true
  },
  "Llaima": {
    "lat": -38.71238,
    "lon": -71.73447,
    "buffer_km": 4.0,
    "zona": "Sur",
    "id": "357110",
    "activo": true
  },
  "Sollipulli": {
    "lat": -38.98103,
    "lon": -71.51557,
    "buffer_km": 5.0,
    "zona": "Sur",
    "id": "357115",
    "activo": true
  },
  "Villarrica": {
    "lat": -39.42021,
    "lon": -71.93987,
    "buffer_km": 1.0,
    "zona": "Sur",
    "id": "357120",
    "activo": true
  },
  "Quetrupillan": {
    "lat": -39.5315,
    "lon": -71.70337,
    "buffer_km": 8.5,
    "zona": "Sur",
    "id": "357125",
    "activo": true
  },
  "Lanin": {
    "lat": -39.637488,
    "lon": -71.502686,
    "buffer_km": 4.0,
    "zona": "Sur",
    "id": "357130",
    "activo": true
  },
  "Mocho-Choshuenco": {
    "lat": -39.933961,
    "lon": -72.030398,
    "buffer_km": 6.0,
    "zona": "Sur",
    "id": "357135",
    "activo": true
  },
  "Carran - Los Venados": {
    "lat": -40.37922,
    "lon": -72.10509,
    "buffer_km": 6.5,
    "zona": "Sur",
    "id": "357143",
    "activo": true
  },
  "Puyehue - Cordon Caulle": {
    "lat": -40.54783,
    "lon": -72.14826,
    "buffer_km": 10.0,
    "zona": "Sur",
    "id": "357150",
    "activo": true
  },
  "Antillanca - Casablanca": {
    "lat": -40.774523,
    "lon": -72.171543,
    "buffer_km": 5.5,
    "zona": "Sur",
    "id": "357155",
    "activo": true
  },
  "Osorno": {
    "lat": -41.10453,
    "lon": -72.49271,
    "buffer_km": 4.0,
    "zona": "Austral",
    "id": "358060",
    "activo": true
  },
  "Calbuco": {
    "lat": -41.33035,
    "lon": -72.60399,
    "buffer_km": 2.5,
    "zona": "Austral",
    "id": "358070",
    "activo": true
  },
  "Yate": {
    "lat": -41.78269,
    "lon": -72.387644,
    "buffer_km": 5.0,
    "zona": "Austral",
    "id": "358080",
    "activo": true
  },
  "Hornopiren": {
    "lat": -41.88132,
    "lon": -72.43178,
    "buffer_km": 2.5,
    "zona": "Austral",
    "id": "358085",
    "activo": true
  },
  "Huequi": {
    "lat": -42.38142,
    "lon": -72.582982,
    "buffer_km": 2.0,
    "zona": "Austral",
    "id": "358090",
    "activo": true
  },
  "Michinmahuida": {
    "lat": -42.83733,
    "lon": -72.43927,
    "buffer_km": 9.5,
    "zona": "Austral",
    "id": "358095",
    "activo": true
  },
  "Chaiten": {
    "lat": -42.83276,
    "lon": -72.65155,
    "buffer_km": 2.7,
    "zona": "Austral",
    "id": "358041",
    "activo": true
  },
  "Corcovado": {
    "lat": -43.193,
    "lon": -72.78979,
    "buffer_km": 2.5,
    "zona": "Austral",
    "id": "358100",
    "activo": true
  },
  "Melimoyu": {
    "lat": -44.074015,
    "lon": -72.867431,
    "buffer_km": 7.0,
    "zona": "Austral",
    "id": "358110",
    "activo": true
  },
  "Mentolat": {
    "lat": -44.696206,
    "lon": -73.072694,
    "buffer_km": 3.0,
    "zona": "Austral",
    "id": "358120",
    "activo": true
  },
  "Cay": {
    "lat": -45.07068,
    "lon": -72.96318,
    "buffer_km": 3.5,
    "zona": "Austral",
    "id": "358130",
    "activo": true
  },
  "Maca": {
    "lat": -45.1121,
    "lon": -73.16908,
    "buffer_km": 3.5,
    "zona": "Austral",
    "id": "358140",
    "activo": true
  },
  "Hudson": {
    "lat": -45.90915,
    "lon": -72.96508,
    "buffer_km": 8.0,
    "zona": "Austral",
    "id": "358150",
    "activo": true
  },
  "Melimoyu_Conos_Eruptivos": {
    "lat": -44.057878,
    "lon": -72.786587,
    "buffer_km": 4.0,
    "zona": "Austral",
    "id": "358110_zoom1",
    "activo": true,
    "vista_zoom_de": "Melimoyu",
    "motivo": "Seguimiento de centros eruptivos menores (Conos Suyai, Correntoso y El Sauce)"
  },
  "Mentolat_Sismicidad_VT": {
    "lat": -44.684081,
    "lon": -73.195247,
    "buffer_km": 3.5,
    "zona": "Austral",
    "id": "358120_zoom1",
    "activo": true,
    "vista_zoom_de": "Mentolat",
    "motivo": "Mayor cluster de sismicidad VT"
  },
  "Hudson_Ultima_Erupcion": {
    "lat": -45.950731,
    "lon": -72.989386,
    "buffer_km": 4.0,
    "zona": "Austral",
    "id": "358150_zoom1",
    "activo": true,
    "vista_zoom_de": "Hudson",
    "motivo": "Zona ultima erupcion"
  },
  "Lascar_Crater": {
    "lat": -23.362885,
    "lon": -67.731225,
    "buffer_km": 0.5,
    "zona": "Norte",
    "id": "355100_zoom1",
    "activo": true,
    "vista_zoom_de": "Lascar",
    "motivo": "Crater"
  },
  "Isluga_Crater_Fumarola": {
    "lat": -19.158113,
    "lon": -68.834894,
    "buffer_km": 0.55,
    "zona": "Norte",
    "id": "355030_zoom1",
    "activo": true,
    "vista_zoom_de": "Isluga",
    "motivo": "Crater y fumarola flanco S"
  },
  "Copahue_Crater_Lake": {
    "lat": -37.855638,
    "lon": -71.160212,
    "buffer_km": 0.36,
    "zona": "Sur",
    "id": "357090_zoom1",
    "activo": true,
    "vista_zoom_de": "Copahue",
    "motivo": "Lago crater Copahue"
  },
  "Nevados_de_Chillan_Crater_Nicanor": {
    "lat": -36.867211,
    "lon": -71.377411,
    "buffer_km": 1.2,
    "zona": "Centro",
    "id": "357070_zoom1",
    "activo": true,
    "vista_zoom_de": "Nevados de Chillan",
    "motivo": "Crater Nicanor (vent activo)"
  },
  "Nevado_de_Longavi_Crater": {
    "lat": -36.198067,
    "lon": -71.164861,
    "buffer_km": 2.0,
    "zona": "Centro",
    "id": "357065_zoom1",
    "activo": true,
    "vista_zoom_de": "Nevado de Longavi",
    "motivo": "Crater"
  }
};

// Lista plana en orden Norte->Sur + vistas zoom al final
window.VOLCANES_LIST = [
  "Taapaca",
  "Parinacota",
  "Guallatiri",
  "Isluga",
  "Irruputuncu",
  "Ollague",
  "San Pedro",
  "Lascar",
  "Tupungatito",
  "San Jose",
  "Tinguiririca",
  "Planchon-Peteroa",
  "Descabezado Grande",
  "Tatara-San Pedro",
  "Laguna del Maule",
  "Nevado de Longavi",
  "Nevados de Chillan",
  "Antuco",
  "Copahue",
  "Callaqui",
  "Lonquimay",
  "Llaima",
  "Sollipulli",
  "Villarrica",
  "Quetrupillan",
  "Lanin",
  "Mocho-Choshuenco",
  "Carran - Los Venados",
  "Puyehue - Cordon Caulle",
  "Antillanca - Casablanca",
  "Osorno",
  "Calbuco",
  "Yate",
  "Hornopiren",
  "Huequi",
  "Chaiten",
  "Michinmahuida",
  "Corcovado",
  "Melimoyu",
  "Mentolat",
  "Cay",
  "Maca",
  "Hudson",
  "Melimoyu_Conos_Eruptivos",
  "Mentolat_Sismicidad_VT",
  "Hudson_Ultima_Erupcion",
  "Lascar_Crater",
  "Isluga_Crater_Fumarola",
  "Copahue_Crater_Lake",
  "Nevados_de_Chillan_Crater_Nicanor",
  "Nevado_de_Longavi_Crater"
];

// Solo volcanes principales (sin vistas zoom), agrupados por zona y ordenados N->S
window.VOLCANES_POR_ZONA = {
  "Norte": [
    "Taapaca",
    "Parinacota",
    "Guallatiri",
    "Isluga",
    "Irruputuncu",
    "Ollague",
    "San Pedro",
    "Lascar"
  ],
  "Centro": [
    "Tupungatito",
    "San Jose",
    "Tinguiririca",
    "Planchon-Peteroa",
    "Descabezado Grande",
    "Tatara-San Pedro",
    "Laguna del Maule",
    "Nevado de Longavi",
    "Nevados de Chillan"
  ],
  "Sur": [
    "Antuco",
    "Copahue",
    "Callaqui",
    "Lonquimay",
    "Llaima",
    "Sollipulli",
    "Villarrica",
    "Quetrupillan",
    "Lanin",
    "Mocho-Choshuenco",
    "Carran - Los Venados",
    "Puyehue - Cordon Caulle",
    "Antillanca - Casablanca"
  ],
  "Austral": [
    "Osorno",
    "Calbuco",
    "Yate",
    "Hornopiren",
    "Huequi",
    "Chaiten",
    "Michinmahuida",
    "Corcovado",
    "Melimoyu",
    "Mentolat",
    "Cay",
    "Maca",
    "Hudson"
  ]
};

// Nombres de las vistas zoom (sub-vistas de Melimoyu/Mentolat/Hudson)
window.VISTAS_ZOOM = [
  "Melimoyu_Conos_Eruptivos",
  "Mentolat_Sismicidad_VT",
  "Hudson_Ultima_Erupcion",
  "Lascar_Crater",
  "Isluga_Crater_Fumarola",
  "Copahue_Crater_Lake",
  "Nevados_de_Chillan_Crater_Nicanor",
  "Nevado_de_Longavi_Crater"
];

// Alias compatible: lista completa (volcanes + vistas zoom)
window.TODOS_VOLCANES = window.VOLCANES_LIST.slice();

// Ranking 14 mas riesgosos (SERNAGEOMIN). Estable, no derivado de config_sentinel2.
window.VOLCANES_RIESGOSOS = [
  {
    "nombre": "Villarrica",
    "region": "La Araucania - Los Rios"
  },
  {
    "nombre": "Calbuco",
    "region": "Los Lagos"
  },
  {
    "nombre": "Llaima",
    "region": "La Araucania"
  },
  {
    "nombre": "Puyehue - Cordon Caulle",
    "region": "Los Rios - Los Lagos"
  },
  {
    "nombre": "Descabezado Grande",
    "region": "Maule"
  },
  {
    "nombre": "Carran - Los Venados",
    "region": "Los Rios"
  },
  {
    "nombre": "Chaiten",
    "region": "Los Lagos"
  },
  {
    "nombre": "Osorno",
    "region": "Los Lagos"
  },
  {
    "nombre": "Mocho-Choshuenco",
    "region": "Los Rios"
  },
  {
    "nombre": "Nevados de Chillan",
    "region": "Nuble"
  },
  {
    "nombre": "Lonquimay",
    "region": "La Araucania"
  },
  {
    "nombre": "Hudson",
    "region": "Aysen"
  },
  {
    "nombre": "Lascar",
    "region": "Antofagasta"
  },
  {
    "nombre": "Copahue",
    "region": "Bio Bio"
  }
];

// ------------------------------------------------------------------
// Helpers (idempotentes, no mutan estado)
// ------------------------------------------------------------------
window.getVolcanesPorZona = function(zona) {
  return (window.VOLCANES_POR_ZONA[zona] || []).slice();
};
window.getVolcanInfo = function(nombre) {
  return window.VOLCANES_CONFIG[nombre] || null;
};
window.esVistaZoom = function(nombre) {
  return window.VISTAS_ZOOM.indexOf(nombre) !== -1;
};

