"""
    GitHub file download script.
    Downloads files based on configuration provided in JSON files.
    Copyright 2026 Samyar Sadat Akhavi

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import subprocess
import requests
import json
import tomllib
from argparse import ArgumentParser
from pathlib import Path



# Program config
DIR_DOWNLOAD_CONFIF_FILE = "gh_downloads.json"
GH_DOWNLAOD_URL = "https://raw.githubusercontent.com"

# Download directories config
_DOWNLAOD_DIRS_FILE = "gh_download_dirs.toml"
with open(_DOWNLAOD_DIRS_FILE, "rb") as file:
    _DL_CONFIG = tomllib.load(file)

DOWNLOAD_DIRS = _DL_CONFIG["download_dirs"]



def get_git_root() -> Path:
    return Path(subprocess.check_output([
        "git", "rev-parse", "--show-toplevel"
    ]).decode().strip())

def download_file(url: str, save_path: Path) -> bool:
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return True
    except requests.exceptions.RequestException as _:
        return False

def test_file_exts(dl_url: str, exts: list[str]) -> str | None:
    for ext in exts:
        url = f"{dl_url}.{ext}"
        response = requests.head(url, allow_redirects=True)
        
        if response.status_code == 200:
            return url
    return None


def process_downloads(dir_path: Path, dl_files: bool) -> None:
    dir_config_path = dir_path / DIR_DOWNLOAD_CONFIF_FILE
    
    if not dir_config_path.exists():
        print(f"Configuration file not found in {dir_path}")
        return

    print(f"Processing directory: {dir_path}")

    with open(dir_config_path, "r") as file:
        dir_config = json.load(file)

    dl_url_pre = f"{GH_DOWNLAOD_URL}/{dir_config.get('repo_dir')}"
    file_ext = dir_config.get("file_type")

    for subdir, subdir_obj in dir_config.get("files", {}).items():
        print(f"Processing repo subdirectory: {subdir}")

        dl_filename_prefix = subdir_obj.get("dl_filename_prefix")
        filename_prefix = subdir_obj.get("filename_prefix")

        for file, file_dl in subdir_obj.get("downloads", {}).items():
            dl_filename_noext = f"{dl_filename_prefix}{file_dl}"
            filename = f"{filename_prefix}{file}.{file_ext}"

            dl_url_noext = f"{dl_url_pre}/{subdir}/{dl_filename_noext}"
            save_path = dir_path / filename

            dl_file_exts = [file_ext.upper(), file_ext.lower(), file_ext]
            dl_url = test_file_exts(dl_url_noext, dl_file_exts)
            if not dl_url:
                raise RuntimeError(f"Valid file extension not found for {dl_filename_noext}")

            if dl_files:
                if download_file(dl_url, save_path):
                    print(f"Downloaded file {filename}")
                else:
                    raise RuntimeError(f"Failed to download {filename} from {dl_url}")
            else:
                print(f"Checked file {filename}")


# Entrypoint
def main():
    arg_parser = ArgumentParser(
        description="download lists of files from GitHub based on config"
    )
    
    arg_parser.add_argument("--test-dls", 
        action="store_false",
        help="only test donwload urls, but do not download files"
    )

    args = arg_parser.parse_args()
    repo_root = get_git_root()

    for dir in DOWNLOAD_DIRS:
        dir_path = repo_root / dir
        process_downloads(dir_path, args.test_dls)


if __name__ == "__main__":
    main()
