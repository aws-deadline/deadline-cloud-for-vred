# AWS Deadline Cloud for VRED

[![pypi](https://img.shields.io/pypi/v/deadline-cloud-for-vred.svg?style=flat)](https://pypi.python.org/pypi/deadline-cloud-for-vred)
[![python](https://img.shields.io/pypi/pyversions/deadline-cloud-for-vred.svg?style=flat)](https://pypi.python.org/pypi/deadline-cloud-for-vred)
[![license](https://img.shields.io/pypi/l/deadline-cloud-for-vred.svg?style=flat)](https://github.com/aws-deadline/deadline-cloud-for-vred/blob/mainline/LICENSE)

AWS Deadline Cloud for VRED is a Python-based package that supports creating and running Autodesk VRED render jobs
within [AWS Deadline Cloud][deadline-cloud]. It provides a user-friendly VRED submitter plug-in for your Windows-based
workstation. You can choose from a set of common render options and offload the computation of your rendering
workloads to [AWS Deadline Cloud][deadline-cloud] to reduce the load on local compute resources to pursue other tasks.

[aws-cli-credentials]: https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-authentication.html

[deadline-cloud]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/what-is-deadline-cloud.html

[deadline-cloud-client]: https://github.com/aws-deadline/deadline-cloud

[deadline-cloud-monitor-setup]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/submitter.html#install-deadline-cloud-monitor

[deadline-cloud-for-vred]: https://github.com/aws-deadline/deadline-cloud-for-vred

[default-queue-environment]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/create-queue-environment.html#conda-queue-environment

[job-bundle]: https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/build-job-bundle.html

[job-bundle-templates]: https://github.com/aws-deadline/deadline-cloud-samples/tree/mainline/job_bundles

[openjd]: https://github.com/OpenJobDescription/openjd-specifications/wiki

[service-managed-fleets]: https://docs.aws.amazon.com/deadline-cloud/latest/userguide/smf-manage.html

[vred-requirements]: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/System-requirements-for-Autodesk-VRED-2026-products.html

## Compatibility

The AWS Deadline Cloud for VRED package requires:

1. VRED Pro or VRED Core 2025/2026 and its [requirements][vred-requirements]
    - Note: at the time of writing, it is strongly recommended to use NVIDIA GPU driver 553.xx  (until future
      driver
      levels pass hardware qualifications for VRED.)
2. Python 3.11 or higher;
3. Operating System support:
    - Windows 10+ (for the in-app VRED Submitter plugin, Worker, Standalone AWS Deadline Cloud client submitter)
    - Linux (for the Worker, Standalone AWS Deadline Cloud client Submitter)
    - macOS (for the Standalone AWS Deadline Cloud client Submitter)
4. Optionally: [ImageMagick](https://imagemagick.org/) static binary (to support tile assembly when region rendering
   with raytracing is applied).

**Important**: This integration of AWS Deadline Cloud into VRED requires **bring your own licensing (BYOL)** for VRED.
You must have valid VRED licenses available for your render farm fleet.

## Versioning

This package's version follows [Semantic Versioning 2.0](https://semver.org/), but it is still considered to be in its
initial development, thus backwards incompatible versions are denoted by minor version bumps. To help illustrate how
versions will increment during this initial development stage, they are described below:

1. The MAJOR version is currently 0, indicating initial development.
2. The MINOR version is currently incremented when backwards incompatible changes are introduced to the public API.
3. The PATCH version is currently incremented when bug fixes or backwards compatible changes are introduced to the
   public API.

## Getting Started

This VRED integration for AWS Deadline Cloud provides an in-app Submitter plug-in. It must be installed on the
Windows workstation that you will use to submit render jobs from within VRED Pro.

Before submitting any large, complex, or otherwise compute-heavy VRED render jobs to your farm, we strongly
recommend that you construct a simple test scene file that can be rendered quickly. You can then submit renders of that
scene to your render farm fleet to ensure that its setup is correctly functioning.

### VRED Submitter Plug-in

The VRED Submitter plug-in creates a menu (Deadline Cloud) and menu item (Submit to Deadline Cloud) in VRED's
menu bar, which can be used to submit render jobs to AWS Deadline Cloud. This menu item launches a Submitter UI to
create a job submission for AWS Deadline Cloud using the [AWS Deadline Cloud client library][deadline-cloud-client].
It automatically determines the files required for submission based on the loaded scene file (includes Source/Smart
references as dependencies.) Additionally, the Submitter provides basic render options (in the Job-specific settings
tab), and builds an [Open Job Description template][openjd] that defines the render pipeline workflow. From there, the
Submitter submits the render job to the render farm queue and fleet of your choice.

#### Prerequisites

1. Install the required applications:
    - VRED Pro 2025/2026 [Autodesk](https://manage.autodesk.com)
    - [Deadline Cloud Client][deadline-cloud-client]
    - [Deadline Cloud Monitor](https://docs.aws.amazon.com/deadline-cloud/latest/userguide/open-deadline-cloud-monitor.html)

2. Open Deadline Cloud Monitor and perform sign-in on an appropriate profile (see instructions below).

#### Submitter (Manual Installation Steps)

If you are not using an installer package for installing the Submitter, then you can install it by applying the
following manual installation steps (below). For the instructions that follow, change the directory names as
appropriate to correspond to the VRED installation where you would like to install the Submitter. For example, for VRED
Core 2026, the 18.X numbering convention was applied to the VREDCore-18.0 portion of the path.

1. Fetch the latest AWS Deadline Cloud for VRED code:
   ```cmd
   git clone https://github.com/aws-deadline/deadline-cloud-for-vred
   cd deadline-cloud-for-vred
   # Note: for updates: git fetch
   ```

2. Install the Submitter plug-in:
    - Create submitter installation directories:
   ```cmd
   mkdir C:\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline
   # or
   mkdir %USERPROFILE%\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline
   ```
    - Copy `vred_submitter_plugin/plug-ins/DeadlineCloudForVRED.py` to VRED's Python libraries directory:
        - For VRED Core: `C:\Program Files\Autodesk\VREDCore-18.0\lib\python\Lib\site-packages`
        - For VRED Pro: `C:\Program Files\Autodesk\VREDPro-18.0\lib\python\Lib\site-packages`
    - Copy `src/deadline/vred_submitter` to your Deadline Cloud submitter directory:
      `C:\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline` or
      `%USERPROFILE%\DeadlineCloudSubmitter\Submitters\VRED\scripts\deadline`

3. Set environment variables (examples for VRED Pro and VRED Core 2026):
   ```cmd
   # For VRED Core
   setx VREDCORE "C:\Program Files\Autodesk\VREDCore-18.0\bin\WIN64\VREDCore.exe"
   # or for VRED Pro
   setx VREDPRO "C:\Program Files\Autodesk\VREDPro-18.0\bin\WIN64\VREDPro.exe"
   ```
4. Supply AWS account credentials for the submitter to use when submitting a render job through either of these steps:
    - [Install and set up the Deadline Cloud Monitor][deadline-cloud-monitor-setup], and then log in to the monitor.
      (Logging in to the monitor will make AWS credentials available to the submitter, automatically.)
    - Set up an AWS credentials profile [as you would for the AWS CLI][aws-cli-credentials], and select that profile
      for the submitter to use.
    - Or default to your AWS EC2 instance profile credentials if you are running a workstation in the cloud.

5. Configure the VRED Submitter plug-in to load on startup.
    - Start VRED Pro and click on these items: `Edit menu → Preferences → General Settings → Script`
    - Please ensure that the `Enable Python Sandbox` option is unchecked.
    - In the `Script` section, scroll to the bottom and append:
      ```python
      from DeadlineCloudForVRED import DeadlineCloudForVRED
      DeadlineCloudForVRED()
      ```
    - Click the `Save` button

6. Logout and login to refresh environment variables.

#### Optional: Submitter Post-Installation Steps

The following steps are NOT required or recommended in regular practice:

- **Enable VRED's Python Sandbox (this is NOT recommended, since AWS Deadline Cloud requires network and file access by
  default):**
    - Start VRED Pro and click on these items: `Edit menu → Preferences → General Settings → Script`
    - In the `Python Sandbox` section, ensure that `Enable Python Sandbox` is enabled
    - Copy the contents of `python-sandbox-module-allowlist.txt` from this repository into the `Allowed Modules` text
      box
    - Click the `Save` button

- **If the AWS Deadline Cloud for VRED Python installation is missing, then copy another Submitter's Python
  installation:**

  ```cmd
  Copy the contents of C:\DeadlineCloudSubmitter\Submitters\Blender\Python to:
  C:\DeadlineCloudSubmitter\Submitters\VRED\Python
  
  Alternatively, copy the contents of %USERPROFILE%\DeadlineCloudSubmitter\Submitters\Blender\Python to:
  %USERPROFILE%\DeadlineCloudSubmitter\Submitters\VRED\Python
  ```

#### Launching the Submitter

1. Open VRED.
2. Open a VRED scene file.
3. Open the `Deadline Cloud` menu and click the `Submit to Deadline Cloud` menu item to launch the Submitter.

   **Note**: If you have not already authenticated with Deadline Cloud, then the `Authentication Status` section at the
   bottom of the Submitter will show `NEEDS_LOGIN`.

   a) Click the `Login` button. Then, in the web browser window that appears, authenticate using your IAM user
   credentials.

   b) Click the `Allow` button (your login will then be authenticated and the `Authentication Status` section will show `
   AUTHENTICATED`).

4. In the `Submit to AWS Deadline Cloud` dialog, configure appropriate settings (including the render settings that are
   listed in the `Job-specific settings` tab).
5. Click the `Submit` button to submit your render job to AWS Deadline Cloud.

### VRED Software Availability in AWS Deadline Cloud Service Managed Fleets

Please ensure that the version of VRED that you want to run is also available on the fleet (worker nodes) when you are
using AWS Deadline Cloud's [Service Managed Fleets][service-managed-fleets] to run render jobs; these fleet hosts do
not have any rendering applications pre-installed. The standard way of installing applications is
described [in the service
documentation](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/provide-applications.html).

**Licensing Requirements**: VRED requires valid BYOL licenses on all worker nodes. You must configure your license
server to be accessible from your render farm, ensuring that licenses are available for concurrent rendering tasks.

## Submitter Interfaces

The VRED Submitter provides multiple interfaces for configuring render jobs. These interfaces will vary slightly
since the values for certain settings (including animation clips and viewpoints/cameras) are only known during runtime
(within VRED).

### Submitter GUI (within VRED)

Settings applied in this interface will persist for the entire duration that a given scene file is open (this includes
closing and reopening the Submitter window). Initial settings in the Submitter UI are populated from VRED's general
render options (which are saved in the scene file). Saving the scene file won't persist the Submitter UI options, but
certain options (including frame range to render) will be repopulated if saved in VRED's general render settings.

![VRED Submitter Dialog](VRED-Submitter-Dialog.png)

### Standalone Submitter (external to VRED)

This interface can be accessed via command line and offers most of the options presented in the Submitter GUI.

![VRED Standalone Submitter Dialog](VRED-Standalone-Submitter-Dialog.png)

### Description of Interface Options

Below are descriptions of the options available in both of the above interfaces.

### Render Options

- **Output Directory (Render Output)**: Directory where rendered images will be saved
- **Output Filename (Render Output)**: Base name for output files (without filename extension)
- **Output File Format (Render Output)**: Image format (PNG, EXR, JPEG, TIFF, etc.)
- **Render Viewpoint/Camera**: Name of the viewpoint or camera from which to render
- **Image Size Presets**: The available presets for image size and resolution (HD 1080, 4K, etc.)
- **Image Size**: Width and height in pixels; can be set via Image Size Presets setting (HD 1080, 4K, etc.)
- **Printing Size**: The printing size in centimeters (width and height), influences image size.
- **Resolution (DPI)**: Dots-per-inch scaling factor, influences image size.
- **Render Quality**: Quality level (Analytic Low/High, Realistic Low/High, Raytracing, Non-Photorealistic (NPR))
- **DLSS Quality**: Deep Learning Super Sampling quality (Off, Performance, Balanced, Quality, Ultra Performance)
- **SS Quality**: Super Sampling quality (Off, Low, Medium, High, Ultra High); overridden by DLSS quality setting
- **Use GPU Ray Tracing**: Enable GPU-accelerated raytracing (if hardware supports it)

### Animation Options

- **Render Animation**: If checked, allows specifying an animation type (which can also include a specific animation
  clip), corresponding frame range and frames per task.
- **Animation Type**: The type of animation (Clip or Timeline).
- **Animation Clip**: The name of the animation clip to render
- **Frame Range (Start Frame, End Frame, Frame Step)**: Start and end frames with optional step size. (format:
  'a', 'a-b', or 'a-bxn', where 'a' is the start frame, 'b' is the end frame, and 'n' is the frame step). Negative
  frames are supported.
- **Frames Per Task**: The number of frames that will be rendered at a time for each task within a render job.

### Tiling Settings

- **Enable Region Rendering**: When enabled, the rendered output image will be divided into multiple tiles
  (subregions) that are first rendered as separate tasks for a given frame. These tiles will then be assembled
  (combined) into one output image for a given frame (in a separate step).
- **Tiles in X/Y**: Number of horizontal/vertical tiles to divide the specified rendered output image for a given frame

**Important**: Region rendering (tiling) is designed for scene files that have been configured for Raytracing.
Raytracing will automatically be enabled when using this setting. Applying region rendering to scene files that aren't
configured for Raytracing may result in solid black-rendered output.

### Invoking the Standalone Submitter

The standalone submitter is invoked via command line and relies on the following environment variables, which you can
substitute with appropriate values:

```bash
# Windows
set FARM_ID=farm-<farm-id>
set QUEUE_ID=queue-<queue-id>
set FLEET_ID=fleet-<fleet-id>
deadline bundle gui-submit .

# Linux
export FARM_ID=farm-<farm-id>
export QUEUE_ID=queue-<queue-id>
export FLEET_ID=fleet-<fleet-id>
deadline bundle gui-submit .
```

## Viewing/Submitting a Job Bundle

Before submitting a render job, the Submitter first generates a [Job Bundle][job-bundle], and then relies on the
[AWS Deadline Cloud Client][deadline-cloud-client] package to submit that Job Bundle to a specified render farm. If you
would like to examine that job bundle, then you can use the `Export Bundle` button in the Submitter to export the Job
Bundle to a location of your choice. If you want to submit the exported Job Bundle manually outside VRED, then you
can use the Standalone [AWS Deadline Cloud Client][deadline-cloud-client] to submit that same Job Bundle to your
specified render farm in a platform-agnostic manner.

Standalone [AWS Deadline Cloud Client][deadline-cloud-client] render jobs should use the appropriate Job Bundle
Template obtained through this [link][job-bundle-templates]. There, you will find one Job Bundle Template for
supporting tile-based rendering (tile_render_vred/template.yaml) and another Job Bundle Template for non-tile rendering
(vred_render/template.yaml). When submitting a render job that doesn't rely on tiling, you can use the standard job
Please also ensure that your Job Bundle directory has a `scripts` subdirectory containing
`VRED_RenderScript_DeadlineCloud.py`, which is a required pipeline rendering component for the job bundle. You
should also include `parameter_values.yaml` (values for the fields defined in the Job Bundle Template) and
`asset_references.yaml` (for defining file dependencies).

## Optional: Worker Setup - Customer Managed Fleet (CMF) (for Windows and Linux only)

While using AWS' Service Managed Fleet (SMF) is highly recommended, you can also set up a customer managed fleet (CMF)
worker for your own farm using the steps below:

1. Create your own farm in the AWS Console (under the `AWS Deadline Cloud` service). Note the Farm ID, Fleet ID, and
   AWS Region (substituting them in step 3).

2. Install the `AWS Deadline Cloud` worker agent:
   ```
   pip install deadline-cloud-worker-agent
   ```

3. Configure the worker agent in `C:\ProgramData\Amazon\Deadline\Config\worker.toml` or similar (and substitute the
   field values below):
   ```toml 
   farm_id = "farm-<farm-id>"
   fleet_id = "fleet-<fleet-id>"
   profile = "<my_aws_profile_name>"
   worker_logs_dir = "c:/users/username/desktop"
   
   [capabilities.amounts]
   "amount.attr.worker.gpu" = 1
   ```

4. Switch to the AWS profile (substitute below) that was used to create the farm.
   ```batch
   # on Windows:
   set AWS_PROFILE=my_deadline_profile
   # on Linux:
   export AWS_PROFILE=my_deadline_profile
   ```

5. Create a batch file to continually re-run worker agent:

   (Windows: create run-worker.bat)
   ```batch
   :do
   python -m deadline_worker_agent --run-jobs-as-agent-user
   goto do
   ```

   (Linux: create run-worker.sh)
   ```batch
   #!/bin/sh
   while true; do
       python -m deadline_worker_agent --run-jobs-as-agent-user
   done
   ```

   ```cmd
   chmod +x run-worker.sh
   ```

6. Optional: Follow the instructions in the [ImageMagick Installation](#imagemagick-installation) section (if you would
   like to support region rendering/tiling)

7. Run the worker: `run-worker.bat` (Windows), `./run-worker.sh` (Linux)

## [ImageMagick Installation](#imagemagick-installation)

For render jobs using region rendering (tiling), ImageMagick must be installed on the worker nodes:

### Windows

1. Visit the ImageMagick downloads
   page [https://imagemagick.org/script/download.php](https://imagemagick.org/script/download.php)
2. Download and install the 64-bit static binary release
3. Set the `MAGICK` environment variable as appropriate (depending on installation path/version):
   ```cmd
   setx MAGICK "C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe"
   ```
4. Logout, login.

### Linux

**Important**: use a static ImageMagick binary to prevent missing file format decoder dependency issues:

1. Apply the commands below, adjusting the `MAGICK` environment variable as appropriate (depending on ImageMagick
   binary path/version):

```
wget https://imagemagick.org/archive/binaries/magick
chmod 755 magick
yum install fontconfig libX11 fribidi  # or dnf install fontconfig libX11 fribidi
export MAGICK=$PWD/magick
```

You can also add these steps (above) to an existing Conda package (or make another one) and reference that package's
name in the render job submission (under the `Conda Packages` setting). At the time of writing, Customer
Managed Fleet (CMF) instances only support tiling since there isn't yet an official Conda package that provides
a static ImageMagick binary (including dependencies) on Linux. However, it is possible to create that Conda package.

**IMPORTANT**: Without ImageMagick, tile assembly will fail and region rendering jobs will not complete successfully.

## Environment Variables

The following environment variables can be used to configure the Submitter amd:

### Environment Variables for VRED Submitter

##### Optional

- `CONDA_CHANNELS`: Override default conda channels for job environments (example: `s3://conda-bucket/Conda/linux-64`)
- `CONDA_PACKAGES`: Override default conda packages (example: `vredcore=2026*`)

### Environment Variables for Fleet/Worker Nodes

One of these environment variables must be set:

- `VREDCORE`: Path (including filename) to VRED Core executable (takes precedence if VREDPRO environment variable is
  also set)
- `VREDPRO`: Path (including filename) to VRED Pro executable

##### Optional

- `VRED_DISABLE_WEBINTERFACE`: Disable VRED web interface (enabled by default)
- `VRED_IDLE_LICENSE_TIME`: License release timeout in seconds (set to "60" by default)
- `FLEXLM_DIAGNOSTICS`: FlexLM diagnostic level for licensing (set to "3" by default)

### Environment Variables for Tile Assembly

- `MAGICK`: Path to ImageMagick static binary executable (required for region rendering jobs)

## Troubleshooting

In general, the AWS Deadline Cloud Monitor provides valuable insights into the activities that occurred while a worker
node was processing a VRED scene file. Logs from these activities can be generated and shared with support teams. 
Depending on the scope/nature of an issue, there may be additional avenues worth investigating. Below are 
suggestions.

### Common Issues

1. **Worker Reports that VRED Executable is not Found**
    - Verify the setting of the VREDCORE or VREDPRO environment variables
    - Check VRED installation path and permissions

2. **VRED Hangs at Startup or lists "builtins.builtins.exec blocked by python sandbox"**
    - Load VRED using the `-insecure_python` program argument, disable Python Sandbox in VRED's preferences.
    - Alternatively, if you must use VRED's Python Sandbox (against our recommendations), then verify that the Python
      module allowlist (`python-sandbox-module-allowlist.txt`) had its contents entered into VRED's preferences.
    - Verify that your Job Bundle Template is applying the `-insecure_python` program argument
    - On Windows, check VRED logs in `%TEMP%\VREDPro\log`
   
3. **VRED Submitter Menu is Missing**
    - Ensure that DeadlineCloudForVRED.py is in the correct directory for the version of VRED being used
    - Ensure that DeadlineCloudForVRED.py is listed in VRED's Preferences screen:
        - `Edit menu → Preferences → General Settings → Script`
    - Ensure that AWS Deadline Cloud for VRED was installed correctly
    - Check the VRED Console for any unusual errors

4. **Worker is Producing Unusual Crashes**
    - Ensure that the worker has ample resources (CPU and GPU memory) for processing the scene file in question
        - For SMF workers, define appropriate render farm resource requirements and update your host requirements
          configuration:
        - Target ample resources:
            - GPU: A10G, L4, L40S. 24-48GB of GPU memory
            - CPU RAM: 32GB-64GB
            - Try to leverage G5, G6, and G6e machine instance families.
        - For CMF workers, define similar render farm resource requirements (to those above) and update your host
          requirements configuration.

5. **Tile Assembly Failed**
    - Verify that ImageMagick is installed and that the `MAGICK` environment variable is set on the worker node
    - Check ImageMagick executable permissions
    - Ensure sufficient disk space for tile processing

6. **Rendering Process is Slow**
   - Verify that OpenGL hardware acceleration is enabled and functional
   - Verify that ample hardware resources are allocated
   - Consider tile rendering your scene file
   - Allocate ample worker nodes
   - Disable GPU Raytracing (if not required)
   - Scale down quality level and image resolution

7. **VRED Licensing Issues**
   ```
   License checkout failed
   ```
    - Verify VRED license server accessibility
    - Check available floating licenses
    - Ensure license server can handle concurrent requests from render farm
    - Check diagnostic worker output feedback in Deadline Cloud Monitor

### VRED Rendering Issues (Detailed)

1. **Raytraced Renders Appear Solid Black**
   - Verify that the scene file is configured for Raytracing
   - Region rendering requires Raytracing for proper tile generation
   - Check render quality settings in the scene file
   - Verify that X Server is correctly configured and operational when rendering on Linux
   - **Lighting**: Raytracing requires proper light sources
      - consider increasing light intensity 5-10x or add area lights/HDR environment
   - **Materials**: Verify materials have proper diffuse colors and raytracing-compatible properties
   - **Camera**: Check exposure settings and camera position
   - **Quick fix**: Add area light and verify that materials aren't pure black

2. **Region-based Rendering/Tiling Appears Solid Black**
   - Render regions only work with raytracing enabled in VRED and will be enabled by default (see the above scenario) 

3. **Rendered Output Colors Appear Inconsistent on Windows v.s. Linux**
   - Check the tone mapper being applied to the rendered Camera/view.
   - Try changing the tone mapper and all Color Space/Range-related settings to the sRGB/Reinhard/Linear color space. 
   - Use a compatible/hardware qualified NVIDIA driver level (553.xx)
   - Consider distributing ICC monitor profile (if necessary) per Autodesk recommendations
   
## Security

We take all security reports seriously. When we receive such reports, we will investigate and subsequently address any
potential vulnerabilities as quickly as possible. If you discover a potential security issue in this project, please
notify AWS/Amazon Security via
our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/) or directly via email
to [AWS Security](mailto:aws-security@amazon.com). Please do not create a public GitHub issue in this project.

## Telemetry

See [telemetry](https://github.com/aws-deadline/deadline-cloud-for-vred/blob/release/docs/telemetry.md) for more
information.

## License

This project is licensed under the Apache-2.0 License.