# Log file interpreter

this is a simple python program used to interpret a log file in combined log format.
there are no additional libraries used at the moment

## usage

you can simply run the script and point it to your log file using `-f` or `--file` flag.

```sh
python main.py -f access.log
```

you can ask for a basic report using the `-b` or `--basic-report` flag.

```sh
python main.py -f access.log -b
```

you can ask for a time distribution of the requests in the report using the `-t` or `--time-distribution` flag.

```sh
python main.py -f access.log -b -t
```

## testing

there are basic unit tests included in `test.py` which can simply be run.

```sh
python test.py
```

