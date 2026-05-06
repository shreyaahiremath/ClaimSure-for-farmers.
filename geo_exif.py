"""
Extract GPS from image EXIF. Uses multiple strategies because phone JPEGs vary:
Pillow's parser misses some files; piexif / exifread read raw APP1 segments reliably.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from PIL import Image
from PIL.ExifTags import GPSTAGS


def _rational_to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, tuple) and len(value) == 2:
        num, den = value
        den = den or 1
        return float(num) / float(den)
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        d = value.denominator or 1
        return float(value.numerator) / float(d)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_hemisphere_ref(ref) -> Optional[str]:
    if ref is None:
        return None
    if isinstance(ref, bytes):
        ref = ref.decode("ascii", errors="ignore").strip()
    s = str(ref).strip().upper()
    if not s:
        return None
    return s[0]  # N, S, E, W


def _dms_to_decimal(dms, ref) -> Optional[float]:
    if not dms:
        return None
    if not isinstance(dms, (list, tuple)):
        dms = [dms]
    if len(dms) < 3:
        return None
    deg = (
        _rational_to_float(dms[0])
        + _rational_to_float(dms[1]) / 60.0
        + _rational_to_float(dms[2]) / 3600.0
    )
    r = _normalize_hemisphere_ref(ref)
    if r in ("S", "W"):
        deg = -deg
    return deg


def _gps_from_pillow(path: str) -> Optional[Tuple[float, float]]:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if exif is None:
                return None
            try:
                from PIL.ExifTags import IFD

                gps_ifd = exif.get_ifd(IFD.GPSInfo) or {}
            except Exception:
                gps_ifd = {}
            if not gps_ifd:
                from PIL.ExifTags import TAGS

                for tag_id, val in exif.items():
                    if TAGS.get(tag_id) == "GPSInfo" and isinstance(val, dict):
                        gps_ifd = val
                        break
            if not gps_ifd:
                return None

            labeled = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
            lat = _dms_to_decimal(labeled.get("GPSLatitude"), labeled.get("GPSLatitudeRef"))
            lon = _dms_to_decimal(labeled.get("GPSLongitude"), labeled.get("GPSLongitudeRef"))
            if lat is None or lon is None:
                return None
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return None
            return (round(lat, 6), round(lon, 6))
    except Exception:
        return None


def _gps_from_piexif(path: str) -> Optional[Tuple[float, float]]:
    try:
        import piexif

        raw = piexif.load(path)
        gps = raw.get("GPS") or {}
        if not gps:
            return None

        def rat(tup) -> float:
            if tup is None:
                return 0.0
            if not isinstance(tup, (tuple, list)) or len(tup) < 2:
                return _rational_to_float(tup)
            num, den = int(tup[0]), int(tup[1]) if tup[1] else 1
            return float(num) / float(den)

        def dms(coords, ref) -> Optional[float]:
            if not coords or len(coords) < 3:
                return None
            v = rat(coords[0]) + rat(coords[1]) / 60.0 + rat(coords[2]) / 3600.0
            r = _normalize_hemisphere_ref(ref)
            if r in ("S", "W"):
                v = -v
            return v

        lat = dms(gps.get(2), gps.get(1))
        lon = dms(gps.get(4), gps.get(3))
        if lat is None or lon is None:
            return None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return (round(lat, 6), round(lon, 6))
    except Exception:
        return None


def _gps_from_exifread(path: str) -> Optional[Tuple[float, float]]:
    try:
        import exifread

        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        def coord_from_tag(lat_tag, ref_tag) -> Optional[float]:
            lat = tags.get(lat_tag)
            ref = tags.get(ref_tag)
            if lat is None or ref is None:
                return None
            vals = getattr(lat, "values", None)
            if not vals or len(vals) < 3:
                return None

            def rfloat(x) -> float:
                if hasattr(x, "num") and hasattr(x, "den"):
                    d = x.den or 1
                    return float(x.num) / float(d)
                return _rational_to_float(x)

            deg = rfloat(vals[0]) + rfloat(vals[1]) / 60.0 + rfloat(vals[2]) / 3600.0
            rv = ref.values
            if isinstance(rv, (list, tuple)) and rv:
                rv = rv[0]
            if isinstance(rv, bytes):
                s = rv.decode("ascii", errors="ignore").strip().upper()
            else:
                s = str(rv).strip().upper()
            if not s:
                return None
            hemi = s[0]
            if hemi in ("S", "W"):
                deg = -deg
            return deg

        lat = coord_from_tag("GPS GPSLatitude", "GPS GPSLatitudeRef")
        lon = coord_from_tag("GPS GPSLongitude", "GPS GPSLongitudeRef")
        if lat is None or lon is None:
            return None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return (round(lat, 6), round(lon, 6))
    except Exception:
        return None


def extract_gps_lat_lon(path: str, ext: str = "") -> Optional[Tuple[float, float]]:
    """
    Try several readers; many phone JPEGs only parse correctly with piexif/exifread.
    """
    ext_l = (ext or "").lower().lstrip(".")
    strategies: List[Callable[[], Optional[Tuple[float, float]]]] = [
        lambda: _gps_from_pillow(path),
    ]
    if ext_l in ("jpg", "jpeg", "jpe"):
        strategies.append(lambda: _gps_from_piexif(path))
    strategies.append(lambda: _gps_from_exifread(path))

    for fn in strategies:
        try:
            out = fn()
            if out:
                return out
        except Exception:
            continue
    return None


def analyze_field_image(path: str, ext: str) -> dict:
    ext_l = (ext or "").lower().lstrip(".")
    out = {
        "geo_verified": False,
        "gps": None,
        "width": None,
        "height": None,
        "resolution_ok": False,
        "evidence_ok": False,
        "detail": "no_file",
    }
    try:
        with Image.open(path) as img:
            w, h = img.size
            out["width"], out["height"] = w, h
            out["resolution_ok"] = w >= 400 and h >= 400
    except Exception:
        out["detail"] = "unreadable_image"
        return out

    gps = extract_gps_lat_lon(path, ext_l)
    if gps:
        out["geo_verified"] = True
        out["gps"] = {"lat": gps[0], "lon": gps[1]}
        out["detail"] = "gps_ok"
    else:
        out["detail"] = "no_gps_exif"

    if ext_l in ("webp", "gif") and not out["geo_verified"]:
        out["detail"] = "format_no_gps"

    out["evidence_ok"] = bool(out["geo_verified"] and out["resolution_ok"])
    return out
