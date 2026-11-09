# -*- coding: utf-8 -*-
"""按候选 JSON 建立圆柱壳模型并运行有限元分析。"""

from __future__ import print_function

import argparse

from runtime_build_pressure_hull import main


def run(input_json, result_json, user_subroutine=""):
    return main(input_json, result_json, user_subroutine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json")
    parser.add_argument("result_json")
    parser.add_argument("--user-subroutine", default="")
    arguments = parser.parse_args()
    run(arguments.input_json, arguments.result_json, arguments.user_subroutine)
