"""Bounded ZIP verification in memory. No extraction or imported text output."""
import hashlib
import io
import re
import stat
import struct
import zipfile
import zlib
from pathlib import Path

from .compare import IDS, STATES, decode_object, invalid, numeric_version
from .discovery import bounded_read
from .history import counts

MAX_ZIP_BYTES = 4 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MEMBERS = frozenset(("support.json", "summary.zh.md", "summary.en.md", "PRIVACY.txt", "SHA256SUMS.txt"))


def validate_support(raw):
    obj = decode_object(raw)
    if not isinstance(obj, dict) or obj.get("schema_version") != "1.0" or obj.get("report_type") != "support":
        invalid()
    findings = obj.get("findings")
    if not isinstance(findings, list) or len(findings) > len(IDS):
        invalid()
    projected = {}
    for finding in findings:
        if not isinstance(finding, dict):
            invalid()
        id, state = finding.get("id"), finding.get("status")
        if not isinstance(id, str) or id not in IDS or id in projected or not isinstance(state, str) or state not in STATES:
            invalid()
        evidence = finding.get("evidence")
        if not isinstance(evidence, dict):
            invalid()
        allowed = {"version"} if id.endswith((".version", ".dependency")) else {"installation_groups", "scan_limited"} if id.endswith(".path") else set()
        if evidence.keys() - allowed:
            invalid()
        for key, value in evidence.items():
            if key == "version" and value is not None and numeric_version(value) is None:
                invalid()
            if key == "installation_groups" and (type(value) is not int or not 0 <= value <= 32):
                invalid()
            if key == "scan_limited" and type(value) is not bool:
                invalid()
        projected[id] = {"status": state}
    summary = obj.get("summary")
    if not isinstance(summary, dict) or set(summary) != set(STATES):
        invalid()
    if any(type(n) is not int or not 0 <= n <= len(IDS) for n in summary.values()) or summary != counts(projected):
        invalid()


def member_layout(raw, info, central_start):
    offset = info.header_offset
    if offset < 0 or offset + 30 > central_start:
        invalid()
    sig, _, flags, method, _, _, crc, compressed, size, namesize, extrasize = struct.unpack_from("<4s5H3I2H", raw, offset)
    if sig != b"PK\x03\x04" or flags != info.flag_bits or method != info.compress_type:
        invalid()
    start = offset + 30 + namesize + extrasize
    end = start + info.compress_size
    if start > central_start or end > central_start:
        invalid()
    name = raw[offset + 30:offset + 30 + namesize]
    if name != info.filename.encode("ascii"):
        invalid()
    if not flags & 8 and (crc, compressed, size) != (info.CRC, info.compress_size, info.file_size):
        invalid()
    record_end = end
    if flags & 8:
        descriptor = end + (4 if raw[end:end + 4] == b"PK\x07\x08" else 0)
        if descriptor + 12 > central_start or struct.unpack_from("<3I", raw, descriptor) != (info.CRC, info.compress_size, info.file_size):
            invalid()
        record_end = descriptor + 12
    return offset, start, end, record_end


def verify_support(path):
    raw = bounded_read(Path(path).absolute(), MAX_ZIP_BYTES)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if len(infos) != len(MEMBERS) or {i.filename for i in infos} != MEMBERS:
                invalid()
            total = 0
            layouts = []
            for info in infos:
                kind = stat.S_IFMT(info.external_attr >> 16)
                if (info.orig_filename != info.filename or kind not in (0, stat.S_IFREG) or
                    info.external_attr & 0x58 or info.volume != 0 or info.flag_bits & ~0x080e or
                    info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) or
                    not 0 <= info.file_size <= MAX_MEMBER_BYTES or not 0 <= info.compress_size <= MAX_ZIP_BYTES):
                    invalid()
                total += info.file_size
                layouts.append(member_layout(raw, info, archive.start_dir))
            if total > MAX_TOTAL_BYTES:
                invalid()
            ordered = sorted(layouts)
            if any(a[3] > b[0] for a, b in zip(ordered, ordered[1:])):
                invalid()
            contents = {}
            actual_total = 0
            for info, (_, start, end, _) in zip(infos, layouts):
                compressed = raw[start:end]
                if info.compress_type == zipfile.ZIP_STORED:
                    data = compressed
                else:
                    decoder = zlib.decompressobj(-15)
                    data = decoder.decompress(compressed, MAX_MEMBER_BYTES + 1)
                    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                        invalid()
                actual_total += len(data)
                if (len(data) > MAX_MEMBER_BYTES or actual_total > MAX_TOTAL_BYTES or
                    len(data) != info.file_size or zlib.crc32(data) != info.CRC):
                    invalid()
                contents[info.filename] = data
            manifest = contents["SHA256SUMS.txt"].decode("ascii")
            listed = {}
            for line in manifest.splitlines():
                match = re.fullmatch(r"([0-9a-fA-F]{64})  (support\.json|summary\.zh\.md|summary\.en\.md|PRIVACY\.txt)", line)
                if not match or match[2] in listed:
                    invalid()
                listed[match[2]] = match[1].lower()
            if set(listed) != MEMBERS - {"SHA256SUMS.txt"}:
                invalid()
            if any(hashlib.sha256(contents[name]).hexdigest() != digest for name, digest in listed.items()):
                invalid()
            validate_support(contents["support.json"])
            return {"member_count": len(infos), "archive_bytes": len(raw), "uncompressed_bytes": actual_total}
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, struct.error, EOFError, NotImplementedError) as exc:
        raise ValueError("invalid_bundle") from exc
