# lib/ — Dependency JARs

This folder holds the open-source dependency JARs required to build the project.
**None of these files are committed to git** (they are excluded by `.gitignore`).

## Populate this folder

### Option A — Copy from the eSign SDK project (quickest)

If you have already cloned [java-esign-sdk](https://github.com/emudhraltd/java-esign-sdk),
its `lib/` folder contains all the files listed below. Just copy them here.

### Option B — Download individually

| File | Source |
|------|--------|
| `gson-2.8.5.jar` | [Maven Central](https://repo1.maven.org/maven2/com/google/code/gson/gson/2.8.5/gson-2.8.5.jar) |
| `batik-all-1.13.jar` | [Maven Central](https://repo1.maven.org/maven2/org/apache/xmlgraphics/batik-all/1.13/batik-all-1.13.jar) |
| `commons-io-2.4.jar` | [Maven Central](https://repo1.maven.org/maven2/commons-io/commons-io/2.4/commons-io-2.4.jar) |
| `xmlgraphics-commons-2.4.jar` | [Maven Central](https://repo1.maven.org/maven2/org/apache/xmlgraphics/xmlgraphics-commons/2.4/xmlgraphics-commons-2.4.jar) |
| `org.w3c.dom.svg-1.1.0.jar` | [Maven Central](https://repo1.maven.org/maven2/org/apache/xmlgraphics/batik-svg-dom/1.13/batik-svg-dom-1.13.jar) |

### Option C — Use the download script

**Windows (PowerShell):**
```powershell
.\scripts\download-deps.ps1
```

**Linux / macOS:**
```bash
bash scripts/download-deps.sh
```

## eSign SDK JAR (separate)

The `eSignASPLibrary` JAR is **not** stored here — it is the proprietary SDK
and must be built separately:

1. Clone [java-esign-sdk](https://github.com/emudhraltd/java-esign-sdk)
2. Build it: `ant clean jar`
3. Copy `dist/eSignASPLibrary5_5.jar` to a convenient location
4. Set the path in your `local.properties` (see `local.properties.example`)
