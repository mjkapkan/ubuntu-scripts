# WiFi MAC Address Blacklist Tool for Ubuntu Netowrk Manager

Alows to specify a list of MAC addresses that should be blocked for a list of Wifi Networks. 
This is useful when user has no control over the Access Point (AP) configuration (Workplace, neighbors ands so on) when one or several APs have bad/no connectivity.
This fixes problem described here:
https://ubuntuforums.org/showthread.php?t=2403369

## How it works
Scans available WiFi networks using nmcli, creates a separate network manager config file for each AP MAC adress. 
If network AP is in blacklist, the autoconnect option is set to False, so the network manager will never connect to that network autoamtically.

## Requirements
Python 3+

## Usage
After updating config file or to re-scan for new AP MACs run the script as follows.

```
$ sudo ./wifi_blacklist.py
Usage: [Wifi Name (SSID)] [MAC Address (BSSID) List (comma delimited)]
Or specify text file with the same format: --conf [config file].
Config will be read from first uncommented line.
```
