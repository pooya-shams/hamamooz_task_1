# Log file interpreter

this is a simple python program used to interpret a log file in combined log format.
there are no additional libraries used at the moment

## usage

you can simply run the script and point it to your log file using `-f` or `--file` flag. the program supports using gzip-compressed files but that should be explicitly mentioned using the `--gzip` or `-g` flag. automatically detecting the file format is possible using the mime type libraries but is kinda pointless here because it will add yet another dependency to this small program which is using only the standard library for now. it also isn't really helping because anyone using the program will probably know if their log file is compressed or not. there is also the option of using the filename as an indicator but it's not reliable because sometimes gzip-compressed files are renamed with different extensions (you can look at [tachiyomi backup](https://github.com/mihonapp/mihon#:~:text=backups) files for an example). so ultimately just using a flag is the best solution I came up with.

for using a normal text file:
```sh
python main.py -f access.log
```

for using a gzip-compresssed file:
```sh
python main.py -g -f access.log
```

you can ask for a basic report using the `-b` or `--basic-report` flag.

```sh
python main.py -f access.log -b
```

you can ask for a time distribution of the requests in the report using the `-t` or `--time-distribution` flag.

```sh
python main.py -f access.log -b -t
```

you can specify the number of required top ips in the report using the `-n` or `--ip-count` flag. the default is 10.

```sh
python main.py -f access.log -b -n 10
```

you can check for unusual login attempts by using the `-l` or `--login-attack` flag. if no argument is supplied, the required number of attempts to mark this ip as an attacker is 10. otherwise the supplied count is used as the threshold.

```sh
python main.py -f access.log -b -l 100
```


## testing

there are basic unit tests included in `test.py` which can simply be run.

```sh
python test.py
```

