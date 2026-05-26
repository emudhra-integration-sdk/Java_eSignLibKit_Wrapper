'use strict';

/**
 * eMudhra eSign Node.js Bridge — Usage Example
 *
 * This file demonstrates a complete two-phase eSign workflow.
 * Phase 1: getGatewayParameter  — send document → receive gateway redirect
 * Phase 2: getSignedDocument    — receive callback XML → get signed PDF
 *
 * Update the CONFIGURATION block below with your real credentials before running.
 */

const fs = require('fs');
const path = require('path');
const ESignClient = require('./esign-client');

// ── CONFIGURATION ─────────────────────────────────────────────────────────────
const config = {
    // Path to the built fat JAR
    jarPath: path.join(__dirname, '..', 'dist', 'newJarEmudhra.jar'),

    // eMudhra gateway credentials
    aspID:      'YOUR_ASP_ID',
    eSignURL:   'https://esign-uat.emudhra.com/eSignRequest',    // V2 (Aadhaar)
    eSignURLV2: 'https://esign-uat.emudhra.com/eSignPANRequest', // V3 (PAN)

    // ASP signing certificate
    pfxPath:     '/path/to/your-certificate.pfx',
    pfxPassword: 'pfx-password',
    pfxAlias:    '1',

    // Session
    tempFolderPath: '/tmp/esign',
    signerID:       'signer@example.com',
    responseURL:    'https://yourapp.com/esign/callback',

    // Document to sign (PDF file)
    pdfPath: '/path/to/document.pdf'
};
// ─────────────────────────────────────────────────────────────────────────────

async function phase1() {
    console.log('── Phase 1: Initiating eSign ──────────────────────────');

    const client = new ESignClient(config.jarPath);

    // Read PDF and encode as base64
    const pdfBytes  = fs.readFileSync(config.pdfPath);
    const base64Doc = pdfBytes.toString('base64');

    const result = await client.getGatewayParameter({
        aspID:         config.aspID,
        eSignURL:      config.eSignURL,
        eSignURLV2:    config.eSignURLV2,
        pfxPath:       config.pfxPath,
        pfxPassword:   config.pfxPassword,
        pfxAlias:      config.pfxAlias,
        tempFolderPath: config.tempFolderPath,
        signerID:      config.signerID,
        responseURL:   config.responseURL,
        eSignType:     'V2',    // V2 = Aadhaar, V3 = PAN
        authMode:      'OTP',

        inputs: [
            {
                base64Doc,
                docInfo:    'Service Agreement',
                signerName: 'John Doe',
                reason:     'I agree to the terms',
                location:   'Bangalore',

                // Signature placement — PageLevel lets you specify exact coordinates
                pageTobeSigned:      'PageLevel',
                pageLevelCoordinates: '1-400,100,150,50;',  // page-x,y,width,height

                // OR use a preset quadrant on the last page:
                // pageTobeSigned: 'Last',
                // coordinates:    'BottomRight',

                appearanceType: 'StandardSignature',
                coSign:         true,
                inputType:      'PDF'
            }
        ]
    });

    console.log('Status:', result.status === 1 ? 'SUCCESS' : 'FAILED');
    if (result.status !== 1) {
        console.error('Error:', result.errorCode, '-', result.errorMessage);
        return;
    }

    console.log('Transaction ID:    ', result.transactionID);
    console.log('Pre-signed temp:   ', result.preSignedTempFile);
    console.log('Gateway parameter: ', result.gatewayParameter ? result.gatewayParameter.substring(0, 80) + '...' : 'N/A');

    console.log('\n→ Redirect the user to the eMudhra gateway with the gatewayParameter.');
    console.log('→ Save transactionID and preSignedTempFile for Phase 2.');
}

async function phase2(responseXML, preSignedTempFile) {
    console.log('\n── Phase 2: Retrieving Signed Document ─────────────────');

    const client = new ESignClient(config.jarPath);

    const result = await client.getSignedDocument({
        aspID:         config.aspID,
        eSignURL:      config.eSignURL,
        eSignURLV2:    config.eSignURLV2,
        pfxPath:       config.pfxPath,
        pfxPassword:   config.pfxPassword,
        pfxAlias:      config.pfxAlias,
        responseXML,
        preSignedTempFile,
        signedFilePath: '/tmp/esign/signed-'  // writes signed-0.pdf, signed-1.pdf, …
    });

    console.log('Status:', result.status === 1 ? 'SUCCESS' : 'FAILED');
    if (result.status !== 1) {
        console.error('Error:', result.errorCode, '-', result.errorMessage);
        return;
    }

    (result.returnDocuments || []).forEach((doc, i) => {
        if (doc.status === 1) {
            console.log(`Document ${i}: signed ✓  (${doc.docInfo})`);
            // doc.signedDocument contains base64-encoded signed PDF
            // if signedFilePath was set, it's also written to disk
        } else {
            console.log(`Document ${i}: FAILED — ${doc.errorMessage}`);
        }
    });
}

// ── Run examples ──────────────────────────────────────────────────────────────
if (require.main === module) {
    (async () => {
        // Phase 1 demo (comment out when testing Phase 2)
        await phase1().catch(console.error);

        // Phase 2 demo — paste the actual XML from your gateway callback
        // const xml = fs.readFileSync('/path/to/gateway-response.xml', 'utf8');
        // await phase2(xml, '/tmp/esign/<preSignedTempFile>').catch(console.error);
    })();
}

module.exports = ESignClient;
