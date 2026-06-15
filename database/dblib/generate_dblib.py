"""
    Altium .DbLib file generation utility script.
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

import tomllib
from argparse import ArgumentParser
from pathlib import Path
from parts_db.schema import BY_SHEET



# DbLib file structure
_DBLIB_STRUCTURE_FILE = Path(__file__).with_name("dblib_struct.toml")
with _DBLIB_STRUCTURE_FILE.open("rb") as file:
    _DBLIB_STRUCTURE = tomllib.load(file)

DBLIB_START: str = _DBLIB_STRUCTURE["file_beginning"]
DBLIB_TABLE_ENTRY: str = _DBLIB_STRUCTURE["table_entry"]
DBLIB_FIELD_MAP: str = _DBLIB_STRUCTURE["field_map_entry"]

# Field configuration
_FIELDS_CONF_FILE = Path(__file__).with_name("dblib_fields_conf.toml")
with _FIELDS_CONF_FILE.open("rb") as file:
    FIELDS_CONFIG = tomllib.load(file)



# Generate field mapping entries for a given table
def generate_field_maps(table: str, current_index: int) -> list[str]:
    ret_list = []

    pk_field = FIELDS_CONFIG["pk_field"]
    ret_list.append(
        DBLIB_FIELD_MAP.format(
            num=current_index,
            table_name=table,
            field_name=pk_field,
            field_type=0,
            param_name=pk_field
        )
    )
    current_index += 1

    all_fields = FIELDS_CONFIG["fields"] + (
        FIELDS_CONFIG["footprint_fields"] if BY_SHEET[table]["has_footprint"] else []
    )

    for field in all_fields:
        ret_list.append(
            DBLIB_FIELD_MAP.format(
                num=current_index,
                table_name=table,
                field_name=field,
                field_type=1,
                param_name=f"[{field}]"
            )
        )
        current_index += 1
    return ret_list


# Generate the full .DbLib file string
def generate_file(database_path: str) -> str:
    beginning = DBLIB_START.format(
        db_path=database_path
    )

    tables = []
    field_maps = []
    
    for i, name in enumerate(BY_SHEET, 1):
        print(f"Adding table #{i}: {name}")

        table_str = DBLIB_TABLE_ENTRY.format(
            num=i, name=name
        )
        tables.append(table_str)

        field_maps += generate_field_maps(
            name, 
            len(field_maps) + 1
        )

    print(f"Added {len(tables)} tables with {len(field_maps)} parameters.")
    return f"{beginning}\n{"\n".join(tables)}\n{"".join(field_maps)}"


# Entrypoint
def main():
    arg_parser = ArgumentParser(
        description="generate an Altium DbLib file based on the latest schema"
    )
    
    arg_parser.add_argument("--db-file-path", 
        default=".\\Altium-Library.db",
        help="flat parts database file path relative to DbLib file"
    )
    arg_parser.add_argument("--out",
        default="Altium-Library.DbLib",
        help="output Altium DbLib file path"
    )
    
    args = arg_parser.parse_args()
    with open(args.out, "w") as file:
        file.write(generate_file(args.db_file_path))


if __name__ == "__main__":
    main()
