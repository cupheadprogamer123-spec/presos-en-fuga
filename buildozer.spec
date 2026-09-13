[app]
title = Presos en Fuga
package.name = presosenfuga
package.domain = org.presosenfuga

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,json

version = 1.0.0

requirements = python3,kivy

orientation = portrait
fullscreen = 1

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
