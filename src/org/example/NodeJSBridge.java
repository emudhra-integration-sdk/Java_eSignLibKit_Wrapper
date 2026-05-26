package org.example;

import java.io.IOException;

/**
 * CLI Bridge for Node.js to call EmudhraJarFile methods
 * Usage: java -cp jar.jar org.example.NodeJSBridge <methodName> <jsonInput>
 */
public class NodeJSBridge {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: java -cp newJarEmudhra.jar org.example.NodeJSBridge <methodName> <jsonInput>");
            System.err.println("Methods: getGatewayParameter, getSignedDocument");
            System.exit(1);
        }

        String methodName = args[0];
        String jsonInput = args[1];

        try {
            String result = null;

            switch (methodName) {
                case "getGatewayParameter":
                    result = EmudhraJarFile.getGatewayParameterMain(jsonInput);
                    break;

                case "getSignedDocument":
                    result = EmudhraJarFile.getSignedDocMain(jsonInput);
                    break;

                default:
                    System.err.println("Unknown method: " + methodName);
                    System.err.println("Available methods: getGatewayParameter, getSignedDocument");
                    System.exit(1);
            }

            if (result != null) {
                System.out.println(result);
            } else {
                System.err.println("Method returned null");
                System.exit(1);
            }

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
