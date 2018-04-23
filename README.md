# pyfu
Various scripts for work automation in Python 3.

## Dashboard

### Configure

Dashboard is configured by a properties file.  Create a properties file:
`~/.dashboard/dashboard.properties` with contents:

```
# ------------------------
# "foo" dashboard
# ------------------------

dashboard.foo.width=150
dashboard.foo.height=140

dashboard.foo.box.0.name=Foo
dashboard.foo.box.0.width=149
dashboard.foo.box.0.height=10
dashboard.foo.box.0.color-border-fg=cyan
dashboard.foo.box.0.cmd=echo "$(date)"
dashboard.foo.box.0.rate-sec=1

dashboard.foo.box.1.name=Foo
dashboard.foo.box.1.width=149
dashboard.foo.box.1.height=30
dashboard.foo.box.1.color-border-fg=blue
dashboard.foo.box.1.cmd=echo "$(date)"
dashboard.foo.box.1.rate-sec=2

# ------------------------
# "bar" dashboard
# ------------------------ 
dashboard.bar.width=150
dashboard.bar.height=140

dashboard.bar.box.0.name=Bar
dashboard.bar.box.0.width=49
dashboard.bar.box.0.height=15
dashboard.bar.box.0.color-border-fg=red
dashboard.bar.box.0.cmd=echo "$(date)"
dashboard.bar.box.0.rate-sec=120

dashboard.bar.box.1.name=Bar
dashboard.bar.box.1.width=49
dashboard.bar.box.1.height=15
dashboard.bar.box.1.color-border-fg=blue
dashboard.bar.box.1.cmd=echo "$(date)"
dashboard.bar.box.1.rate-sec=120

dashboard.bar.box.2.name=Bar
dashboard.bar.box.2.width=49
dashboard.bar.box.2.height=15
dashboard.bar.box.2.color-border-fg=blue
dashboard.bar.box.2.cmd=echo "$(date)"
dashboard.bar.box.2.rate-sec=120
```

This configures 2 dashboards named `foo` and `bar`.

### Run

```
./dashboard foo
```

```
./dashboard bar
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
