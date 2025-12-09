# Installation

To install the AWS Deadline Cloud submitter for Autodesk VRED, prepare the following environment:

- Windows 10+ workstation
- VRED Pro 2025 or 2026 installation
- Python 3.11 or higher
- Access to an AWS Deadline Cloud farm with either:
    - A service-managed fleet with VRED software and licensing configured
    - A customer-managed fleet with VRED and licensing set up

**Important**: AWS Deadline Cloud for VRED requires bring your own licensing (BYOL). You must have valid VRED licenses available for your render farm fleet.

## Installing the submitter

The Autodesk VRED submitter plugin allows you to submit jobs to Deadline Cloud directly from within VRED. To install the submitter:

1. Download the [official Deadline Cloud submitter installer](https://docs.aws.amazon.com/deadline-cloud/latest/userguide/submitter.html).
2. Run the installer and follow the on-screen instructions.
3. Open VRED Pro.
4. Choose **Edit** > **Preferences**.
5. In the Preferences window, select **General Settings**, and then choose **Script**.
6. Verify the **Enable Python Sandbox** option is not selected.
7. In the Script section, add the following text to the end of the section:

    ```python
    from DeadlineCloudForVRED import DeadlineCloudForVRED
    DeadlineCloudForVRED()
    ```

8. Choose **Save**.
9. Restart VRED Pro. When VRED opens, the **Deadline Cloud** menu displays in the menu bar.

For manual installation or developer workflows, see the [DEVELOPMENT.md](https://github.com/aws-deadline/deadline-cloud-for-vred/blob/mainline/DEVELOPMENT.md) file.

## Updating the submitter

To update the submitter to the latest version, download and run the latest submitter installer.
