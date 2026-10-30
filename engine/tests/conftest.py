# -*- coding: utf-8 -*-
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from fixtures_v2 import build_v2_board  # noqa: E402


@pytest.fixture()
def v2_board():
    return build_v2_board()
