#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
TOOLS="$SDK/build-tools/36.0.0"
ANDROID_JAR="$SDK/platforms/android-36/android.jar"
OUT="$ROOT/build"
KEYSTORE="${SLOT_VISION_KEYSTORE:-$HOME/.android/reel-atrium.jks}"
KEYPASS="${SLOT_VISION_KEYPASS:-$HOME/.android/reel-atrium.pass}"
VERSION_NAME="${VERSION_NAME:-1.0.0}"
VERSION_CODE="${VERSION_CODE:-1}"

for tool in javac keytool openssl zip; do
  command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 1; }
done
[[ -f "$ANDROID_JAR" && -x "$TOOLS/aapt2" ]] || {
  echo "Install Android SDK platform 36 and build-tools 36.0.0." >&2; exit 1;
}
mkdir -p "$OUT" "$(dirname "$KEYSTORE")"
rm -rf "$OUT/classes" "$OUT/dex" "$OUT/generated"
mkdir -p "$OUT/classes" "$OUT/dex" "$OUT/filament-downloads" "$OUT/native/lib"

fetch_dependency() {
  local file="$1" url="$2" expected="$3"
  if [[ ! -f "$file" ]]; then
    curl --proto '=https' --proto-redir '=https' -fsSL --retry 3 "$url" -o "$file"
  fi
  printf '%s  %s\n' "$expected" "$file" | shasum -a 256 -c - >/dev/null
}

FILAMENT_VERSION=1.77.3
FILAMENT_BASE="https://repo.maven.apache.org/maven2/com/google/android/filament"
while read -r artifact hash; do
  [[ -n "$artifact" ]] || continue
  archive="$OUT/filament-downloads/$artifact.aar"
  fetch_dependency "$archive" "$FILAMENT_BASE/$artifact/$FILAMENT_VERSION/$artifact-$FILAMENT_VERSION.aar" "$hash"
  mkdir -p "$OUT/filament-downloads/$artifact"
  unzip -oq "$archive" -d "$OUT/filament-downloads/$artifact"
  for abi in arm64-v8a armeabi-v7a x86 x86_64; do
    mkdir -p "$OUT/native/lib/$abi"
    cp "$OUT/filament-downloads/$artifact/jni/$abi/"*.so "$OUT/native/lib/$abi/"
  done
done < "$ROOT/filament-dependencies.sha256"
fetch_dependency "$OUT/filament-downloads/kotlin-stdlib.jar" \
  "https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/2.4.0/kotlin-stdlib-2.4.0.jar" \
  ccb14ff83fabcb11458b798dbc9824748ccdffeec79c9aba789e6ed1cda86b1c
fetch_dependency "$OUT/filament-downloads/r8.jar" \
  "https://dl.google.com/dl/android/maven2/com/android/tools/r8/9.5.26/r8-9.5.26.jar" \
  3502f087388ce95bbf5254555927f09385dc2636873964d0bd53f3eaf4fb49ad
fetch_dependency "$OUT/filament-downloads/coroutines-core.jar" \
  "https://repo.maven.apache.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-core-jvm/1.11.0/kotlinx-coroutines-core-jvm-1.11.0.jar" \
  d1d75aa01dffbb4d1c520e67e4c4e7f5f6174718e7cb4632412503f2f0e604fa
fetch_dependency "$OUT/filament-downloads/coroutines-android.jar" \
  "https://repo.maven.apache.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-android/1.11.0/kotlinx-coroutines-android-1.11.0.jar" \
  c2cb206d27017c7d1bf5ff179787397543d13748dbabb0d7237e1585e0b29044
CLASSPATH="$OUT/filament-downloads/filament-android/classes.jar:$OUT/filament-downloads/gltfio-android/classes.jar:$OUT/filament-downloads/filament-utils-android/classes.jar:$OUT/filament-downloads/kotlin-stdlib.jar"

if [[ "${UNSIGNED:-0}" != 1 ]]; then
if [[ ! -f "$KEYSTORE" ]]; then
  [[ ! -e "$KEYPASS" ]] || { echo "Signing key is missing but its password file exists; restore the key." >&2; exit 1; }
  (umask 077 && openssl rand -hex 24 > "$KEYPASS")
  keytool -genkeypair -keystore "$KEYSTORE" -storepass:file "$KEYPASS" -alias reel-atrium \
    -keyalg RSA -keysize 3072 -validity 10950 -dname "CN=Slot Vision Release"
  chmod 600 "$KEYSTORE"
