"""path_parser.py — Parse SVG path d="" attribute into normalized absolute command list."""
from __future__ import annotations

import re
from typing import List, Tuple

_CMD_PARAMS = {
    'M': 2, 'm': 2, 'L': 2, 'l': 2, 'H': 1, 'h': 1, 'V': 1, 'v': 1,
    'C': 6, 'c': 6, 'S': 4, 's': 4, 'Q': 4, 'q': 4, 'T': 2, 't': 2,
    'A': 7, 'a': 7, 'Z': 0, 'z': 0,
}
_TOKEN_RE = re.compile(
    r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'
)


def parse_path(d: str) -> List[Tuple]:
    if not d or not d.strip():
        return []
    tokens = _TOKEN_RE.findall(d)
    commands: List[Tuple] = []
    i = 0
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    last_cmd = ''
    last_ctrl: Tuple[float, float] = (0.0, 0.0)

    def read_nums(count: int):
        nonlocal i
        nums = []
        while len(nums) < count and i < len(tokens):
            t = tokens[i]
            if t in _CMD_PARAMS:
                break
            try:
                nums.append(float(t))
                i += 1
            except ValueError:
                i += 1
        return nums

    while i < len(tokens):
        tok = tokens[i]
        if tok in _CMD_PARAMS:
            cmd = tok
            i += 1
        else:
            if last_cmd == 'M':
                cmd = 'L'
            elif last_cmd == 'm':
                cmd = 'l'
            else:
                cmd = last_cmd or 'L'

        n = _CMD_PARAMS.get(cmd.upper(), 0)

        if cmd in ('Z', 'z'):
            commands.append(('Z',))
            cur_x, cur_y = start_x, start_y
            last_cmd = cmd
            continue

        nums = read_nums(n)
        if len(nums) < n:
            break

        cx, cy = cur_x, cur_y

        if cmd == 'M':
            cur_x, cur_y = nums[0], nums[1]
            start_x, start_y = cur_x, cur_y
            commands.append(('M', cur_x, cur_y))
        elif cmd == 'm':
            cur_x, cur_y = cx + nums[0], cy + nums[1]
            start_x, start_y = cur_x, cur_y
            commands.append(('M', cur_x, cur_y))
        elif cmd == 'L':
            cur_x, cur_y = nums[0], nums[1]
            commands.append(('L', cur_x, cur_y))
        elif cmd == 'l':
            cur_x, cur_y = cx + nums[0], cy + nums[1]
            commands.append(('L', cur_x, cur_y))
        elif cmd == 'H':
            cur_x = nums[0]
            commands.append(('L', cur_x, cy))
        elif cmd == 'h':
            cur_x = cx + nums[0]
            commands.append(('L', cur_x, cy))
        elif cmd == 'V':
            cur_y = nums[0]
            commands.append(('L', cx, cur_y))
        elif cmd == 'v':
            cur_y = cy + nums[0]
            commands.append(('L', cx, cur_y))
        elif cmd == 'C':
            last_ctrl = (nums[2], nums[3])
            cur_x, cur_y = nums[4], nums[5]
            commands.append(('C', nums[0], nums[1], nums[2], nums[3], cur_x, cur_y))
        elif cmd == 'c':
            lc = (cx + nums[2], cy + nums[3])
            cur_x, cur_y = cx + nums[4], cy + nums[5]
            commands.append(('C', cx + nums[0], cy + nums[1], lc[0], lc[1], cur_x, cur_y))
            last_ctrl = lc
        elif cmd == 'S':
            if last_cmd.upper() in ('C', 'S'):
                cp1 = (2 * cx - last_ctrl[0], 2 * cy - last_ctrl[1])
            else:
                cp1 = (cx, cy)
            last_ctrl = (nums[0], nums[1])
            cur_x, cur_y = nums[2], nums[3]
            commands.append(('C', cp1[0], cp1[1], nums[0], nums[1], cur_x, cur_y))
        elif cmd == 's':
            if last_cmd.upper() in ('C', 'S'):
                cp1 = (2 * cx - last_ctrl[0], 2 * cy - last_ctrl[1])
            else:
                cp1 = (cx, cy)
            lc = (cx + nums[0], cy + nums[1])
            cur_x, cur_y = cx + nums[2], cy + nums[3]
            commands.append(('C', cp1[0], cp1[1], lc[0], lc[1], cur_x, cur_y))
            last_ctrl = lc
        elif cmd == 'Q':
            last_ctrl = (nums[0], nums[1])
            cur_x, cur_y = nums[2], nums[3]
            commands.append(('Q', nums[0], nums[1], cur_x, cur_y))
        elif cmd == 'q':
            lc = (cx + nums[0], cy + nums[1])
            cur_x, cur_y = cx + nums[2], cy + nums[3]
            commands.append(('Q', lc[0], lc[1], cur_x, cur_y))
            last_ctrl = lc
        elif cmd == 'T':
            if last_cmd.upper() in ('Q', 'T'):
                cp = (2 * cx - last_ctrl[0], 2 * cy - last_ctrl[1])
            else:
                cp = (cx, cy)
            last_ctrl = cp
            cur_x, cur_y = nums[0], nums[1]
            commands.append(('Q', cp[0], cp[1], cur_x, cur_y))
        elif cmd == 't':
            if last_cmd.upper() in ('Q', 'T'):
                cp = (2 * cx - last_ctrl[0], 2 * cy - last_ctrl[1])
            else:
                cp = (cx, cy)
            last_ctrl = cp
            cur_x, cur_y = cx + nums[0], cy + nums[1]
            commands.append(('Q', cp[0], cp[1], cur_x, cur_y))
        elif cmd == 'A':
            cur_x, cur_y = nums[5], nums[6]
            commands.append(('A', nums[0], nums[1], nums[2],
                             int(nums[3]), int(nums[4]), cur_x, cur_y))
        elif cmd == 'a':
            cur_x, cur_y = cx + nums[5], cy + nums[6]
            commands.append(('A', nums[0], nums[1], nums[2],
                             int(nums[3]), int(nums[4]), cur_x, cur_y))

        if cmd.upper() not in ('C', 'S', 'Q', 'T'):
            last_ctrl = (cur_x, cur_y)
        last_cmd = cmd

    return commands


def has_curves(commands: List[Tuple]) -> bool:
    return any(cmd[0] in ('C', 'Q', 'A') for cmd in commands)
