'use strict';

/**
 * example-direct.js
 *
 * Shows the raw child_process integration without the ESignClient wrapper.
 * Copy and adapt this pattern if you prefer to spawn Java directly.
 */

const { spawn } = require('child_process');
const fs   = require('fs');
const path = require('path');

const JAR_PATH = path.join(__dirname, '..', 'dist', 'newJarEmudhra.jar');

/**
 * Call a method on the bridge JAR directly.
 * @param {'getGatewayParameter'|'getSignedDocument'} methodName
 * @param {object} inputData
 * @returns {Promise<object>}
 */
function callBridge(methodName, inputData) {
    return new Promise((resolve, reject) => {
        const proc = spawn('java', [
            '-cp', JAR_PATH,
            'org.example.NodeJSBridge',
            methodName,
            JSON.stringify(inputData)
        ]);

        let stdout = '', stderr = '';
        proc.stdout.on('data', d => { stdout += d; });
        proc.stderr.on('data', d => { stderr += d; });

        proc.on('close', code => {
            if (code !== 0) {
                return reject(new Error(`Java exited with code ${code}\nstderr: ${stderr.trim()}`));
            }
            try {
                resolve(JSON.parse(stdout.trim()));
            } catch (e) {
                reject(new Error(`Bridge returned non-JSON: ${stdout}\nstderr: ${stderr}`));
            }
        });

        proc.on('error', err => reject(new Error(`Could not start Java: ${err.message}`)));
    });
}

// ── Phase 1 example ──────────────────────────────────────────────────────────
async function runPhase1() {
    const pdfBase64 = fs.readFileSync('/path/to/document.pdf').toString('base64');

    const result = await callBridge('getGatewayParameter', {
        aspID:          'YOUR_ASP_ID',
        eSignURL:       'https://esign-uat.emudhra.com/eSignRequest',
        eSignURLV2:     'https://esign-uat.emudhra.com/eSignPANRequest',
        pfxPath:        '/certs/asp-cert.pfx',
        pfxPassword:    'password',
        pfxAlias:       '1',
        tempFolderPath: '/tmp/esign',
        signerID:       'signer@example.com',
        responseURL:    'https://yourapp.com/esign/callback',
        eSignType:      'V2',
        authMode:       'OTP',
        inputs: [{
            base64Doc:            pdfBase64,
            docInfo:              'Service Agreement',
            signerName:           'Jane Doe',
            reason:               'I agree',
            location:             'Bangalore',
            pageTobeSigned:       'PageLevel',
            pageLevelCoordinates: '1-400,100,150,50;',
            appearanceType:       'StandardSignature',
            coSign:               true,
            inputType:            'PDF'
        }]
    });

    if (result.status === 1) {
        console.log('Phase 1 success');
        console.log('Gateway parameter:', result.gatewayParameter.substring(0, 60) + '...');
        console.log('Temp file:', result.preSignedTempFile);
    } else {
        console.error('Phase 1 failed:', result.errorCode, result.errorMessage);
    }
}

// ── Phase 2 example ──────────────────────────────────────────────────────────
async function runPhase2(responseXML, preSignedTempFile) {
    const result = await callBridge('getSignedDocument', {
        aspID:            'YOUR_ASP_ID',
        eSignURL:         'https://esign-uat.emudhra.com/eSignRequest',
        eSignURLV2:       'https://esign-uat.emudhra.com/eSignPANRequest',
        pfxPath:          '/certs/asp-cert.pfx',
        pfxPassword:      'password',
        pfxAlias:         '1',
        responseXML,
        preSignedTempFile,
        signedFilePath:   '/output/signed-'
    });

    if (result.status === 1) {
        (result.returnDocuments || []).forEach((doc, i) => {
            if (doc.status === 1) {
                const buf = Buffer.from(doc.signedDocument, 'base64');
                fs.writeFileSync(`/output/signed-${i}.pdf`, buf);
                console.log(`Saved: /output/signed-${i}.pdf`);
            }
        });
    } else {
        console.error('Phase 2 failed:', result.errorCode, result.errorMessage);
    }
}

if (require.main === module) {
    runPhase1().catch(console.error);
}

module.exports = { callBridge, runPhase1, runPhase2 };