fi
[[ -s "$KEYPASS" ]] || { echo "Restore the signing-key password file." >&2; exit 1; }
fi

for game in classic palace garden; do
  [[ -s "$ROOT/assets/models/${game}_atrium.glb" ]] || { echo "Missing cabinet model: $game" >&2; exit 1; }
done
for season in atrium spring summer autumn winter; do
  [[ -s "$ROOT/assets/textures/symbols_${season}.png" ]] || { echo "Missing seasonal artwork: $season" >&2; exit 1; }
done
[[ -s "$ROOT/assets/ibl/atrium_ibl.ktx" ]] || { echo "Missing lighting environment." >&2; exit 1; }

PROFILE_RENDERER="${PROFILE_RENDERER:-0}"
case "$PROFILE_RENDERER" in
  0) PROFILE_ENABLED=false ;;
  1) PROFILE_ENABLED=true ;;
  *) printf 'PROFILE_RENDERER must be 0 or 1\n' >&2; exit 1 ;;
esac
ASSET_ROOT="$ROOT/assets"
if [[ "$PROFILE_RENDERER" == 1 ]]; then
  python3 "$ROOT/tools/build_profile_assets.py" "$ROOT/assets" "$OUT/profile-assets"
  ASSET_ROOT="$OUT/profile-assets"
fi
"$TOOLS/aapt2" compile --dir "$ROOT/res" -o "$OUT/res.zip"
"$TOOLS/aapt2" link -o "$OUT/unsigned.apk" -I "$ANDROID_JAR" \
  --manifest "$ROOT/AndroidManifest.xml" --min-sdk-version 23 --target-sdk-version 36 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  --java "$OUT/generated" -A "$ASSET_ROOT" "$OUT/res.zip"
cat > "$OUT/generated/com/jeremykenedy/reelatrium/BuildConfig.java" <<EOF
package com.jeremykenedy.reelatrium;
public final class BuildConfig {
  public static final boolean RENDER_DIAGNOSTICS = $PROFILE_ENABLED;
}
EOF
find "$ROOT/src" "$OUT/generated" -name '*.java' > "$OUT/sources.txt"
javac -nowarn -Xlint:-options -source 8 -target 8 -bootclasspath "$ANDROID_JAR" \
  -classpath "$CLASSPATH" -d "$OUT/classes" @"$OUT/sources.txt"
find "$OUT/classes" -name '*.class' > "$OUT/classes.txt"
java -cp "$OUT/filament-downloads/r8.jar" com.android.tools.r8.R8 --release --no-data-resources \
  --pg-conf "$ROOT/proguard-rules.pro" \
  --pg-conf "$OUT/filament-downloads/filament-android/proguard.txt" \
  --pg-conf "$OUT/filament-downloads/gltfio-android/proguard.txt" \
  --pg-conf "$OUT/filament-downloads/filament-utils-android/proguard.txt" --lib "$ANDROID_JAR" --min-api 23 --output "$OUT/dex" @"$OUT/classes.txt" \
  "$OUT/filament-downloads/filament-android/classes.jar" \
  "$OUT/filament-downloads/gltfio-android/classes.jar" \
  "$OUT/filament-downloads/filament-utils-android/classes.jar" \
  "$OUT/filament-downloads/kotlin-stdlib.jar" \
  "$OUT/filament-downloads/coroutines-core.jar" \
  "$OUT/filament-downloads/coroutines-android.jar"
(cd "$OUT/dex" && zip -q -j "$OUT/unsigned.apk" classes*.dex)
(cd "$OUT/native" && zip -q -r "$OUT/unsigned.apk" lib)
"$TOOLS/zipalign" -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
if [[ "${UNSIGNED:-0}" == 1 ]]; then
  cp "$OUT/aligned.apk" "$OUT/slot-vision.apk"
else
"$TOOLS/apksigner" sign --ks "$KEYSTORE" --ks-pass "file:$KEYPASS" --ks-key-alias reel-atrium \
  --out "$OUT/slot-vision.apk" "$OUT/aligned.apk"
"$TOOLS/apksigner" verify "$OUT/slot-vision.apk"
fi
(cd "$OUT" && shasum -a 256 slot-vision.apk > slot-vision.apk.sha256)
printf 'Built %s\n' "$OUT/slot-vision.apk"
cat "$OUT/slot-vision.apk.sha256"
