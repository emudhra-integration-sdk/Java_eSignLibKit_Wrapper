#!/usr/bin/env bash
# download-deps.sh
# Downloads the open-source dependency JARs into the lib/ folder.
# Run from the project root: bash scripts/download-deps.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"
mkdir -p "$LIB_DIR"

download() {
    local name="$1"
    local url="$2"
    local dest="$LIB_DIR/$name"
    if [ -f "$dest" ]; then
        echo "  [skip] $name already exists"
    else
        echo "  [download] $name ..."
        curl -fsSL -o "$dest" "$url" && echo "  [ok] $name" || echo "  [error] Failed to download $name"
    fi
}

download "gson-2.8.5.jar"              "https://repo1.maven.org/maven2/com/google/code/gson/gson/2.8.5/gson-2.8.5.jar"
download "batik-all-1.13.jar"          "https://repo1.maven.org/maven2/org/apache/xmlgraphics/batik-all/1.13/batik-all-1.13.jar"
download "commons-io-2.4.jar"          "https://repo1.maven.org/maven2/commons-io/commons-io/2.4/commons-io-2.4.jar"
download "xmlgraphics-commons-2.4.jar" "https://repo1.maven.org/maven2/org/apache/xmlgraphics/xmlgraphics-commons/2.4/xmlgraphics-commons-2.4.jar"
download "org.w3c.dom.svg-1.1.0.jar"  "https://repo1.maven.org/maven2/xml-apis/xml-apis-ext/1.3.04/xml-apis-ext-1.3.04.jar"

echo ""
echo "Dependencies ready in: $LIB_DIR"
echo "Next: copy local.properties.example to local.properties and set the SDK JAR path."
