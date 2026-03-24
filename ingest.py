"""Ingest Parquet data into PostgreSQL."""

import httpx
from io import BytesIO
import pandas as pd
from sqlalchemy import create_engine
from shapely.geometry import shape

from config import settings


LINK_INFO_URL = "https://cdn.urbansdk.com/data-engineering-interview/link_info.parquet.gz"
SPEED_DATA_URL = "https://cdn.urbansdk.com/data-engineering-interview/duval_jan1_2024.parquet.gz"


def download_parquet(url: str) -> pd.DataFrame:
    print(f"Downloading {url}...")
    response = httpx.get(url, timeout=120)
    response.raise_for_status()
    df = pd.read_parquet(BytesIO(response.content))
    print(f"Downloaded {len(df)} rows")
    return df


def geojson_to_wkt(geojson_str):
    try:
        geom = shape(eval(geojson_str))
        return geom.wkt
    except Exception:
        return None


def ingest_data():
    print("Starting data ingestion...")

    link_df = download_parquet(LINK_INFO_URL)
    speed_df = download_parquet(SPEED_DATA_URL)

    engine = create_engine(settings.DATABASE_URL)

    link_df["geometry"] = link_df["geo_json"].apply(geojson_to_wkt)
    link_df = link_df.dropna(subset=["geometry"])

    link_df = link_df[["link_id", "road_name", "geometry"]]
    link_df.columns = ["link_id", "name", "geometry"]

    print("Inserting links...")
    link_df.to_sql("links", engine, if_exists="append", index=False)
    print(f"Inserted {len(link_df)} links")

    link_df2 = pd.read_sql("SELECT link_id, id FROM links", engine)
    link_map = dict(zip(link_df2["link_id"].astype(str), link_df2["id"]))

    speed_df["link_id_pk"] = speed_df["link_id"].astype(str).map(link_map)
    speed_df = speed_df.dropna(subset=["link_id_pk"])

    day_map = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }
    speed_df["day_of_week"] = speed_df["day_of_week"].map(day_map).fillna("Unknown")
    speed_df["hour"] = pd.to_datetime(speed_df["date_time"]).dt.hour

    speed_df = speed_df[["link_id_pk", "date_time", "average_speed", "day_of_week", "hour"]]
    speed_df.columns = ["link_id", "timestamp", "speed", "day_of_week", "hour"]
    speed_df["speed"] = speed_df["speed"].astype(float)
    speed_df["link_id"] = speed_df["link_id"].astype(int)
    speed_df["hour"] = speed_df["hour"].astype(int)

    print("Inserting speed records...")
    speed_df.to_sql("speed_records", engine, if_exists="append", index=False)
    print(f"Inserted {len(speed_df)} speed records")

    print("Ingestion complete!")


if __name__ == "__main__":
    ingest_data()
