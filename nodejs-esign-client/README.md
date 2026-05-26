# eMudhra eSign Node.js Client

Node.js client library to interact with the eMudhra eSign JAR file.

## Prerequisites

- Node.js (v12 or higher)
- Java Runtime Environment (JRE 8 or higher)
- eMudhra eSign JAR file (`newJarEmudhra.jar`)
- Valid eMudhra license and certificate files

## Installation

1. Navigate to the project directory:
```bash
cd nodejs-esign-client
```

2. Install dependencies (if any are added later):
```bash
npm install
```

3. Ensure the JAR file is built:
```bash
cd ..
# Build the JAR file using NetBeans or Ant
```

## Usage

### Basic Example

```javascript
const ESignClient = require('./esign-client');
const path = require('path');

// Initialize client
const jarPath = path.join(__dirname, '..', 'dist', 'newJarEmudhra.jar');
const client = new ESignClient(jarPath);

// Get Gateway Parameters
const config = {
    inputs: [
        {
            base64doc: 'JVBERi0xLjQK...',  // Base64 encoded PDF
            docInfo: 'Agreement Document',
            signerName: 'John Doe',
            reason: 'Signing Agreement',
            location: 'Mumbai',
            pageCoordinates: '100,100,200,150,1',
            coSign: false
        }
    ],
    eSignType: 'V3',
    authMode: 'OTP',  // Options: OTP, FingerPrint, IRIS, FaceRecognition
    tempFolderPath: 'C:\\temp\\esign',
    signerID: 'john.doe@example.com',
    responseURL: 'https://yourapp.com/callback',
    licenceFilePath: 'C:\\path\\to\\license.xml',
    pfxPath: 'C:\\path\\to\\cert.pfx',
    pfxPassword: 'password',
    pfxAlias: 'alias',
    sessionTimeout: 30000
};

// Call the method
const result = await client.getGatewayParameter(config);
console.log('Gateway URL:', result.gatewayUrl);
```

### Get Signed Document

```javascript
const signedDocConfig = {
    responseXML: '<xml>RESPONSE_FROM_GATEWAY</xml>',
    preSignedTempFile: 'C:\\temp\\esign\\presigned.dat',
    licenceFilePath: 'C:\\path\\to\\license.xml',
    pfxPath: 'C:\\path\\to\\cert.pfx',
    pfxPassword: 'password',
    pfxAlias: 'alias',
    signedFilePath: 'C:\\output\\signed_'
};

const result = await client.getSignedDocument(signedDocConfig);
console.log('Signed document status:', result.status);
```

## API Methods

### `new ESignClient(jarPath)`
Creates a new eSign client instance.

**Parameters:**
- `jarPath` (string): Path to the JAR file (optional, defaults to `../dist/newJarEmudhra.jar`)

### `client.getGatewayParameter(config)`
Gets gateway parameters for the eSign workflow.

**Returns:** Promise<object> - Gateway parameters including URL

### `client.getSignedDocument(config)`
Retrieves the signed document after eSign completion.

**Returns:** Promise<object> - Signed document data

## Configuration

### Gateway Parameter Config

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| inputs | Array | Yes | Array of document input configurations |
| eSignType | String | Yes | API version: 'V2' or 'V3' |
| authMode | String | Yes | Authentication mode: 'OTP', 'FingerPrint', 'IRIS', 'FaceRecognition' |
| tempFolderPath | String | Yes | Temporary folder for processing |
| signerID | String | Yes | Signer's email or ID |
| responseURL | String | Yes | Callback URL for gateway response |
| licenceFilePath | String | Yes | Path to eMudhra license file |
| pfxPath | String | Yes | Path to PFX certificate |
| pfxPassword | String | Yes | PFX password |
| pfxAlias | String | Yes | Certificate alias |
| sessionTimeout | Number | No | Session timeout in ms (default: 30000) |

### Input Document Config

| Field | Type | Description |
|-------|------|-------------|
| base64doc | String | Base64 encoded PDF document |
| docInfo | String | Document description |
| signerName | String | Name of the signer |
| reason | String | Reason for signing |
| location | String | Location of signing |
| pageCoordinates | String | Signature position: 'x,y,width,height,page' |
| coSign | Boolean | Enable co-signing |

## Running Examples

```bash
npm start
```

## Troubleshooting

### Java Not Found
Ensure Java is installed and in your system PATH:
```bash
java -version
```

### JAR File Not Found
Build the JAR file first:
```bash
cd ..
ant clean jar
```

### Module Not Found
The project uses native Node.js modules (no external dependencies required).

## License

Proprietary - eMudhra Limited
