# SwimCam

   SwimCam is intended to be used as a low cost backup camera system for swim meets. This respository currently hosts the key functional backend components.  There is a basic centralized system to allow to allow remote cameras to locate the master and provide for synchronized time references from the starter to the camera.

## Requirements

While this should build cleanly on most linux distros the primary development has occurred on Raspberry PIs with the HD Camera module. There is no restriction on platform or camera inherent in the code.

Using Raspberry PI 4s

- (All-in One) PI(4GB) w/ 64 GB flash card, HD Camera Module

OR

- (Master) PI(4GB) w/ SSD (future recordings) optional POE hat
- (Lane Camera) PI(2GB) w/ 16GB flash card, POE hat


## Features

- Early development release, features evolving

## Installation

- see ![INSTALL](INSTALL)

## How it works

1. On the main system launch SwimCamMaster.
2. In a separate window launch the starter_simulator
3. Launch the camera system (see ![NOTES](NOTES)) for examples
4. Play the stream with any media player (VLC, etc)

## License
This software is licensed under the GNU Affero General Public License version
3. See the [LICENSE](LICENSE) file for full details.

## Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### [Unreleased]

- :bug: Fixed installer scripts
- :bug: Fixed issue if the start time is after the current frame time

### [0.0.1] - 2021-02-03

- :sparkles: Initial release

