# download-deps.ps1
# Downloads the open-source dependency JARs into the lib/ folder.
# Run from the project root: .\scripts\download-deps.ps1

$libDir = Join-Path $PSScriptRoot "..\lib"
New-Item -ItemType Directory -Force $libDir | Out-Null

$deps = @(
    @{ name = "gson-2.8.5.jar";               url = "https://repo1.maven.org/maven2/com/google/code/gson/gson/2.8.5/gson-2.8.5.jar" },
    @{ name = "batik-all-1.13.jar";            url = "https://repo1.maven.org/maven2/org/apache/xmlgraphics/batik-all/1.13/batik-all-1.13.jar" },
    @{ name = "commons-io-2.4.jar";            url = "https://repo1.maven.org/maven2/commons-io/commons-io/2.4/commons-io-2.4.jar" },
    @{ name = "xmlgraphics-commons-2.4.jar";   url = "https://repo1.maven.org/maven2/org/apache/xmlgraphics/xmlgraphics-commons/2.4/xmlgraphics-commons-2.4.jar" },
    @{ name = "org.w3c.dom.svg-1.1.0.jar";    url = "https://repo1.maven.org/maven2/xml-apis/xml-apis-ext/1.3.04/xml-apis-ext-1.3.04.jar" }
)

foreach ($dep in $deps) {
    $dest = Join-Path $libDir $dep.name
    if (Test-Path $dest) {
        Write-Host "  [skip] $($dep.name) already exists"
    } else {
        Write-Host "  [download] $($dep.name) ..."
        try {
            Invoke-WebRequest -Uri $dep.url -OutFile $dest -UseBasicParsing
            Write-Host "  [ok] $($dep.name)"
        } catch {
            Write-Host "  [error] Failed to download $($dep.name): $_"
        }
    }
}

Write-Host "`nDependencies ready in: $libDir"
Write-Host "Next: copy local.properties.example to local.properties and set the SDK JAR path."
