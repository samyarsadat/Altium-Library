"""
    Parameters database schema flattening utility.
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

import sqlite3
import pandas as pd
from argparse import ArgumentParser
from sqlalchemy import select
from sqlalchemy.orm import Session
from parts_db.schema import (
    CATEGORIES, PARAM_TABLES, Part, engine_for
)



# Create the list of table columns for the flattened schema.
def flat_columns(cat: dict, n_suppliers: int) -> list[str]:
    cols = [
        "Part Number",
        "Description",
        "Library Ref",
        "Library Path"
    ] + [
        header for header, _ in cat["params"]
    ]
    
    if cat["has_footprint"]:
        cols.append("Footprint Ref")
        cols.append("Footprint Path")

    if cat["has_manufacturer"]:
        cols.append("Manufacturer")

    if cat["has_supplier"]:
        for i in range(1, n_suppliers + 1):
            cols += [f"Supplier {i}", f"Supplier Part Number {i}"]

    return cols


# Return all parts in a category as flattened rows.
def flat_rows(session: Session, cat: dict, add_suppliers: bool) -> tuple[int, list[dict]]:
    ParamModel = PARAM_TABLES.get(cat["key"])
    params = (
        {row.part_number: row for row in session.scalars(select(ParamModel))}
        if ParamModel else {}
    )

    rows = []
    max_part_supps = 0
    parts = session.scalars(
        select(Part).where(Part.category == cat["key"])
    )
    
    for part in parts:
        row = {
            "Part Number": part.part_number,
            "Description": part.description,
            "Library Ref": part.symbol.library_ref,
            "Library Path": part.symbol.library_path,
        }

        # it is assumed that we cannot trust the database to ONLY have parameters
        # specified in the category config JSON file, or to have ALL pramaters specified.
        VALUE_MISSING_ERR_MSG = f" for {part.part_number} is/are missing!"

        part_params = params.get(part.part_number)
        if cat["params"] and part_params:
            for header, attr in cat["params"]:
                row[header] = getattr(part_params, attr)
        elif cat["params"]:
            print("Parameter values" + VALUE_MISSING_ERR_MSG)

        if cat["has_footprint"] and part.footprint:
            row["Footprint Ref"] = part.footprint.footprint_ref
            row["Footprint Path"] = part.footprint.footprint_path
        elif cat["has_footprint"]:
            print("Footprint data" + VALUE_MISSING_ERR_MSG)
        
        if cat["has_manufacturer"] and part.manufacturer:
            row["Manufacturer"] = part.manufacturer.name
        elif cat["has_manufacturer"]:
            print("Manufacturer name" + VALUE_MISSING_ERR_MSG)
        
        if cat["has_supplier"] and add_suppliers:
            len_supps = len(part.suppliers)
            
            if len_supps > max_part_supps:
                max_part_supps = len_supps

            supps_ordered = sorted(part.suppliers, key=lambda supp: supp.rank)
            for i in range(len_supps):
                supp = supps_ordered[i]
                row[f"Supplier {i + 1}"] = supp.supplier.name
                row[f"Supplier Part Number {i + 1}"] = supp.supplier_part_number
        
        rows.append(row)
    return max_part_supps, rows


# Flatten all categories and write the data to the output DB.
def flatten(source_url: str, out_path: str, min_suppliers: int) -> None:
    out_db = sqlite3.connect(out_path)
    
    try:
        total_parts = 0
        with Session(engine_for(source_url)) as session:
            for cat in CATEGORIES:
                num_supp_cols, rows = flat_rows(session, cat, min_suppliers > 0)
                
                if cat["has_supplier"]:
                    num_supp_cols = max(num_supp_cols, min_suppliers)
                
                df = pd.DataFrame(rows).reindex(columns=flat_columns(cat, num_supp_cols))
                df.to_sql(cat["sheet"], out_db, if_exists="replace", index=False)
                total_parts += len(df)
                
                print(
                    f"{cat['sheet']:<32} {len(df):>4} rows" + 
                    (f", {num_supp_cols} supplier(s)" if num_supp_cols else "")
                )
        out_db.commit()
    finally:
        out_db.close()
    
    print(f"Wrote {total_parts} parts across {len(CATEGORIES)} tables -> {out_path}")



# Entrypoint
def main():
    arg_parser = ArgumentParser(
        description="flatten the normalized library for use with Altium"
    )
    
    arg_parser.add_argument("--source", 
        default="sqlite:///parts_db/master_library.db",
        help="normalized source DB"
    )
    arg_parser.add_argument("--out",
        default="Altium-Library.db",
        help="flat output database file"
    )
    arg_parser.add_argument("--min-suppliers", 
        type=int, default=1,
        help="minimum Supplier columns to expose, even if data needs fewer"
    )
    
    args = arg_parser.parse_args()
    flatten(args.source, args.out, args.min_suppliers)


if __name__ == "__main__":
    main()
