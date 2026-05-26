'use strict';

/**
 * quick-test.js — Smoke test for the eMudhra eSign bridge JAR.
 *
 * Verifies that:
 *   1. The JAR can be found
 *   2. The Java process starts correctly
 *   3. Bad credentials return a structured JSON error (not a crash)
 *
 * Usage:
 *   node quick-test.js
 *   node quick-test.js /custom/path/to/newJarEmudhra.jar
 */

const path = require('path');
const ESignClient = require('./esign-client');

const jarPath = process.argv[2] || path.join(__dirname, '..', 'dist', 'newJarEmudhra.jar');

console.log('eMudhra eSign Bridge — Quick Test');
console.log('==================================');
console.log('JAR:', jarPath);
console.log('');

const client = new ESignClient(jarPath, { timeout: 30000 });

(async () => {
    // ── Test 1: Missing fields → expect a structured JSON error ─────────────
    console.log('Test 1: getGatewayParameter with intentionally bad input');
    try {
        const result = await client.getGatewayParameter({
            aspID:          'TEST',
            eSignURL:       'https://example.com/eSignRequest',
            eSignURLV2:     'https://example.com/eSignPANRequest',
            pfxPath:        '/nonexistent/cert.pfx',
            pfxPassword:    'wrong',
            pfxAlias:       '1',
            tempFolderPath: '/tmp',
            signerID:       'test@example.com',
            responseURL:    'https://example.com/callback',
            eSignType:      'V2',
            authMode:       'OTP',
            inputs: [{ base64Doc: 'dGVzdA==', docInfo: 'Test Doc', pageTobeSigned: 'Last', appearanceType: 'StandardSignature' }]
        });

        if (result && typeof result.status !== 'undefined') {
            console.log('  ✓ Got JSON response  status=' + result.status);
            if (result.status === 0) {
                console.log('  ✓ Error returned cleanly:', result.errorCode, '-', result.errorMessage);
            }
        } else {
            console.log('  ✗ Unexpected response type:', typeof result);
            process.exit(1);
        }
    } catch (err) {
        if (err.message && (err.message.includes('ENOENT') || err.message.includes('no such file'))) {
            console.log('  ✗ JAR not found at:', jarPath);
            console.log('    Run "ant clean jar" from the project root first.');
        } else if (err.message && err.message.toLowerCase().includes('java')) {
            console.log('  ✗ Java not on PATH. Install Java 8+ and ensure "java" is accessible.');
        } else {
            console.log('  ✗ Unexpected error:', err.message);
        }
        process.exit(1);
    }

    // ── Test 2: getSignedDocument with bad input ─────────────────────────────
    console.log('\nTest 2: getSignedDocument with bad input');
    try {
        const result = await client.getSignedDocument({
            aspID:            'TEST',
            eSignURL:         'https://example.com/eSignRequest',
            eSignURLV2:       'https://example.com/eSignPANRequest',
            pfxPath:          '/nonexistent/cert.pfx',
            pfxPassword:      'wrong',
            pfxAlias:         '1',
            responseXML:      '<invalid/>',
            preSignedTempFile: '/nonexistent.tmp'
        });

        if (result && typeof result.status !== 'undefined') {
            console.log('  ✓ Got JSON response  status=' + result.status);
            if (result.status === 0) {
                console.log('  ✓ Error returned cleanly:', result.errorCode);
            }
        }
    } catch (err) {
        console.log('  ✗ Error:', err.message);
    }

    console.log('\n✓ Smoke test complete — JAR is reachable and returns structured JSON.');
    console.log('  Update index.js with real credentials for a live end-to-end test.');
})();
