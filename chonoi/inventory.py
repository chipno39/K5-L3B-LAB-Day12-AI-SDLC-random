"""File kho v1.2 (TICKET-03): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}.

Đọc: từ chối kho đếm kiểu cũ (v1.0/v1.1), sai schema, kind lạ, id trùng, fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, giữ đủ độ chính xác float ở ngưỡng 30, qua file tạm cùng thư mục rồi thay thế nguyên tử.
"""

from fractions import Fraction
import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_V11 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


def fresh_frac(v) -> Fraction:
    """Chuyển độ tươi (int/float/Fraction) sang Fraction chính xác."""
    if isinstance(v, Fraction):
        return v
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise BadInput(f"fresh phải là số hữu hạn trong [0, 100], đang là {v!r}")
    return Fraction(str(v))


def fresh_num(f):
    """Xuất Fraction/số ra int nếu nguyên, hoặc float đủ độ chính xác cho JSON."""
    if isinstance(f, Fraction):
        if f.denominator == 1:
            return int(f.numerator)
        return float(f)
    if isinstance(f, float) and f.is_integer():
        return int(f)
    return f


def validate_items(items, kinds=KINDS_V11) -> list:
    """Kiểm mảng cá thể v1.2; từ chối kho đếm (dict) hoặc phần tử sai schema."""
    if not isinstance(items, list):
        raise BadInput("v1.2 yêu cầu items là mảng cá thể [{id, kind, fresh}], không nhận kho đếm")
    out = []
    seen = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it.keys()) != {"id", "kind", "fresh"}:
            raise BadInput(f"items[{i}] phải có đúng khóa id, kind, fresh")
        iid = it["id"]
        kind = it["kind"]
        fresh = it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"items: id trùng {iid!r}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"items[{i}]: nguyên liệu lạ {kind!r}")
        fr = fresh_frac(fresh)
        if fr < 0 or fr > 100:
            raise BadInput(f"items[{i}].fresh ngoài [0, 100]: {fresh!r}")
        out.append({"id": iid, "kind": kind, "fresh": fresh_num(fr)})
    return out


def read_inventory(path: str, kinds=KINDS_V11) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> list:
    """Khoang (mảng cá thể theo thứ tự nhặt) -> mảng cá thể sắp theo id."""
    return [
        {"id": it["id"], "kind": it["kind"], "fresh": fresh_num(it["fresh"])}
        for it in sort_by_id(hold)
    ]


def write_inventory(path: str, items: list):
    ordered = hold_to_items(items)
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": ordered}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
