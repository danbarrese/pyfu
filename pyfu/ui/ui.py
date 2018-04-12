import termbox as Termbox
import subprocess
import threading
import _thread

from pyfu.util import props


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
            x=0,
            y=0,
            end_x=150,
            end_y=140,
            border_fg=Color.WHITE,
            border_bg=Color.DEFAULT,
            fg=Color.WHITE,
            bg=Color.DEFAULT
    ):
        self.termbox = termbox
        self.x = x
        self.y = y
        if self.x > 1:
            self.x -= 1
        if self.y > 1:
            self.y -= 1
        self.end_x = end_x
        self.end_y = end_y
        self.border_fg = border_fg
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

    def append(self, contents):
        self.write(self.contents + contents)

    def _write_header(self):
        i = 0
        if self.header:
            hdr = '  ' + self.header + '  '
            for row in range(self.y + 1, self.end_y - 1):
                if i >= len(hdr):
                    return
                for col in range(self.x + 1, self.end_x - 1):
                    self.termbox.change_cell(col, row, ord(hdr[i]), Color.BLACK, self.border_fg)
                    i += 1
                    if i >= len(hdr):
                        return

    def write(self, contents):
        self.clear()
        self.contents = contents
        i = 0
        j = self.y + 1
        if self.header:
            j += 1
        just_encountered_newline = False
        self._write_header()
        for row in range(j, self.end_y - 1):
            if i >= len(self.contents):
                return
            if not self.allow_wrap and not just_encountered_newline and i > 0:
                return
            for col in range(self.x + 1, self.end_x - 1):
                if self.contents[i] == '\n':
                    just_encountered_newline = True
                    i += 1
                    break
                just_encountered_newline = False
                self.termbox.change_cell(col, row, ord(self.contents[i]), self.fg, self.bg)
                i += 1
                if i >= len(self.contents):
                    return

    def draw_borders(self):
        # draw rows ---
        for col in range(self.x, self.end_x):
            self.termbox.change_cell(col, self.y, self.row_char, self.border_fg, self.border_bg)
            self.termbox.change_cell(col, self.end_y - 1, self.row_char, self.border_fg, self.border_bg)

        # draw columns |||
        for row in range(self.y, self.end_y):
            self.termbox.change_cell(self.x, row, self.col_char, self.border_fg, self.border_bg)
            self.termbox.change_cell(self.end_x - 1, row, self.col_char, self.border_fg, self.border_bg)

        # draw corners +++
        self.termbox.change_cell(self.x, self.y, ord('┌'), self.border_fg, self.border_bg)
        self.termbox.change_cell(self.end_x - 1, self.y, ord('┐'), self.border_fg, self.border_bg)
        self.termbox.change_cell(self.x, self.end_y - 1, ord('└'), self.border_fg, self.border_bg)
        self.termbox.change_cell(self.end_x - 1, self.end_y - 1, ord('┘'), self.border_fg, self.border_bg)

    def clear(self):
        self.contents = ''
        for row in range(self.y + 1, self.end_y - 1):
            for col in range(self.x + 1, self.end_x - 1):
                self.termbox.change_cell(col, row, self.blank_char, self.fg, self.bg)

    def refresh(self):
        contents = subprocess.Popen(
            self.refresh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        ).stdout.read().decode('utf8').strip()
        self.write(contents)
        self.termbox.present()

    def _refresh_and_reschedule(self):
        self.refresh()
        if self.refresh_rate > 0:
            thread = threading.Timer(self.refresh_rate, self._refresh_and_reschedule)
            thread.start()
            thread.join()

    def start_refreshing(self):
        _thread.start_new_thread(self._refresh_and_reschedule, ())


class Dashboard(object):
    def __init__(self, properties):
        self.properties = properties
        self.max_x = int(properties['width'])
        self.max_y = int(properties['height'])
        self.current_x = 0
        self.current_y = 0
        self.longest_y = 0
        self.boxes = []

    def add_box(self, termbox, width=60, height=20):
        if width > self.max_x:
            raise Exception("width of box cannot be wider than max_x: " + str(self.max_x))
        if height > self.max_y:
            raise Exception("height of box cannot be higher than max_y: " + str(self.max_y))
        if self.current_x + width > self.max_x:
            self.current_x = 0
            self.current_y = self.longest_y
        box = Box(termbox, x=self.current_x, end_x=self.current_x + width, y=self.current_y,
                  end_y=self.current_y + height - 1)
        self.current_x += width + 1
        if self.current_y + height > self.longest_y:
            self.longest_y = self.current_y + height
        self.boxes.append(box)
        return box

    def draw(self):
        for b in self.boxes:
            b.draw()

    def run(self):
        with Termbox.Termbox() as termbox:
            termbox.clear()

            for k in sorted(self.properties['box'].keys()):
                box_props = self.properties['box'][k]
                box = self.add_box(termbox, int(box_props['width']), int(box_props['height']))
                if 'name' in box_props:
                    box.header = box_props['name']
                box.refresh_cmd = box_props['cmd']
                if 'rate-sec' in box_props:
                    box.refresh_rate = int(box_props['rate-sec'])
                if 'color-border-fg' in box_props:
                    box.border_fg = Color.from_string(box_props['color-border-fg'])
                if 'color-border-bg' in box_props:
                    box.border_bg = Color.from_string(box_props['color-border-bg'])
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
                    if type == Termbox.EVENT_KEY:
                        if key in [Termbox.KEY_ESC, Termbox.KEY_CTRL_C]:
                            exit(0)
                        if ch == 'j':
                            self.boxes[1].border_fg = Color.RED
                            # self.draw()
                    event_here = termbox.peek_event()
