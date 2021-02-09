.. include:: common.rst
=======
SwimCam
=======

.. https://docutils.sourceforge.io/docs/user/rst/quickref.html
.. https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html
.. https://docutils.sourceforge.io/docs/ref/rst/directives.html

.. toctree::
   :caption: Contents
   :hidden:
   :titlesonly:
   :includehidden:

   self
   configuration
   simulator

|sc| is intended to be used as a low cost backup camera system for swim meets. This respository currently hosts the key functional backend components.  There is a basic centralized system to allow to allow remote cameras to locate the master and provide for synchronized time references from the starter to the camera.real-time.

.. image:: media/demo1.png
   :alt: Example image


Features
========

The |sc| system is customizable to varying degrees of timing accuracy
based on the hardware available

- Configurable number of lanes (4 - 10)
- All cameras are time synchronized
- Designed to run without internet access on closed networks
- Circuit designs for various starters and primary timing sources

Requirements
============

While this should build cleanly on most linux distros the primary development has occurred on Raspberry PIs with the HD Camera module. There is no restriction on platform or camera inherent in the code.

Using Raspberry PI 4s

- (All-in One) PI(4GB) w/ 64 GB flash card, HD Camera Module

OR

- (Master) PI(4GB) w/ SSD (future recordings) optional POE hat
- (Lane Camera) PI(2GB) w/ 16GB flash card, POE hat

License
=======

|sc| is free, open-source software that you can download and use.
The software is licensed under the GNU Affero General Public License, version
3.

If you are interested in contributing, `check out the project's repository on
GitHub. <https://github.com/dmanuxrex/swimcam>`_:

- View the latest releases
- File bug reports
- Download the source code
- Contribute enhancements


