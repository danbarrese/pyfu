# pyfu
Various scripts for work automation in Python 3.

## Dashboard

### Configure

Dashboard is configured by a yaml file.  Create the file:
`~/.dashboard/dashboard.yaml` with contents:

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
* black
* red
* orange
* yellow
* green
* blue
* magenta
* orange
* gray
* any number from 1-256
