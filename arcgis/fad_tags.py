# -*- coding: utf-8 -*-
"""Append ASCII TIFF tags without GDAL (ArcGIS Desktop and Pro)."""

import struct


def write_tiff_tags(path, tags):
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:4] == b"II*\x00":
        endian = "<"
    elif data[:4] == b"MM\x00*":
        endian = ">"
    else:
        raise RuntimeError("not a classic TIFF file")
    if len(data) < 8:
        raise RuntimeError("not a valid TIFF file")
    ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
    if ifd_offset + 2 > len(data):
        raise RuntimeError("not a valid TIFF file")
    count = struct.unpack(endian + "H", data[ifd_offset:ifd_offset + 2])[0]
    position = ifd_offset + 2
    entries = []
    for _ in range(count):
        if position + 12 > len(data):
            raise RuntimeError("not a valid TIFF file")
        entries.append(data[position:position + 12])
        position += 12
    if position + 4 > len(data):
        raise RuntimeError("not a valid TIFF file")
    next_offset = struct.unpack(endian + "I", data[position:position + 4])[0]

    replaced = set(tags)
    entries = [entry for entry in entries
               if struct.unpack(endian + "H", entry[:2])[0] not in replaced]

    base = len(data)
    if base % 2:
        base += 1
    values_offset = base + 2 + 12 * (len(entries) + len(tags)) + 4
    values = b""
    for tag in sorted(tags):
        payload = str(tags[tag]).encode("ascii", "replace") + b"\x00"
        entry = struct.pack(endian + "HHI", tag, 2, len(payload))
        if len(payload) <= 4:
            entry += payload.ljust(4, b"\x00")
        else:
            entry += struct.pack(endian + "I", values_offset + len(values))
            values += payload
        entries.append(entry)
    entries.sort(key=lambda entry: struct.unpack(endian + "H", entry[:2])[0])

    ifd = struct.pack(endian + "H", len(entries))
    ifd += b"".join(entries)
    ifd += struct.pack(endian + "I", next_offset)

    with open(path, "ab") as handle:
        handle.write(b"\x00" * (base - len(data)))
        handle.write(ifd)
        handle.write(values)
    with open(path, "r+b") as handle:
        handle.seek(4)
        handle.write(struct.pack(endian + "I", base))
