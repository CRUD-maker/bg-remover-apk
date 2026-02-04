[app]
title = BG Remover AI
package.name = bgremover
package.domain = org.faseeh
# Source code where the main.py lives
source.dir = Mobile app

source.include_exts = py,png,jpg,kv,atlas,onnx
version = 1.0.0

# Dependencies
# Cleanest minimal set for KivyMD + ONNX
requirements = python3,kivy,kivymd,pillow,numpy,onnxruntime,requests

# Orientation
orientation = portrait
fullscreen = 0

# Android specific
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET
android.api = 33
android.minapi = 21
android.arch = arm64-v8a
android.presplash_color = #1e1e1e

# Using default NDK (Let buildozer handle it)

[buildozer]
log_level = 2
warn_on_root = 1
