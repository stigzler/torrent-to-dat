import argparse
import datetime
import hashlib
import os
import xml.etree.ElementTree as ET


def bdecode(data, idx=0):
    char = chr(data[idx])
    if char == "i":
        end = data.index(b"e", idx)
        return int(data[idx + 1:end]), end + 1
    elif char == "l":
        res, idx = [], idx + 1
        while chr(data[idx]) != "e":
            val, idx = bdecode(data, idx)
            res.append(val)
        return res, idx + 1
    elif char == "d":
        res, idx = {}, idx + 1
        while chr(data[idx]) != "e":
            key, idx = bdecode(data, idx)
            val, idx = bdecode(data, idx)
            res[key.decode("utf-8", errors="ignore")] = val
        return res, idx + 1
    elif char.isdigit():
        colon = data.index(b":", idx)
        length = int(data[idx:colon])
        start = colon + 1
        return data[start:start + length], start + length
    raise ValueError(f"Invalid bencode at {idx}")


def detect_category(name):
    """Assign Redump-style <category> tags so Retool filters properly."""
    lower = name.lower()
    if "(demo" in lower or "(taikenban)" in lower or "(otameshiban)" in lower:
        return "Demos"
    if "(beta" in lower or "(proto" in lower:
        return "Preproduction"
    if "bonus disc" in lower or "movie disc" in lower:
        return "Bonus Discs"
    if any(k in lower for k in ["freeloader", "netflix", "menu install", "discupdate", "backup disc", "udraw studio"]):
        return "Applications"
    return "Games"


def deterministic_hashes(filename, size):
    """Generate unique, valid-format hex strings from filename+size."""
    seed = f"{filename}:{size}".encode("utf-8")
    md5_val = hashlib.md5(seed).hexdigest()
    sha1_val = hashlib.sha1(seed).hexdigest()
    crc_val = md5_val[:8]
    return crc_val, md5_val, sha1_val


def clean_system_name(torrent_name):
    """Ensure <header><name> matches 'Nintendo - Wii U' so Retool loads its clone lists."""
    if "wii u" in torrent_name.lower():
        return "Nintendo - Wii U"
    return torrent_name


def main():
    parser = argparse.ArgumentParser(description="Convert a .torrent file into a Redump-style Logiqx XML .dat file.")
    parser.add_argument("input_torrent", help="Path to the input .torrent file")
    parser.add_argument("output_dat", nargs="?", default=None, help="Optional output .dat filename")
    args = parser.parse_args()

    torrent_file = args.input_torrent
    if not os.path.isfile(torrent_file):
        print(f"Error: File not found -> '{torrent_file}'")
        raise SystemExit(1)

    base_name, _ = os.path.splitext(torrent_file)
    output_file = args.output_dat if args.output_dat else f"{base_name}.dat"

    with open(torrent_file, "rb") as f:
        meta, _ = bdecode(f.read())

    info = meta.get("info", {})
    raw_torrent_name = info.get("name", b"Torrent Set").decode("utf-8", errors="ignore")
    system_name = clean_system_name(raw_torrent_name)

    creation_ts = meta.get("creation date")
    if isinstance(creation_ts, int):
        dt = datetime.datetime.fromtimestamp(creation_ts, tz=datetime.timezone.utc)
    else:
        dt = datetime.datetime.now(datetime.timezone.utc)
    redump_date = dt.strftime("%Y-%m-%d %H-%M-%S")

    files = []
    if "files" in info:
        for entry in info.get("files", []):
            path_parts = [p.decode("utf-8", errors="ignore") for p in entry.get("path", [])]
            files.append((
                "/".join(path_parts),
                entry.get("length", 0),
                entry.get("md5sum"),
                entry.get("sha1"),
            ))
    else:
        files.append((
            raw_torrent_name,
            info.get("length", 0),
            info.get("md5sum"),
            info.get("sha1"),
        ))

    valid_files = [
        item for item in files
        if not os.path.basename(item.__getitem__(0)).startswith("_____padding_file")
    ]

    root = ET.Element("datafile")
    header = ET.SubElement(root, "header")
    ET.SubElement(header, "name").text = system_name
    ET.SubElement(header, "description").text = f"{system_name} ({len(valid_files)}) ({redump_date})"
    ET.SubElement(header, "version").text = redump_date
    ET.SubElement(header, "date").text = redump_date
    ET.SubElement(header, "author").text = "redump.org"
    ET.SubElement(header, "homepage").text = "redump.org"
    ET.SubElement(header, "url").text = "http://redump.org"

    for filepath, size, md5, sha1 in valid_files:
        filename = os.path.basename(filepath)
        game_name, _ = os.path.splitext(filename)
        crc_fb, md5_fb, sha1_fb = deterministic_hashes(filename, size)

        md5_str = md5.decode("utf-8", errors="ignore").lower() if md5 else md5_fb
        sha1_str = (
            (sha1.hex().lower() if isinstance(sha1, bytes) else str(sha1).lower())
            if sha1
            else sha1_fb
        )
        crc_str = md5_str[:8] if md5 else crc_fb

        game_el = ET.SubElement(root, "game", name=game_name)
        ET.SubElement(game_el, "category").text = detect_category(game_name)
        ET.SubElement(game_el, "description").text = game_name

        ET.SubElement(
            game_el,
            "rom",
            name=filename,
            size=str(size),
            crc=crc_str,
            md5=md5_str,
            sha1=sha1_str,
        )

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t")

    doctype = '<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://logiqx.com">\n'
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0"?>\n')
        f.write(doctype)
        f.write(ET.tostring(root, encoding="unicode"))

    print(f"Generated Redump-style DAT '{output_file}' with {len(valid_files)} entries.")


if __name__ == "__main__":
    main()
