Pre-Release Version 0.1 Notes

   SwimCam is intended to be used as a low cost backup camera system for swim meets. This initial drop allows for image capture, processing and streaming via RTSP.  There is a basic centralized system to allow to allow remote cameras to locate the master and provide for synchronized time references from the starter to the camera.


   While this should build cleaning on most linux distros the primary development has occurred on Raspberry PIs with the HD Camera module.

   For a development setup you will need (at a minimum):

   Raspberry PI 4 (4GB)
   Min 64GB flash card
   Raspberry PI HD Camera module

   A "production" environment would comprise:

   PI4 (2GB), POE HAT, HD Camera for each lane you wish to record
   PI4 (4GB), POE HAT (Optional), SSD for the main recording/playback system

Documents:

INSTALL - Basic installation, setup and operation
PIPELINES - Sample camera pipelines for various platforms
NOTES - Some general notes on the current development and known issues

