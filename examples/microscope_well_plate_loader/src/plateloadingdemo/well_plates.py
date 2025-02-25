# Raster scan variables
WELL_PLATES: dict = {
    "96": {
        "rows": 8,
        "columns": 12,
        "pitch": 9.00,  # Distance in mm between center of one well and the center of the adjacent wells
        "row_offset": 11.24,  # Distance in mm between the center of well A1 and the top edge of the plate
        "column_offset": 14.38,  # Distance in mm between the center of well A1 and the left edge of the plate
    },
}

PLATE_TYPE: str = "96"
