# pyfu
Various scripts for work automation in Python 3.

## Dashboard

![dashboard example screenshot](screenshots/img.png)

### Configure

Dashboard leverages termbox to build a live dashboard made of various boxes of
different sizes and colors.  The contents of each box are the output of any
arbitrary shell command, which can be specified in the dashboard config file.

Dashboard is configured by a yaml file.  Create the file:
`~/.dashboard/dashboard.yaml` with the contents:

```
dashboards:
    - name: test
      width: 150
      height: 140
      boxes:
          - id: test0
            name: test
            cmd: echo $(date)
            width: 149
            height: 10
            color-border-fg: cyan
            color-border-bg: red
            color-content-fg: yellow
            color-content-bg: blue
            rate-sec: 1
          - id: test1
            name: test
            cmd: echo $(date)
            width: 149
            height: 30
            color-border-fg: blue
            rate-sec: 2
```

This configures 1 dashboard named `foo`.

### Run

```
./dashboard foo
```

### Dashboard colors

* white
* gray
* black
* red
* orange
* yellow
* green
* blue
* magenta
* any number from 1-256

### Controls

* `j`/`k` - select next/previous box
* `esc` - clear selection highlighting
* `r` - refresh selected box
* `R` - refresh all boxes
* `ctrl + l` - redraw all boxes

