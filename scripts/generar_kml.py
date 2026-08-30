# -*- coding: utf-8 -*-
"""Regenera centroides_volcanes.kml desde config_sentinel2.py.

POR QUE EXISTE
==============
El KML se habia generado una vez a mano y despues quedo huerfano: ningun .py,
.html ni .yml del repo lo lee. Eso lo dejo fuera del camino de cualquier
correccion, y por eso sobrevivio ahi el mismo error que motivo una auditoria
entera: el placemark "Nevados de Chillan" quedo a 60.20 km de las coordenadas
reales del volcan -- y a 1.31 km del placemark "Antuco" -- porque las coordenadas
de Chillan eran, en realidad, las de Antuco. En config_sentinel2.py y en
docs/volcanes.js ese error ya estaba corregido; en el KML no.

Un archivo que nadie ejecuta no es inofensivo: es una referencia envenenada
esperando a que alguien lo abra en QGIS y confie en el.

La correccion de fondo no es editar el KML a mano -- eso reproduce el mismo
patron -- sino que deje de ser una copia con vida propia. config_sentinel2.py
es el unico dueno de las coordenadas; este script deriva el KML de ahi, igual
que scripts/generar_volcanes_js.py deriva docs/volcanes.js.

USO
===
    python scripts/generar_kml.py            # reescribe centroides_volcanes.kml
    python scripts/generar_kml.py --check    # solo verifica; sale 1 si difiere

--check es lo que conviene correr en CI: falla si alguien movio un centroide en
el config y el KML se quedo atras.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_sentinel2 import VOLCANES  # noqa: E402

SALIDA = "centroides_volcanes.kml"

# El KML es para inspeccion geografica de los centroides. Las vistas zoom no son
# volcanes distintos: son recortes mas cerrados de uno que ya esta en la lista,
# asi que meterlas duplicaria puntos casi encima y recrearia justo la confusion
# "dos placemarks a 1 km con nombres distintos" que este archivo tuvo.
def es_vista_zoom(cfg):
    return bool(cfg.get("vista_zoom_de"))


ZONAS = [
    ("Norte", "norte"),
    ("Centro", "centro"),
    ("Sur", "sur"),
    ("Austral", "austral"),
]

ESTILOS = {
    "norte": "ff0000ff",
    "centro": "ff00ff00",
    "sur": "ffff0000",
    "austral": "ff00ffff",
}


def construir():
    reales = {n: c for n, c in VOLCANES.items() if not es_vista_zoom(c)}
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    out.append("  <Document>")
    out.append("    <name>Centroides Volcanes Chile - %d Volcanes Activos</name>"
               % len(reales))
    out.append("    <description>Generado por scripts/generar_kml.py desde "
               "config_sentinel2.py. No editar a mano: los cambios se pierden "
               "y el archivo vuelve a divergir del config.</description>")
    out.append("")
    out.append("    <!-- Estilos por zona -->")
    for _, sid in ZONAS:
        out.append('    <Style id="%s">' % sid)
        out.append("      <IconStyle>")
        out.append("        <color>%s</color>" % ESTILOS[sid])
        out.append("        <scale>1.2</scale>")
        out.append("        <Icon><href>http://maps.google.com/mapfiles/kml/"
                   "shapes/volcano.png</href></Icon>")
        out.append("      </IconStyle>")
        out.append("      <LabelStyle><color>%s</color></LabelStyle>" % ESTILOS[sid])
        out.append("    </Style>")
    out.append("")

    ubicados = set()
    for zona, sid in ZONAS:
        enz = [(n, c) for n, c in reales.items() if c.get("zona") == zona]
        enz.sort(key=lambda kv: -kv[1]["lat"])   # norte -> sur (lat negativas)
        if not enz:
            continue
        out.append("    <Folder>")
        out.append("      <name>Zona %s (%d volcanes)</name>" % (zona, len(enz)))
        for nombre, c in enz:
            ubicados.add(nombre)
            out.append("      <Placemark>")
            out.append("        <name>%s</name>" % nombre)
            out.append("        <description>buffer_km: %s | id: %s</description>"
                       % (c.get("buffer_km", "?"), c.get("id", "?")))
            out.append("        <styleUrl>#%s</styleUrl>" % sid)
            out.append("        <Point><coordinates>%.5f,%.5f,0</coordinates></Point>"
                       % (c["lon"], c["lat"]))
            out.append("      </Placemark>")
        out.append("    </Folder>")
        out.append("")

    faltan = set(reales) - ubicados
    if faltan:
        raise SystemExit("[ERROR] volcanes sin zona reconocida: %s"
                         % ", ".join(sorted(faltan)))

    out.append("  </Document>")
    out.append("</kml>")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="no escribe; sale 1 si el archivo esta desactualizado")
    args = ap.parse_args()

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(raiz, SALIDA)
    nuevo = construir()

    if args.check:
        try:
            with open(ruta, encoding="utf-8") as fh:
                actual = fh.read()
        except FileNotFoundError:
            print("[FALLA] %s no existe" % SALIDA)
            return 1
        if actual.replace("\r\n", "\n") != nuevo:
            print("[FALLA] %s no coincide con config_sentinel2.py. "
                  "Corre: python scripts/generar_kml.py" % SALIDA)
            return 1
        print("[ok] %s coincide con config_sentinel2.py" % SALIDA)
        return 0

    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(nuevo)
    print("[ok] %s regenerado desde config_sentinel2.py" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
