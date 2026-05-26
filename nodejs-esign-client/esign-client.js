'use strict';

const { spawn } = require('child_process');
const path = require('path');

/**
 * ESignClient — Node.js wrapper for the eMudhra eSign Java bridge.
 *
 * Spawns the JAR as a child process, passes JSON on the command line,
 * and returns the parsed JSON response. Requires Java 8+ on PATH.
 *
 * @example
 * const ESignClient = require('./esign-client');
 * const client = new ESignClient('/path/to/newJarEmudhra.jar');
 * const result = await client.getGatewayParameter({ ... });
 */
class ESignClient {
    /**
     * @param {string} [jarPath] - Absolute path to newJarEmudhra.jar.
     *   Defaults to ../dist/newJarEmudhra.jar relative to this file.
     * @param {object} [options]
     * @param {string} [options.javaExecutable='java'] - Java executable to use.
     * @param {number} [options.timeout=120000] - Process timeout in ms (0 = no timeout).
     */
    constructor(jarPath, options = {}) {
        this.jarPath = jarPath || path.join(__dirname, '..', 'dist', 'newJarEmudhra.jar');
        this.javaExecutable = options.javaExecutable || 'java';
        this.timeout = options.timeout !== undefined ? options.timeout : 120000;
    }

    /**
     * Low-level: spawn the Java bridge and return the parsed JSON response.
     *
     * @param {'getGatewayParameter'|'getSignedDocument'} methodName
     * @param {object} inputData
     * @returns {Promise<object>}
     */
    executeMethod(methodName, inputData) {
        return new Promise((resolve, reject) => {
            const inputJson = JSON.stringify(inputData);
            let timer;

            const proc = spawn(this.javaExecutable, [
                '-cp', this.jarPath,
                'org.example.NodeJSBridge',
                methodName,
                inputJson
            ]);

            if (this.timeout > 0) {
                timer = setTimeout(() => {
                    proc.kill();
                    reject(new Error(`Java process timed out after ${this.timeout}ms`));
                }, this.timeout);
            }

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => { stdout += data.toString(); });
            proc.stderr.on('data', (data) => { stderr += data.toString(); });

            proc.on('close', (code) => {
                if (timer) clearTimeout(timer);

                if (code !== 0) {
                    return reject(new Error(
                        `Java process exited with code ${code}\nstderr: ${stderr.trim()}`
                    ));
                }

                const raw = stdout.trim();
                try {
                    resolve(JSON.parse(raw));
                } catch (e) {
                    reject(new Error(
                        `Java returned non-JSON output: ${raw}\nstderr: ${stderr.trim()}`
                    ));
                }
            });

            proc.on('error', (err) => {
                if (timer) clearTimeout(timer);
                reject(new Error(
                    `Failed to start Java process ('${this.javaExecutable}'): ${err.message}`
                ));
            });
        });
    }

    /**
     * Phase 1 — Initiate signing.
     *
     * Sends the document(s) to the eMudhra gateway and returns the
     * gateway redirect parameter and a temp-file path needed for Phase 2.
     *
     * @param {object} config
     * @param {string} config.aspID              - eMudhra ASP ID
     * @param {string} config.eSignURL           - Gateway V2 (Aadhaar) URL
     * @param {string} config.eSignURLV2         - Gateway V3 (PAN) URL
     * @param {string} config.pfxPath            - Path to signing PFX certificate
     * @param {string} config.pfxPassword        - PFX password
     * @param {string} config.pfxAlias           - PFX alias (usually "1")
     * @param {string} config.tempFolderPath     - Writable temp folder
     * @param {string} config.signerID           - Signer email / identifier
     * @param {string} config.responseURL        - Callback URL for gateway response
     * @param {string} [config.redirectUrl]      - Redirect URL (falls back to responseURL)
     * @param {string} [config.transactionID]    - Your transaction ID (optional)
     * @param {'V2'|'V3'} [config.eSignType='V2'] - API version
     * @param {string} [config.authMode='OTP']   - Auth mode: OTP|FingerPrint|IRIS|FaceRecognition
     * @param {Array}  config.inputs             - Array of document objects (see README)
     * @param {boolean} [config.proxyReq=false]
     * @param {string}  [config.proxyIp]
     * @param {number}  [config.proxyPort]
     * @param {string}  [config.proxyUserID]
     * @param {string}  [config.proxyUserPassword]
     * @param {number}  [config.sessionTimeout=0]
     * @param {number}  [config.signatureContents=0]
     * @returns {Promise<object>} eSignServiceReturn serialized as JSON
     */
    async getGatewayParameter(config) {
        const payload = {
            aspID:              config.aspID,
            eSignURL:           config.eSignURL,
            eSignURLV2:         config.eSignURLV2,
            pfxPath:            config.pfxPath,
            pfxPassword:        config.pfxPassword,
            pfxAlias:           config.pfxAlias,
            tempFolderPath:     config.tempFolderPath,
            signerID:           config.signerID,
            responseURL:        config.responseURL,
            redirectUrl:        config.redirectUrl || config.responseURL,
            transactionID:      config.transactionID || '',
            eSignType:          config.eSignType || 'V2',
            authMode:           config.authMode || 'OTP',
            inputs:             config.inputs || [],
            proxyReq:           config.proxyReq || false,
            proxyIp:            config.proxyIp || '',
            proxyPort:          config.proxyPort || 0,
            proxyUserID:        config.proxyUserID || '',
            proxyUserPassword:  config.proxyUserPassword || '',
            sessionTimeout:     config.sessionTimeout || 0,
            signatureContents:  config.signatureContents || 0
        };
        return this.executeMethod('getGatewayParameter', payload);
    }

    /**
     * Phase 2 — Retrieve signed document.
     *
     * Called after the user completes signing at the gateway.
     * Pass the XML from the gateway callback and the temp file path
     * returned by Phase 1.
     *
     * @param {object} config
     * @param {string} config.aspID              - eMudhra ASP ID
     * @param {string} config.eSignURL           - Gateway V2 URL
     * @param {string} config.eSignURLV2         - Gateway V3 URL
     * @param {string} config.pfxPath
     * @param {string} config.pfxPassword
     * @param {string} config.pfxAlias
     * @param {string} config.responseXML        - Full XML from gateway callback
     * @param {string} config.preSignedTempFile  - Temp file path from Phase 1 response
     * @param {string} [config.signedFilePath]   - Base path to write signed PDFs on disk
     *   e.g. '/output/signed-' → writes '/output/signed-0.pdf', '/output/signed-1.pdf', …
     *   Omit to skip file writing; signed data is in the JSON response.
     * @param {boolean} [config.proxyReq=false]
     * @param {string}  [config.proxyIp]
     * @param {number}  [config.proxyPort]
     * @param {string}  [config.proxyUserID]
     * @param {string}  [config.proxyUserPassword]
     * @param {number}  [config.sessionTimeout=0]
     * @param {number}  [config.signatureContents=0]
     * @returns {Promise<object>} eSignServiceReturn serialized as JSON
     */
    async getSignedDocument(config) {
        const payload = {
            aspID:              config.aspID,
            eSignURL:           config.eSignURL,
            eSignURLV2:         config.eSignURLV2,
            pfxPath:            config.pfxPath,
            pfxPassword:        config.pfxPassword,
            pfxAlias:           config.pfxAlias,
            responseXML:        config.responseXML,
            preSignedTempFile:  config.preSignedTempFile,
            signedFilePath:     config.signedFilePath || '',
            proxyReq:           config.proxyReq || false,
            proxyIp:            config.proxyIp || '',
            proxyPort:          config.proxyPort || 0,
            proxyUserID:        config.proxyUserID || '',
            proxyUserPassword:  config.proxyUserPassword || '',
            sessionTimeout:     config.sessionTimeout || 0,
            signatureContents:  config.signatureContents || 0
        };
        return this.executeMethod('getSignedDocument', payload);
    }
}

module.exports = ESignClient;
