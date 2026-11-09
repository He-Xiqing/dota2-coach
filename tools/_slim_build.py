"""打包瘦身：headless OpenCV、排除未用模块、构建后裁剪。"""

from pathlib import Path

root = Path(__file__).resolve().parents[1]

vision = root / "requirements-vision.txt"
text = vision.read_text(encoding="utf-8")
text = text.replace("opencv-python>=4.9", "opencv-python-headless>=4.9")
vision.write_text(text, encoding="utf-8")

init = root / "src" / "dota2coach" / "__init__.py"
init_text = init.read_text(encoding="utf-8").replace('__version__ = "0.1.0"', '__version__ = "0.1.1"')
init.write_text(init_text, encoding="utf-8")

info = root / "packaging" / "version_info.txt"
info_text = info.read_text(encoding="utf-8")
info_text = info_text.replace("(0, 1, 0, 0)", "(0, 1, 1, 0)").replace('"0.1.0"', '"0.1.1"')
info.write_text(info_text, encoding="utf-8")

build = root / "scripts" / "build.ps1"
script = build.read_text(encoding="utf-8")
script = script.replace(
    '    "--exclude-module", "tokenizers"\n)',
    '    "--exclude-module", "tokenizers",\n'
    '    "--exclude-module", "tkinter",\n'
    '    "--exclude-module", "pydoc_data",\n'
    '    "--exclude-module", "setuptools",\n'
    '    "--exclude-module", "pip",\n'
    '    "--exclude-module", "pytest",\n'
    '    "--exclude-module", "IPython"\n)',
)
script = script.replace('    "--add-data", "config.toml;.",', '    "--add-data", "config.example.toml;.",')
script = script.replace(
    """    if (-not (Test-Path (Join-Path $target "config.toml"))) {
        Copy-Item (Join-Path $root "config.toml") $target
    }
    Copy-Item (Join-Path $root "data") $target -Recurse -Force
    Copy-Item (Join-Path $root "docs\\gsi.cfg") $target -Force
    Copy-Item (Join-Path $root "README.md") $target -Force""",
    """    Copy-Item (Join-Path $root "data") $target -Recurse -Force
    Copy-Item (Join-Path $root "docs\\gsi.cfg") $target -Force
    Copy-Item (Join-Path $root "README.md") $target -Force
    Copy-Item (Join-Path $root "README.zh-CN.md") $target -Force
    Copy-Item (Join-Path $root "LICENSE") $target -Force
    Copy-Item (Join-Path $root "RELEASE_NOTES.md") $target -Force
    Copy-Item (Join-Path $root "config.example.toml") $target -Force

    # 裁剪用不到的二进制，保持功能不变
    $prune = @(
        "_internal\\cv2\\opencv_videoio_ffmpeg*.dll",
        "_internal\\cv2\\data",
        "_internal\\PyQt6\\Qt6\\bin\\opengl32sw.dll",
        "_internal\\PyQt6\\Qt6\\translations",
        "_internal\\PyQt6\\Qt6\\qml",
        "_internal\\PyQt6\\Qt6\\plugins\\sqldrivers",
        "_internal\\PyQt6\\Qt6\\plugins\\qmltooling",
        "_internal\\PyQt6\\Qt6\\plugins\\iconengines",
        "_internal\\PyQt6\\Qt6\\plugins\\imageformats\\qpdf.*",
        "_internal\\PyQt6\\Qt6\\plugins\\imageformats\\qtiff.*"
    )
    foreach ($pattern in $prune) {
        Get-ChildItem -Path (Join-Path $target $pattern) -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }""",
)
build.write_text(script, encoding="utf-8")
print("build optimized")
