# Mintdesktop

Desktop configuration tool for MATE and Xfce. Mintdesktop provides some additional settings for the MATE desktop environment and the ability to switch window managers.

![image](https://user-images.githubusercontent.com/19881231/122778484-b6a34900-d2b5-11eb-86d7-bf92f056caac.png)

## Build
Get source code
```
git clone https://github.com/linuxmint/mintdesktop
cd mintdesktop
```
Build
```
dpkg-buildpackage --no-sign
```
Install
```
cd ..
sudo dpkg -i mintdesktop*.deb
```

## Translations
Please use Launchpad to translate Mintdesktop: https://translations.launchpad.net/linuxmint/latest/.

The PO files in this project are imported from there.

## License
- Code: GPLv2
