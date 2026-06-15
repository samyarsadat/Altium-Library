<h1 align="center">Altium Library</h1>

<p align="center">
	<a href="LICENSE"><img src="https://img.shields.io/github/license/samyarsadat/Altium-Library?color=blue"></a>
	|
	<a href="../../issues"><img src="https://img.shields.io/github/issues/samyarsadat/Altium-Library"></a>
	<br><br>
</p>

<br>

----
This repository contains my main Altium database library. This library contains a mix of generic, custom, and downloaded parts from UltraLibrarian and Component Search Engine.

> [!NOTE]
> Some generic part footprints are downloaded from the [Celestial Altium Library](https://github.com/issus/altium-library).

<br>

## Setup

> [!WARNING]
> You need to install an ODBC driver for SQLite. I tested with [Christian Werner's driver](http://www.ch-werner.de/sqliteodbc/),
> but you can also use [the one made by Devart](https://www.devart.com/odbc/sqlite/).

To setup the library, clone the repo locally, and install [Altium-Library.DbLib](./Altium-Library.DbLib) in Altium.

You will then need to run the GitHub [file download script](./gh_download/downloader.py) (for downloading generic footprints).

Alternatively, you can use the [provided PowerShell script](./scripts/update_lib.ps1) that creates a Python virtual environment, installs required dependencies, and runs the script automatically.

That same script can then be run periodically to fully update your local library.

<br>

## Contact
You can contact me via e-mail.\
E-mail: samyarsadat@gigawhat.net

If you think that you have found a bug or issue please report it [here](../../issues).

<br>

## Credits

| Role           | Name                                                        |
| -------------- | ----------------------------------------------------------- |
| Maintainer     | [Samyar Sadat Akhavi](https://github.com/samyarsadat)       |

<br>

Copyright © 2026 Samyar Sadat Akhavi.
