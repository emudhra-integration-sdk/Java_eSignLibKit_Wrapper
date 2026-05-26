# eMudhra eSign Node.js Client (Java Bridge)

Node.js client that uses the `java` npm package to directly call Java methods without spawning child processes.

## Advantages of Java Bridge Approach

✅ **Better Performance** - Direct method calls (no process spawning)
✅ **Synchronous & Async** - Support for both sync and async calls
✅ **Better Error Handling** - Direct Java exception handling
✅ **Type Safety** - Direct access to Java objects
✅ **Lower Overhead** - No JSON serialization to command line

## Prerequisites

- Node.js (v12 or higher)
- Java Development Kit (JDK 8 or higher) - **JDK required, not just JRE**
- Python 2.7 or 3.x (required for `node-gyp` to build native modules)
- Build tools:
  - **Windows**: Visual Studio Build Tools or `windows-build-tools`
  - **macOS**: Xcode Command Line Tools
  - **Linux**: `build-essential`

## Installation

### 1. Install Build Tools (Windows)

```bash
# Option 1: Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/

# Option 2: Use npm package
npm install --global windows-build-tools
```

### 2. Install Dependencies

```bash
cd nodejs-esign-client
npm install java
```

**Note**: The `java` package requires native compilation and may take a few minutes to install.

### 3. Set JAVA_HOME

Ensure `JAVA_HOME` environment variable is set:

```bash
# Windows
set JAVA_HOME=C:\Program Files\Java\jdk1.8.0_xxx

# macOS/Linux
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.8.0_xxx.jdk/Contents/Home
```

## Usage

### Method 1: Synchronous Call (Faster)

```javascript
const ESignClient = require('./esign-client-java-bridge');

const client = new ESignClient('../dist/newJarEmudhra.jar');

const config = {
    inputs: [{
        base64doc: 'JVBERi0xLjQK...',
        docInfo: 'Document Name',
        signerName: 'John Doe',
        reason: 'Signing',
        location: 'Mumbai',
        pageCoordinates: '100,100,200,150,1',
        coSign: false
    }],
    eSignType: 'V3',
    authMode: 'OTP',
    tempFolderPath: 'C:\\temp\\esign',
    signerID: 'signer@example.com',
    responseURL: 'https://yourapp.com/callback',
    licenceFilePath: 'C:\\path\\to\\license.xml',
    pfxPath: 'C:\\path\\to\\cert.pfx',
    pfxPassword: 'password',
    pfxAlias: 'alias',
    sessionTimeout: 30000
};

// Synchronous call (blocks until complete)
const response = client.getGatewayParameterSync(config);
console.log('Gateway URL:', response.gatewayUrl);
```

### Method 2: Asynchronous Call (Non-blocking)

```javascript
// Async call (non-blocking)
const response = await client.getGatewayParameter(config);
console.log('Gateway URL:', response.gatewayUrl);
```

### Complete Example (Like Your Client's Code)

```javascript
const processRequestInEmudhraNewJar = async (inputJson) => {
    try {
        const mainClass = "org.example.EmudhraJarFile";
        const response = await java.callStaticMethodSync(
            mainClass,
            "getGatewayParameterMain",
            JSON.stringify(inputJson)
        );
        return response;
    } catch (error) {
        console.error("❌ processRequestInEmudhraNewJar ~ error:", error);
        throw new Error("INTERNAL SERVER ERROR");
    }
};
```

## API Reference

### Constructor

```javascript
new ESignClient(jarPath, additionalJars)
```

**Parameters:**
- `jarPath` (string): Path to newJarEmudhra.jar
- `additionalJars` (Array<string>, optional): Additional JAR dependencies

### Methods

#### getGatewayParameterSync(config)
Synchronously gets gateway parameters.

**Returns:** `object` - Gateway parameters

#### getGatewayParameter(config)
Asynchronously gets gateway parameters.

**Returns:** `Promise<object>` - Gateway parameters

#### getSignedDocumentSync(config)
Synchronously retrieves signed document.

**Returns:** `object` - Signed document data

#### getSignedDocument(config)
Asynchronously retrieves signed document.

**Returns:** `Promise<object>` - Signed document data

## Comparison: Java Bridge vs Child Process

| Feature | Java Bridge | Child Process |
|---------|-------------|---------------|
| Performance | ⚡ Fast | Slower |
| Setup | Complex | Simple |
| Dependencies | Many | None |
| Memory | Shared | Separate |
| Type Safety | Yes | No |
| Sync Support | Yes | No |

## Troubleshooting

### Error: "Cannot find module 'java'"

```bash
npm install java
```

### Error: "JAVA_HOME is not set"

Set the environment variable:
```bash
set JAVA_HOME=C:\Program Files\Java\jdk1.8.0_xxx
```

### Error: "Python not found"

Install Python 2.7 or 3.x and add to PATH.

### Error: "MSBuild.exe not found" (Windows)

Install Visual Studio Build Tools:
```bash
npm install --global windows-build-tools
```

### Native Module Build Fails

Try rebuilding:
```bash
npm rebuild java
```

## Performance Tips

1. **Use Sync Methods** when possible (faster than async for quick operations)
2. **Reuse Client Instance** - Create once, call multiple times
3. **Increase Heap Size** if processing large documents:
   ```javascript
   java.options.push('-Xmx2048m');
   ```

## License

Proprietary - eMudhra Limited
