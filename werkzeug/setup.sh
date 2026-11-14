#!/usr/bin/env bash
# Richtet die Werkzeuge in einer frischen Claude-Sitzung ein (ca. 2–3 Min.).
set -e
cd "$(dirname "$0")"
VER="${ORCA_VERSION:-v2.5.0}"
mkdir -p orca && cd orca

# 1) Systempakete: OpenSCAD (Modelle), WebKit/GL/Xvfb (OrcaSlicer ohne Bildschirm)
if ! command -v openscad >/dev/null || ! command -v xvfb-run >/dev/null; then
  (apt-get install -y --no-install-recommends openscad xvfb libwebkit2gtk-4.1-0 libgl1 libegl1 \
     libgl1-mesa-dri libgstreamer-plugins-base1.0-0 >/dev/null 2>&1) || \
  (apt-get update >/dev/null 2>&1 && apt-get install -y --no-install-recommends openscad xvfb \
     libwebkit2gtk-4.1-0 libgl1 libegl1 libgl1-mesa-dri libgstreamer-plugins-base1.0-0 >/dev/null)
fi

# 2) OrcaSlicer (AppImage entpacken)
if [ ! -x squashfs-root/AppRun ]; then
  N="${VER#v}"
  curl -sL -o orca.AppImage \
    "https://github.com/SoftFever/OrcaSlicer/releases/download/${VER}/OrcaSlicer_Linux_AppImage_Ubuntu2404_V${N}.AppImage"
  chmod +x orca.AppImage && ./orca.AppImage --appimage-extract >/dev/null && rm orca.AppImage
fi

# 3) Profile als JSON (passend zur Version, nur Anycubic/Flashforge)
if [ ! -d profile/resources/profiles/Anycubic ]; then
  GIT_LFS_SKIP_SMUDGE=1 git -c advice.detachedHead=false clone -q --depth 1 --branch "$VER" --filter=blob:none --sparse \
    https://github.com/SoftFever/orcaslicer profile
  git -C profile sparse-checkout set --no-cone 'resources/profiles/Anycubic*' \
    'resources/profiles/Flashforge*' 'resources/profiles/OrcaFilamentLibrary*'
fi
# 4) Optional: Python-Geometrie (Reliefs, Prüfungen) und CAD-Stufe build123d (werkzeug/cad.py).
#    Ein Fehlschlag bricht das Setup nicht ab.
python3 -c "import trimesh, manifold3d, scipy, PIL, skimage" 2>/dev/null || \
  pip install --break-system-packages -q trimesh manifold3d scipy pillow scikit-image fast-simplification >/dev/null 2>&1 || \
  echo "Hinweis: trimesh/manifold3d nicht installiert (bild_relief.py, Prüfungen)"
python3 -c "import build123d" 2>/dev/null || \
  pip install --break-system-packages -q build123d >/dev/null 2>&1 || \
  echo "Hinweis: build123d nicht installiert – werkzeug/cad.py nicht nutzbar"
# Leichte 3D-Vorschau fürs Handy (*.app.stl) – ohne pymeshlab lädt die App die großen Netze
python3 -c "import pymeshlab" 2>/dev/null || pip install -q --break-system-packages pymeshlab >/dev/null 2>&1 || echo "Hinweis: pymeshlab fehlt – keine leichten Vorschau-Netze"
echo "druckwerk bereit: OrcaSlicer $VER, $(openscad --version 2>&1 | head -1)"
