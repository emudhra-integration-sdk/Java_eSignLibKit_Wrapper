# Contributing

Thank you for taking the time to contribute!

## Ground rules

- This project is a **thin bridge** — business logic belongs in the
  [eMudhra eSign SDK](https://github.com/emudhraltd/java-esign-sdk), not here.
  If you want to add support for a new SDK feature, check whether the SDK itself
  needs to change first.
- All public methods must continue to accept JSON in and return JSON out, and
  must never throw to the caller.
- Keep the source files minimal. Currently there are only three `.java` files;
  adding more should be rare and well-justified.

## Development setup

```bash
git clone https://github.com/emudhraltd/esign-node-bridge.git
cd esign-node-bridge

# 1. Download open-source dependency JARs
.\scripts\download-deps.ps1     # Windows
bash scripts/download-deps.sh   # Linux / macOS

# 2. Build the eMudhra eSign SDK
git clone https://github.com/emudhraltd/java-esign-sdk.git ../java-esign-sdk
cd ../java-esign-sdk && ant clean jar && cd ../esign-node-bridge

# 3. Configure local paths
cp local.properties.example local.properties
# (edit local.properties if your SDK JAR path differs)

# 4. Build the bridge
ant clean jar
```

## Making changes

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b fix/your-fix-name
   ```

2. **Edit** only what is needed. Keep commits focused.

3. **Compile-check** after every change:
   ```bash
   ant jar
   ```

4. **Test manually** using the Java test harness:
   - Update `EmudhraJarFileTest.java` constants with real credentials
   - `ant jar && java -cp "dist/newJarEmudhra.jar;build/classes" org.example.EmudhraJarFileTest`

5. **Test the Node.js client**:
   ```bash
   cd nodejs-esign-client && node quick-test.js
   ```

6. Open a **Pull Request** against `main`. Describe what you changed and why.

## Reporting bugs

Please open a GitHub Issue and include:

- Operating system and Java version (`java -version`)
- Node.js version (if relevant)
- The exact JSON input you passed (redact credentials)
- The full stdout + stderr output
- What you expected vs. what actually happened

## What not to contribute

- Changes to business logic that belong in the SDK
- Bundling proprietary JARs (the eMudhra SDK) into the repository
- Breaking changes to the JSON API schema without a version bump
