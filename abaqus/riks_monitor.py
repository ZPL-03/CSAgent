# -*- coding: utf-8 -*-
"""按已收敛状态记录监测 Riks 后峰并保存终止证据。"""

from __future__ import print_function

import os
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
from runtime_build_pressure_hull import classify_riks_limit_point, riks_status_curve, write_json


def monitor(job_name, command):
    outcome = {"controlled": False, "error": None}
    try:
        while True:
            stopped = os.path.isfile(job_name + ".monitor.stop")
            path = job_name + ".sta"
            if os.path.isfile(path) and not stopped:
                with open(path, "r") as stream:
                    curve = riks_status_curve(stream.read())
                evidence = classify_riks_limit_point(curve, "RUNNING", minimum_drop_ratio=0.2)
                if evidence["limit_point_observed"]:
                    code = subprocess.call(["cmd.exe", "/c", command, "terminate", "job=" + job_name],
                                           creationflags=0x08000000 if os.name == "nt" else 0)
                    if code != 0:
                        raise RuntimeError("Abaqus 后峰终止命令失败，返回码 %s" % code)
                    outcome.update(controlled=True, status_curve_evidence=evidence,
                                   termination_reason="post_peak_drop_20_percent")
                    break
            if stopped:
                break
            time.sleep(0.5)
    except Exception:
        outcome["error"] = traceback.format_exc()
    write_json(job_name + ".monitor.json", outcome)
    return 1 if outcome["error"] else 0


if __name__ == "__main__":
    sys.exit(monitor(sys.argv[1], sys.argv[2]))
