"""使用案例数据训练 SCREENER 代理模型。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.surrogate_model import SurrogateModelManager


def main() -> int:
    manager = SurrogateModelManager()
    records = manager.load_training_records()
    if not records:
        raise RuntimeError("未找到可用于训练的成功案例。")

    summary = manager.train_from_records(records)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
