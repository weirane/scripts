#!/usr/bin/env python3

from subprocess import run, PIPE, DEVNULL
import json
import operator
import sys

BAR_HEIGHT = 36


# --- utils ---
def json_run(args):
    '''Run command and return json output'''
    shell = isinstance(args, str)
    r = run(args, stdout=PIPE, stderr=DEVNULL, shell=shell).stdout
    return json.loads(r) if r else None


def current_window():
    '''Get the current focused window in json'''
    return json_run('yabai -m query --windows --window')


# --- move ---
def center(window):
    '''Center floating window on the display'''
    if not window['is-floating']:
        return
    wid = str(window['id'])
    display = json_run(['yabai', '-m', 'query', '--displays', '--window', wid])
    win = window['frame']
    dis = display['frame']
    x = dis['x'] + (dis['w'] - win['w']) / 2
    y = dis['y'] + (BAR_HEIGHT + dis['h'] - win['h']) / 2
    run(['yabai', '-m', 'window', wid, '--move', f'abs:{x}:{y}'])


def move_tiled(window, direction):
    '''Move tiled window'''
    match direction:
        case 'west' | 'east' | 'north' | 'south':
            run(f'''yabai -m window --swap {direction} \\
                || (yabai -m window --display {direction} \\
                    && yabai -m window --focus {window['id']})''',
                shell=True)


def move_floating(window, direction: str, amount):
    '''Move floating window for a certain amount, to the edge or center of the display'''
    wid = str(window['id'])
    if direction == 'center':
        center(window)
    elif amount == 'edge':
        display = json_run(['yabai', '-m', 'query', '--displays', '--window', wid])
        win = window['frame']
        dis = display['frame']
        match direction:
            case 'west':
                x = dis['x'] - win['x']
                y = 0
            case 'east':
                x = dis['x'] + dis['w'] - win['x'] - win['w']
                y = 0
            case 'north':
                x = 0
                y = BAR_HEIGHT + dis['y'] - win['y']
            case 'south':
                x = 0
                y = dis['y'] + dis['h'] - win['y'] - win['h']
            case _:
                print('move_floating: unknown direction', direction)
                exit(1)
        run(['yabai', '-m', 'window', wid, '--move', f'rel:{x}:{y}'])
    elif amount == 'display':
        run(['yabai', '-m', 'window', wid, '--display', direction])
        run(['yabai', '-m', 'window', '--focus', wid])
    else:
        amount = int(amount)
        match direction:
            case 'west':
                rel = f'rel:{-amount}:0'
            case 'east':
                rel = f'rel:{amount}:0'
            case 'north':
                rel = f'rel:0:{-amount}'
            case 'south':
                rel = f'rel:0:{amount}'
            case _:
                print('move_floating: unknown direction', direction)
                exit(1)
        run(['yabai', '-m', 'window', wid, '--move', rel])


def move_to_switch(window, space):
    '''Move window to another space and focus on it'''
    wid = str(window['id'])

    run(['yabai', '-m', 'window', wid, '--space', space])
    run(['yabai', '-m', 'window', '--focus', wid])


# --- focus ---
def focus_toggle():
    '''Focus the first floating window if the focused window is tiled, and vice versa'''
    windows = json_run('yabai -m query --windows --space')

    floating = []
    tiled = []
    focused_floating = None

    for w in windows:
        if not w['is-visible'] or w['is-minimized'] or w['is-hidden']:
            continue
        if w['is-floating']:
            floating.append(w)
        else:
            tiled.append(w)
        if w['has-focus']:
            focused_floating = w['is-floating']

    if focused_floating is None:
        # no focused window. focus on floating window first
        if floating:
            target = floating[0]['id']
            run(f'yabai -m window --focus {target}'.split())
        elif tiled:
            target = tiled[0]['id']
            run(f'yabai -m window --focus {target}'.split())
        return

    if not tiled or not floating:
        return
    target = tiled[0]['id'] if focused_floating else floating[0]['id']
    run(f'yabai -m window --focus {target}'.split())


def focus_first():
    '''Focus on the first window in the current space'''
    windows = json_run('yabai -m query --windows --space')
    if windows and windows[0]['is-visible']:
        run(f'yabai -m window --focus {windows[0]["id"]}'.split())


def focus_tiling(direction):
    '''Switch focus between tiled or stacked windows, or focus on another
    display if there is no other tiled window in the direction'''
    space = json_run('yabai -m query --spaces --space')

    # Use stack navigation with loopback if we have multiple stacked windows
    if space['type'] == 'stack' and (direction == 'north' or direction == 'south'):
        STACK_DIRECTION = { 'south': 'stack.next', 'north': 'stack.prev' }
        STACK_LOOPBACK = { 'south': 'stack.first', 'north': 'stack.last' }
        # Check if there are multiple windows in the stack
        space_windows = json_run('yabai -m query --windows --space')
        stacked_windows = [
            w for w in space_windows
            if not w.get("is-floating", True) and w.get("is-visible", False) and w.get("stack-index", 0) > 0
        ]
        if len(stacked_windows) > 1:
            run(f'''yabai -m window --focus {STACK_DIRECTION[direction]} ||
                    yabai -m window --focus {STACK_LOOPBACK[direction]}''', shell=True)
            return

    # Default behavior for all other cases
    run(f'''yabai -m window --focus {direction} ||
            yabai -m display --focus {direction}''', shell=True)


def focus_floating(direction, curr):
    '''Switch focus between floating windows, or focus on another display if
    there is no other floating window in the direction'''
    floating_windows = [w for w in json_run('yabai -m query --windows --space')
                        if (w['is-floating'] and w['is-visible']
                            and not w['is-minimized'] and not w['is-hidden'])]
    if direction == 'north':
        coord = 'y'
        op = operator.lt
    elif direction == 'south':
        coord = 'y'
        op = operator.gt
    elif direction == 'west':
        coord = 'x'
        op = operator.lt
    elif direction == 'east':
        coord = 'x'
        op = operator.gt
    else:
        return
    target = None
    for w in floating_windows:
        if w['id'] == curr['id']:
            continue
        if w['frame'][coord] == curr['frame'][coord]:
            # compare the other coordinate if the assigned coordinate is the same
            coord = 'y' if coord == 'x' else 'x'
        if op(w['frame'][coord], curr['frame'][coord]):
            if target is None:
                target = w
            elif not op(w['frame'][coord], target['frame'][coord]):
                target = w
    if target is not None:
        run(f'yabai -m window --focus {target["id"]}'.split())
    else:
        run(f'yabai -m display --focus {direction}'.split())


if __name__ == '__main__':
    cmd = sys.argv[1]
    match cmd:
        case 'move':
            window = current_window()
            if not window:
                exit(0)
            if window['is-floating']:
                move_floating(window, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'display')
            else:
                move_tiled(window, sys.argv[2])
        case 'move-to-switch':
            window = current_window()
            if not window:
                exit(0)
            move_to_switch(window, sys.argv[2])
        case 'focus':
            arg = sys.argv[2]
            match arg:
                case 'toggle':
                    focus_toggle()
                case 'first':
                    focus_first()
                case 'west' | 'east' | 'north' | 'south':
                    curr = current_window()
                    if curr and curr['is-floating']:
                        focus_floating(arg, curr)
                    else:
                        focus_tiling(arg)
        case _:
            print('unknown command', cmd)
