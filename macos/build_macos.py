"""Compila em macOS e empacota um .app real em ZIP e DMG."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    if sys.platform != "darwin":
        raise SystemExit("Execute em um Mac ou no workflow GitHub Actions; Windows não gera este .app.")
    # A importação assegura que o Python de compilação inclui o toolkit nativo.
    # Não abre a interface nem executa testes do aplicativo.
    import tkinter
    from PIL import Image, ImageOps

    project = Path(__file__).resolve().parent
    os.chdir(project)
    architecture = platform.machine()
    if architecture not in {"arm64", "x86_64"}:
        raise SystemExit(f"Arquitetura não suportada: {architecture}")
    print(f"Compilação macOS {architecture} | Python {platform.python_version()} | Tk {tkinter.TkVersion}", flush=True)
    with Image.open(project / "assets" / "brand.png") as image:
        icon = ImageOps.contain(image.convert("RGBA"), (1024, 1024), Image.Resampling.LANCZOS)
        square = Image.new("RGBA", (1024, 1024))
        square.alpha_composite(icon, ((1024 - icon.width) // 2, (1024 - icon.height) // 2))
        square.save(project / "assets" / "well.icns", format="ICNS")

    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", project / "dist",
        "--workpath", project / "build", project / "Well_app_macos.spec")
    app = project / "dist" / "Well_app.app"
    if not (app / "Contents" / "MacOS" / "Well_app").is_file():
        raise SystemExit("A compilação terminou sem gerar o executável do bundle.")
    run("codesign", "--verify", "--deep", "--strict", app)

    output_name = f"Well_Studio_V5_macOS_{architecture}"
    archive = project / "dist" / f"{output_name}.zip"
    run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", app, archive)
    # Uma pasta por arquitetura preserva a estrutura do bundle no instalador.
    dmg_stage = project / "build" / f"dmg-{architecture}"
    dmg_stage.mkdir(parents=True, exist_ok=True)
    run("ditto", app, dmg_stage / "Well_app.app")
    applications_link = dmg_stage / "Applications"
    if not applications_link.is_symlink() and not applications_link.exists():
        applications_link.symlink_to("/Applications", target_is_directory=True)
    dmg = project / "dist" / f"{output_name}.dmg"
    run("hdiutil", "create", "-ov", "-volname", "Well Studio V5", "-srcfolder", dmg_stage,
        "-format", "UDZO", dmg)

    manifest = {
        "product": "Well Studio V5", "version": "5.0.0", "architecture": architecture,
        "python": platform.python_version(), "macos": platform.mac_ver()[0],
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "code_signing": "ad-hoc", "apple_notarized": False,
        "functional_tests_run": False,
    }
    manifest_path = project / "dist" / f"{output_name}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    checksums = []
    for artifact in (archive, dmg, manifest_path):
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {artifact.name}")
    (project / "dist" / f"{output_name}.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(f"Aplicativo: {app}\nZIP: {archive}\nDMG: {dmg}", flush=True)


if __name__ == "__main__":
    main()
