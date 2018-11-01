import termbox as Termbox
import subprocess
import threading
import _thread
import os
import datetime
import time
from sys import exit


class Color(object):
    DEFAULT = 0
    BLACK = 1
    RED = 2
    GREEN = 3
    YELLOW = 4
    BLUE = 5
    MAGENTA = 6
    CYAN = 7
    WHITE = 8

    @staticmethod
    def from_string(color):
        c = color.lower()
        if c == 'default':
            return Color.DEFAULT
        elif c == 'black':
            return Color.BLACK
        elif c == 'red':
            return Color.RED
        elif c == 'green':
            return Color.GREEN
        elif c == 'yellow':
            return Color.YELLOW
        elif c == 'blue':
            return Color.BLUE
        elif c == 'magenta':
            return Color.MAGENTA
        elif c == 'cyan':
            return Color.CYAN
        elif c == 'white':
            return Color.WHITE
        else:
            return Color.DEFAULT


class Box(object):
    def __init__(
            self,
            termbox,
            col=0,
            row=0,
            end_row=150,
            end_col=140,
            border_fg=Color.WHITE,
            border_bg=Color.DEFAULT,
            fg=Color.WHITE,
            bg=Color.DEFAULT
    ):
        self.termbox = termbox
        self.col = col
        self.row = row
        if self.col > 1:
            self.col -= 1
        if self.row > 1:
            self.row -= 1
        self.end_row = end_row
        self.end_col = end_col
        self.border_fg = border_fg
        self.orig_border_fg = border_fg
        self.orig_border_bg = border_bg
        self.border_bg = border_bg
        self.fg = fg
        self.bg = bg
        self.allow_wrap = True
        self.col_char = ord('│')
        self.row_char = ord('─')
        self.intersection_char = ord('┼')
        self.blank_char = ord(' ')
        self.contents = ''
        self.refresh_cmd = 'echo "hello world"'
        self.refresh_rate = 0
        self.header = None
        self.status = None
        self.id = None

    def draw(self):
        self.draw_borders()
        self.rewrite()

    def no_wrap(self):
        self.allow_wrap = False

    def transparent_borders(self):
        self.col_char = self.blank_char
        self.row_char = self.blank_char
        self.intersection_char = self.blank_char

    def rewrite(self):
        self.write(self.contents)

    def redraw_border(self):
        self.draw_borders()
        self._write_header()
        self.write_status(self.status)

    def reset_border(self):
        self.border_fg = self.orig_border_fg
        self.border_bg = self.orig_border_bg
        self.redraw_border()

    def append(self, contents):
        self.write(self.contents + contents)

    def _write_header(self):
        i = 0
        if self.header:
            hdr = '  ' + self.header + '  '
            for col in range(self.col + 2, self.end_col):
                self.termbox.change_cell(col, self.row, ord(hdr[i]), Color.BLACK, self.border_fg)
                i += 1
                if i >= len(hdr):
                    return

    def write(self, contents):
        self.clear()
        self.contents = contents
        i = 0
        j = self.row + 1
        just_encountered_newline = False
        self._write_header()
        for row in range(j, self.end_row):
            if i >= len(self.contents):
                return
            if not self.allow_wrap and not just_encountered_newline and i > 0:
                return
            for col in range(self.col + 1, self.end_col):
                if self.contents[i] == '\n':
                    just_encountered_newline = True
                    i += 1
                    break
                just_encountered_newline = False
                self.termbox.change_cell(col, row, ord(self.contents[i]), self.fg, self.bg)
                i += 1
                if i >= len(self.contents):
                    return

    def write_status(self, status):
        self.status = status
        if not self.status:
            return
        i = 0
        for col in range(self.col + 2, self.end_col - 1):
            self.termbox.change_cell(col, self.end_row, ord(self.status[i]), self.border_fg, self.bg)
            i += 1
            if i >= len(self.status):
                return

    def draw_borders(self):
        # draw rows ---
        for col in range(self.col, self.end_col):
            self.termbox.change_cell(col, self.row, self.row_char, self.border_fg, self.border_bg)
            self.termbox.change_cell(col, self.end_row, self.row_char, self.border_fg, self.border_bg)

        # draw columns |||
        for row in range(self.row + 1, self.end_row):
            self.termbox.change_cell(self.col, row, self.col_char, self.border_fg, self.border_bg)
            self.termbox.change_cell(self.end_col, row, self.col_char, self.border_fg, self.border_bg)

        # draw corners +++
        self.termbox.change_cell(self.col, self.row, ord('┌'), self.border_fg, self.border_bg)
        self.termbox.change_cell(self.end_col, self.row, ord('┐'), self.border_fg, self.border_bg)
        self.termbox.change_cell(self.col, self.end_row, ord('└'), self.border_fg, self.border_bg)
        self.termbox.change_cell(self.end_col, self.end_row, ord('┘'), self.border_fg, self.border_bg)

    def clear(self):
        self.contents = ''
        for row in range(self.row + 1, self.end_row):
            for col in range(self.col + 1, self.end_col):
                self.termbox.change_cell(col, row, self.blank_char, self.fg, self.bg)
        self._write_header()

    def refresh(self, use_cache=False):
        before = datetime.datetime.now()

        if use_cache:
            contents = [line.rstrip('\n') for line in open('/tmp/dashboard_' + self.id)]
            contents = '\n'.join(contents)
        else:
            contents = subprocess.Popen(
                self.refresh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True
            ).stdout.read().decode('utf8').strip()

        # write to file, for caching
        output = open('/tmp/dashboard_' + self.id, 'w')
        output.write(contents)
        output.close()

        now = datetime.datetime.now()
        self.write(contents)
        took = str(round((now - before).total_seconds(), 1))
        if use_cache:
            self.write_status('{} - cached - next in {}'.format(now.strftime('%H:%M:%S'), self.refresh_rate))
        else:
            self.write_status('{} - took {} - next in {}'.format(now.strftime('%H:%M:%S'), took, self.refresh_rate))
        self.redraw_border()
        self.termbox.present()

    def _refresh_and_reschedule(self):
        do_cache = False
        if self.refresh_rate > 0:
            cache_filename = '/tmp/dashboard_' + self.id
            if os.path.isfile(cache_filename):
                mtime = os.path.getmtime(cache_filename)
                do_cache = mtime > (time.time() - self.refresh_rate + 5) # the +5sec is to make sure the comparison doesn't fail if there's any tiny time comparison issues.
        self.refresh(use_cache=do_cache)
        if self.refresh_rate > 0:
            thread = threading.Timer(self.refresh_rate, self._refresh_and_reschedule)
            thread.start()
            thread.join()

    def start_refreshing(self):
        _thread.start_new_thread(self._refresh_and_reschedule, ())


