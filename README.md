sony_qx_controller
==================

Python script which allows to manage Sony QX100 or Sony QX10 from PC and use ALL API (undocumented API also).


How to use:

Before using this script: manually connect to Wi-Fi; set up IP 10.0.1.1, mask 255.0.0.0 (and if that's not enough - default gateway: 10.0.0.1).

Note. Password can be taken from a text file in the internal memory of the device, connect it with USB and switch on for accessing this memory.

This script depends on PyQt4 for displaying liveview. On Ubuntu just run command: apt-get install python3-pyqt4
