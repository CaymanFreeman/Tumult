<p align="center">
  <img src="assets/icon.png" width="256" height="256" alt="Tumult Logo">
</p>

<div id="toc" align="center">
  <ul style="list-style: none;">
    <summary>
      <h1 align="center">
        Tumult
      </h1>
    </summary>
  </ul>
</div>

<h3 align="center">
  A server-client chatting application
</h3>

<p align="center">
  <a href="https://github.com/CaymanFreeman/Tumult/blob/main/LICENSE.md"><img alt="MIT License" src="https://img.shields.io/github/license/CaymanFreeman/Tumult?style=flat&color=%23B20D35"></a>&nbsp;
  <a href="https://www.python.org/"><img alt="Built With Python" src="https://img.shields.io/badge/built_with-Python-brightgreen&style=flat"></a>&nbsp;
  <a href="https://github.com/CaymanFreeman/Tumult/releases"><img alt="Release" src="https://img.shields.io/github/v/release/CaymanFreeman/Tumult?include_prereleases&display_name=release&style=flat&color=%239d69c3"></a>&nbsp;
  <a href="https://www.linkedin.com/in/caymanfreeman/"><img alt="linkedin" src="https://img.shields.io/badge/linkedin-Connect_with_me-%230072b1?style=flat"></a>
</p>

## Overview

Tumult is a client-server chatting application designed to demonstrate (and for me to learn) the utility of Python sockets. Tumult is not intended for use in a real environment. The basic functionality allows a client to connect to a running server and send messages. Each time the server receives a message from a client, it broadcasts that message to every connected client, where each client renders it in the GUI.

## Download

You can find appropriate downloads for each release [here](https://github.com/CaymanFreeman/Tumult/releases). There is also the option to run the [client](https://github.com/CaymanFreeman/Tumult/blob/main/src/client/main.py) or [server](https://github.com/CaymanFreeman/Tumult/blob/main/src/server/main.py) main script, directly from source.

**Windows Client:** An executable and installer are available to download with each release.

**Windows Server:** An executable is available to download with each release.

**Linux Client & Server:** A binary is included in each release.

## Server Arguments

### Host

##### Default: 127.0.0.1
This is the IP address to listen to and is flagged with `--host`, e.g. `--host 127.0.0.1`.

### Port

##### Default: 65535
This is the port to listen to and is flagged with `--port`, e.g. `--port 65535`.

## Compatibility

Tumult is planned to be compatible with both Windows and Linux before leaving the beta stage.

## Executables & Binaries

Each executable/binary simply acts as a bundle for the source files and an interpreter. Each time the file is executed, the source code is expanded to a temporary directory. You can read more about how PyInstaller creates these executables [here](https://pyinstaller.org/en/stable/operating-mode.html#how-the-one-file-program-works).

## Windows

### Clone Repository
```batch
git clone https://github.com/CaymanFreeman/Tumult && cd Tumult
```

### Virtual Environment Setup
```batch
python -m venv .venv
.venv\Scripts\activate.bat
```

### Install Dependencies
```batch
python -m pip install --upgrade pip
pip install -r ./requirements.txt
pip install pyinstaller
```

### Run From Source

From this point, the client or server can be run from the source scripts with `python src\client\main.py` or `python src\server\main.py`.

### PyInstaller Client Bundle
```batch
pyinstaller --noconfirm --onefile --name "Tumult" --windowed --add-data="LICENSE.md:." --icon="assets\icon.ico" --add-data="assets\icon.png:assets" --add-data="assets\client_window.ui:assets" src\client\main.py
```

### PyInstaller Server Bundle
```batch
pyinstaller --noconfirm --onefile --name "TumultServer" --add-data="LICENSE.md:." --icon="assets\icon.ico" --add-data="assets\icon.png:assets" src\server\main.py
```

### Run Executable

The executable will be located at either `dist\Tumult.exe` or `dist\TumultServer.exe`.

## Linux

The following packages may need to be installed: 
```
python3-dev python3.12-venv python3-xlib binutils build-essential
```

### Clone Repository
```bash
git clone https://github.com/CaymanFreeman/Tumult && cd Tumult
```

### Virtual Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r ./requirements.txt
pip install pyinstaller
```

### Run From Source

From this point, the client or server can be run from the source scripts with `python3 src/client/main.py` or `python3 src/server/main.py`.

### PyInstaller Client Bundle
```bash
pyinstaller --noconfirm --onefile --name "tumult" --add-data="LICENSE.md:." --add-data="assets/client_window.ui:assets" src/client/main.py
```

### PyInstaller Server Bundle
```bash
pyinstaller --noconfirm --onefile --name "tumult-server" --add-data="LICENSE.md:." src/server/main.py
```

### Run Binary

The binary will be located at either `dist/tumult` or `dist/tumult-server`.

‎

hi :)