class Dashboard(object):
    def __init__(self, properties, name):
        self.name = name
        self.properties = properties[name]
        self.auto_size = False
        if self.properties['width'] and str(self.properties['height']) == 'auto':
            self.max_row, self.max_col = os.popen('stty size', 'r').read().split()
            self.max_row = int(self.max_row)
            self.max_col = int(self.max_col)
            self.auto_size = True
        else:
            self.max_col = int(self.properties['width'])
            self.max_row = int(self.properties['height'])
        self.current_row = 0
        self.current_col = 0
        self.longest_row = 0
        self.boxes = []
        self.current_box = -1

    def redraw(self, termbox):
        for box in self.boxes:
            box.rewrite()
            box.reset_border()
            termbox.present()

    def add_box(self, termbox, width, height):
        if width > self.max_col:
            raise Exception("width of box ({width}) cannot be wider than max_row: {self.max_row}".format(**locals()))
        if height > self.max_row:
            raise Exception("height of box ({height}) cannot be higher than max_col: {self.max_col}".format(**locals()))
        if self.current_col + width > self.max_col:
            self.current_col = 0
            self.current_row = self.longest_row + 1
        box = Box(termbox, col=self.current_col, end_col=self.current_col + width - 1, row=self.current_row,
                  end_row=self.current_row + height - 1)
        self.current_col += width + 1
        if self.current_row + height > self.longest_row:
            self.longest_row = self.current_row + height
        self.boxes.append(box)
        return box

    def current(self):
        if self.current_box == -1:
            self.current_box = 0
        return self.boxes[self.current_box]

    def next(self):
        if self.current_box + 1 == len(self.boxes):
            self.current_box = 0
        else:
            self.current_box += 1
        return self.boxes[self.current_box]

    def previous(self):
        if self.current_box <= 0:
            self.current_box = len(self.boxes) - 1
        else:
            self.current_box -= 1
        return self.boxes[self.current_box]

    def draw(self):
        for b in self.boxes:
            b.draw()

    def _get_width_height(self, box_props, box_count):
        if self.auto_size:
            if box_count >= 6:
                return int(self.max_col / 2) - 1, int(self.max_row / (box_count/2))
            else:
                return self.max_col, int(self.max_row / box_count)
        else:
            return int(box_props['width']), int(box_props['height'])

    def run(self):
        with Termbox.Termbox() as termbox:
            termbox.clear()

            for k in sorted(self.properties['box'].keys()):
                box_props = self.properties['box'][k]
                width, height = self._get_width_height(box_props, len(self.properties['box']))
                box = self.add_box(termbox, width, height)
                box.id = '{}_{}'.format(self.name, k)
                if 'name' in box_props:
                    box.header = box_props['name']
                box.refresh_cmd = box_props['cmd']
                if 'rate-sec' in box_props:
                    box.refresh_rate = int(box_props['rate-sec'])
                if 'color-border-fg' in box_props:
                    box.border_fg = Color.from_string(box_props['color-border-fg'])
                    box.orig_border_fg = box.border_fg
                if 'color-border-bg' in box_props:
                    box.border_bg = Color.from_string(box_props['color-border-bg'])
                    box.orig_border_bg = box.border_bg
                if 'color-content-fg' in box_props:
                    box.fg = Color.from_string(box_props['color-content-fg'])
                if 'color-content-bg' in box_props:
                    box.bg = Color.from_string(box_props['color-content-bg'])

            self.draw()
            termbox.present()

            # This uses a new thread to spawn all refresh threads.
            # Each refresh thread blocks the spawn thread, instead of the main thread.
            for box in self.boxes:
                box.start_refreshing()

            # Now use the main thread to wait for user input of any kind.
            while True:
                event_here = termbox.poll_event()
                while event_here:
                    (type, ch, key, mod, w, h, x, y) = event_here
                    if type == Termbox.EVENT_RESIZE:
                        self.redraw(termbox)
                    elif type == Termbox.EVENT_KEY:
                        if key == Termbox.KEY_ESC:
                            self.current().reset_border()
                        elif key == Termbox.KEY_CTRL_C:
                            exit(0)
                        elif ch == 'R':
                            for box in self.boxes:
                                box.clear()
                                box.write("loading...")
                                termbox.present()
                                _thread.start_new_thread(box.refresh, ())
                        elif ch == 'r':
                            box = self.current()
                            box.clear()
                            box.write("loading...")
                            termbox.present()
                            box.refresh()
                        elif ch == 'j':
                            self.current().reset_border()
                            nex = self.next()
                            old_fg = nex.border_fg
                            nex.border_fg = nex.border_bg
                            nex.border_bg = old_fg
                            nex.draw_borders()
                            nex.write_status(nex.status)
                            nex.border_fg = nex.orig_border_fg
                            nex.border_bg = nex.orig_border_bg
                            nex._write_header()
                        elif ch == 'k':
                            self.current().reset_border()
                            pre = self.previous()
                            old_fg = pre.border_fg
                            pre.border_fg = pre.border_bg
                            pre.border_bg = old_fg
                            pre.draw_borders()
                            pre.write_status(pre.status)
                            pre.border_fg = pre.orig_border_fg
                            pre.border_bg = pre.orig_border_bg
                            pre._write_header()
                        elif key == Termbox.KEY_CTRL_L:
                            self.redraw(termbox)
                    elif type == Termbox.EVENT_MOUSE:
                        self.current().reset_border()
                        exit(0)
                    event_here = termbox.peek_event()
                    termbox.present()