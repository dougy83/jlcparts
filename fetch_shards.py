#!/usr/bin/env python3
"""
Download sharded component data from upstream and produce all.jsonlines.tar
compatible with the local buildtables output format.
"""

import concurrent.futures
import gzip
import json
import os
import socket
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

# Force IPv4 — Python's urllib hangs on IPv6
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, *args, **kwargs):
    return [r for r in _orig_getaddrinfo(host, port, *args, **kwargs)
            if r[0] == socket.AF_INET]
socket.getaddrinfo = _ipv4_getaddrinfo

DATA_URL = "https://yaqwsx.github.io/jlcparts/data"
OUTPUT = "web/public/data/all.jsonlines.tar"


def fetch(url, timeout=120, retries=3):
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(2)
            continue
    raise last_err


def fetch_json(url):
    return json.loads(fetch(url).decode("utf-8"))


def entry_to_tar(tar, outdir, key, items_it):
    filename = os.path.join(outdir, key + ".jsonlines.gz")
    with gzip.open(filename, "wt", encoding="utf-8") as f:
        for entry in items_it:
            json.dump(entry, f, separators=(",", ":"), sort_keys=False)
            f.write("\n")
    tar.add(filename, arcname=os.path.relpath(filename, start=outdir))
    os.unlink(filename)


def remap_row(row, subcat_idx):
    """Convert upstream component row to target format.
    Upstream: [lcsc, mfr, joints, desc, datasheet, price, img, url, attrIds, stock, subcatId]
    Target:   [lcsc, mfr, desc, attrsIdx, stock, subcatIdx, joints, datasheet, price, img, url]
    """
    return [
        row[0],   # lcsc
        row[1],   # mfr
        row[3],   # description
        row[8],   # attrsIdx
        row[9],   # stock
        subcat_idx,
        row[2],   # joints
        row[4],   # datasheet
        row[5],   # price
        row[6],   # img
        row[7],   # url
    ]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                       help="Only process first N categories")
    parser.add_argument("--workers", type=int, default=16,
                       help="Parallel download workers")
    parser.add_argument("--data-url", default=DATA_URL)
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()

    data_url = args.data_url.rstrip("/")
    output_path = args.output
    outdir = os.path.dirname(output_path) or "."
    Path(outdir).mkdir(parents=True, exist_ok=True)
    workers = args.workers

    t_start = time.time()

    print("Fetching manifest...", flush=True)
    manifest = fetch_json(f"{data_url}/manifest.json")

    categories = manifest["categories"]
    if args.limit:
        categories = categories[:args.limit]

    total = len(categories)
    total_comps = sum(c.get("componentCount", 0) for c in categories)
    total_shards = sum(len(c["shards"]) for c in categories)
    print(f"  {total} categories, {total_comps} components, {total_shards} shards", flush=True)

    # Map upstream category IDs to contiguous 1-based indices
    cat_id_to_idx = {}
    for idx, cat in enumerate(categories, start=1):
        cat_id_to_idx[cat["id"]] = idx

    print("Fetching attributes LUT...", flush=True)
    lut_url = f"{data_url}/{manifest['attributesLut']}"
    lut_raw = gzip.decompress(fetch(lut_url))
    lut_data = json.loads(lut_raw)
    print(f"  {len(lut_data)} LUT entries", flush=True)

    print(f"Downloading {total_shards} shards with {workers} workers...", flush=True)

    # Build list of (ci, shard_url) tuples
    download_queue = []
    for ci, cat in enumerate(categories):
        for shard_name in cat["shards"]:
            shard_url = f"{data_url}/{shard_name}"
            download_queue.append((ci, shard_url, shard_name))

    # Download all shards concurrently, store results by URL
    shard_data = {}
    dl_t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        fut_to_info = {
            executor.submit(fetch, url): (ci, url, name)
            for ci, url, name in download_queue
        }
        done_count = 0
        for future in concurrent.futures.as_completed(fut_to_info):
            ci, url, name = fut_to_info[future]
            try:
                data = future.result()
                shard_data[url] = (ci, data)
                done_count += 1
                elapsed = time.time() - dl_t0
                rate = done_count / elapsed if elapsed > 0 else 0
                if done_count % 100 == 0 or done_count == total_shards:
                    print(f"  Downloaded {done_count}/{total_shards} ({rate:.0f}/s)", flush=True)
            except Exception as e:
                print(f"  ERROR: {name}: {e}", flush=True)
                sys.exit(1)

    dl_elapsed = time.time() - dl_t0
    print(f"  Downloaded all shards in {dl_elapsed:.0f}s", flush=True)

    # Build the tar
    print("Building tar...", flush=True)
    with tarfile.open(output_path, "w") as tar:
        # 1. Component entries (written first, matching original tar order)
        components_schema = {
            "lcsc": 0, "mfr": 1, "description": 2, "attrsIdx": 3,
            "stock": 4, "subcategoryIdx": 5, "joints": 6,
            "datasheet": 7, "price": 8, "img": 9, "url": 10
        }

        processed = 0
        for ci, cat in enumerate(categories):
            subcat_idx = cat_id_to_idx[cat["id"]]
            comp_count = cat["componentCount"]

            # Collect rows from all shards for this category
            all_rows = []
            for shard_name in cat["shards"]:
                shard_url = f"{data_url}/{shard_name}"
                raw_bytes = shard_data[shard_url][1]
                raw_text = gzip.decompress(raw_bytes).decode("utf-8")
                lines = raw_text.splitlines()
                for line in lines[1:]:
                    if line.strip():
                        row = json.loads(line)
                        all_rows.append(remap_row(row, subcat_idx))

            if not all_rows:
                continue

            def comp_gen():
                yield components_schema
                yield from all_rows

            comp_key = f"components-{subcat_idx}"
            entry_to_tar(tar, outdir, comp_key, comp_gen())

            processed += 1
            if processed % 200 == 0 or processed == 1 or processed == total:
                print(f"  Wrote {processed}/{total} categories", flush=True)

        # 2. Attributes LUT (no schema line — raw data entries only)
        def lut_gen():
            yield from lut_data
        entry_to_tar(tar, outdir, "attributes-lut", lut_gen())
        print("  Wrote attributes-lut", flush=True)

        # 3. Subcategories (written last, matching original tar order)
        subcat_schema = {"subcategory": 0, "category": 1, "subcategoryIdx": 2}
        subcat_items = [
            [cat["subcategory"], cat["category"], cat_id_to_idx[cat["id"]]]
            for cat in categories
        ]
        def subcat_gen():
            yield subcat_schema
            yield from subcat_items
        entry_to_tar(tar, outdir, "subcategories", subcat_gen())
        print("  Wrote subcategories", flush=True)

    t_end = time.time()
    sz = os.path.getsize(output_path)
    for unit in ["B", "KB", "MB", "GB"]:
        if sz < 1024:
            size_str = f"{sz:.1f} {unit}"
            break
        sz /= 1024
    else:
        size_str = f"{sz:.1f} TB"

    print(f"Done in {t_end - t_start:.0f}s. Output: {output_path} ({size_str})", flush=True)


if __name__ == "__main__":
    main()
