# Complete Setup Guide - Step by Step

## Prerequisites Check

### 1. Check if Java JDK is installed

```bash
java -version
javac -version
```

**Required**: JDK 8 or higher (not just JRE - you need the full JDK)

If not installed, download from: https://www.oracle.com/java/technologies/downloads/

### 2. Check if Node.js is installed

```bash
node --version
npm --version
```

**Required**: Node.js v12 or higher

If not installed, download from: https://nodejs.org/

### 3. Set JAVA_HOME environment variable

**Windows:**
```bash
# Check if set
echo %JAVA_HOME%

# If not set, add it (adjust path to your JDK location)
setx JAVA_HOME "C:\Program Files\Java\jdk1.8.0_xxx"
```

**To find your JDK path on Windows:**
```bash
where javac
```

## Installation Steps

### Step 1: Navigate to the project

```bash
cd "D:\OneDrive - eMudhra Limited\development\IntegrationKits\java\newJarEmudhra\nodejs-esign-client"
```

### Step 2: Install Build Tools (Windows ONLY)

**Option A: Install Visual Studio Build Tools** (Recommended)
- Download from: https://visualstudio.microsoft.com/downloads/
- Install "Desktop development with C++"

**Option B: Use npm (may take 15-20 minutes)**
```bash
npm install --global windows-build-tools
```

### Step 3: Install the java package

```bash
npm install java
```

**Note**: This will take 2-5 minutes as it compiles native modules.

### Step 4: Verify the JAR file exists

```bash
# Check if JAR exists
dir ..\dist\newJarEmudhra.jar
```

If it doesn't exist, build it first:
- Open the project in NetBeans
- Click "Clean and Build" (Shift+F11)

## Running the Examples

### Option 1: Run the Direct Example (Simplest)

```bash
node example-direct.js
```

This will show you the template code. You need to:
1. Update the configuration in the file
2. Uncomment the test line
3. Run again

### Option 2: Run with the Client Wrapper

```bash
node index-java-bridge.js
```

### Option 3: Run a Custom Script

Create a file `my-test.js`:

```javascript
const java = require('java');
const path = require('path');

// Add JAR to classpath
const jarPath = path.join(__dirname, '..', 'dist', 'newJarEmudhra.jar');
console.log('Loading JAR from:', jarPath);
java.classpath.push(jarPath);

// Test configuration
const inputJson = {
    inputs: [{
        base64doc: 'TEST',
        docInfo: 'Test Document',
        signerName: 'Test User',
        reason: 'Testing',
        location: 'Mumbai',
        pageCoordinates: '100,100,200,150,1',
        coSign: false,
        imageSignBase64: ''
    }],
    eSignType: 'V3',
    authMode: 'OTP',
    tempFolderPath: 'C:\\temp\\esign',
    signerID: 'test@example.com',
    responseURL: 'https://example.com/callback',
    licenceFilePath: 'C:\\temp\\license.xml',
    pfxPath: 'C:\\temp\\cert.pfx',
    pfxPassword: 'password',
    pfxAlias: 'alias',
    sessionTimeout: 30000
};

async function test() {
    try {
        console.log('Calling Java method...');

        const mainClass = "org.example.EmudhraJarFile";
        const response = java.callStaticMethodSync(
            mainClass,
            "getGatewayParameterMain",
            JSON.stringify(inputJson)
        );

        console.log('Success!');
        console.log('Response:', response);

    } catch (error) {
        console.error('Error:', error.message);
        console.error('Stack:', error.stack);
    }
}

test();
```

Then run:
```bash
node my-test.js
```

## Common Issues and Solutions

### Issue 1: "Cannot find module 'java'"

**Solution:**
```bash
npm install java
```

### Issue 2: "JAVA_HOME is not defined"

**Solution (Windows):**
```bash
# Find Java path
where javac

# Set JAVA_HOME (adjust path)
setx JAVA_HOME "C:\Program Files\Java\jdk1.8.0_301"

# Restart your terminal/command prompt
```

### Issue 3: "Python not found"

**Solution:**
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### Issue 4: "MSBuild.exe not found"

**Solution:**
Install Visual Studio Build Tools or run:
```bash
npm install --global windows-build-tools
```

### Issue 5: "java.lang.ClassNotFoundException: org.example.EmudhraJarFile"

**Solution:**
The JAR file is not built or not in the correct location.
```bash
# Check if JAR exists
dir ..\dist\newJarEmudhra.jar

# If not, rebuild it in NetBeans
```

### Issue 6: Build fails during `npm install java`

**Solution:**
```bash
# Clean npm cache
npm cache clean --force

# Try again
npm install java --verbose
```

## Quick Test (No Configuration Needed)

Create `test-java-bridge.js`:

```javascript
const java = require('java');

// Test if java bridge is working
console.log('Testing Java Bridge...');

try {
    // Test basic Java functionality
    const ArrayList = java.import('java.util.ArrayList');
    const list = new ArrayList();
    list.addSync('Hello');
    list.addSync('World');

    console.log('✓ Java bridge is working!');
    console.log('List size:', list.sizeSync());
    console.log('First item:', list.getSync(0));

} catch (error) {
    console.error('✗ Java bridge failed:', error.message);
}
```

Run:
```bash
node test-java-bridge.js
```

If this works, the Java bridge is installed correctly!

## Next Steps

1. **Build the JAR** (if not done already)
2. **Update configuration** in your script with real values:
   - License file path
   - PFX certificate path
   - Response URLs
   - PDF documents (base64)
3. **Run your script**

## For Your Client

Your client can use this exact pattern from the screenshot:

```javascript
const java = require('java');
const path = require('path');

// Setup
java.classpath.push(path.join(__dirname, 'dist', 'newJarEmudhra.jar'));

// Their function (from screenshot)
const processRequestInEmudhraNewJar = async (inputJson) => {
    try {
        const mainClass = "org.example.EmudhraJarFile";
        const response = java.callStaticMethodSync(
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

That's it! 🎉
