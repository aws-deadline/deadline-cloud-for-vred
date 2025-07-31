### Submitter Installer Development Workflow
#### Build the package

```bash
hatch run build
```

#### Build the installer

```bash
hatch run installer:build-installer --local-dev-build --platform <PLATFORM> [--install-builder-location <LOCATION> --output-dir <DIR>]
```

Run `hatch run installer:build-installer -h` to see the full list of arguments.


#### Test a local installer
```bash
hatch run test-installer
```