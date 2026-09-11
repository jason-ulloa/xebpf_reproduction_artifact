#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib
from huggingface_hub import hf_hub_download
import zstandard as zstd

REPO = "j-klawson/security-gym-v4"
FILE = "exp_30d_heavy_v4.db.zst"
EXPECTED_SHA256 = "4e903e2ba8d50945070c23109079388fa318db8f995ce1c3958e1447082f8824"
DOI = "10.5281/zenodo.21763493"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--outdir",default="data")
    a=ap.parse_args()
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    src=Path(hf_hub_download(repo_id=REPO,filename=FILE,repo_type="dataset"))
    got=sha256(src)
    print("Dataset DOI:",DOI)
    print("Compressed SHA-256:",got)
    if got != EXPECTED_SHA256:
        raise SystemExit("INTEGRITY GATE: FAIL - dataset hash differs from the frozen v4.1 stream")
    dst=out/"exp_30d_heavy_v4.db"
    with src.open("rb") as fi, dst.open("wb") as fo:
        zstd.ZstdDecompressor().copy_stream(fi,fo)
    print("INTEGRITY GATE: PASS")
    print(dst)
if __name__=="__main__": main()
