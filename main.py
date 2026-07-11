#!/usr/bin/env python3

import sys
import argparse
import pathlib
import os
import re
from timeit import default_timer as timer
import gzip

class log_line:
    """
    the current fields are
    <ip> <ident> <user> <timestamp> <request line> <status code> <bytes sent> <referrer> <user agent>
    """
    def __init__(self):
        self.ip = None
        self.ident = None
        self.user = None
        self.time = None
        self.req = None
        self.status_code = None
        self.bytes = None
        self.referrer = None
        self.user_agent = None

    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return f"<{self.__class__.__name__}: {{{', '.join(items)}}}>"

    def _match_ip(ip):
        r = re.compile("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        if r.match(ip) is None:
            return None
        return ip

    def _match_str(string):
        if string.startswith('"') and string.endswith('"'):
            return string[1:-1]
        elif string.startswith("'") and string.endswith("'"):
            return string[1:-1]
        return string

    def _match_time(timestamp):
        pattern = r"(\d{2}):(\d{2}):(\d{2})\s*([+-])(\d{2})(\d{2})" # matches the "00:00:00 +0000" part
        match = re.search(pattern, timestamp)
        if match:
            h, m, s = map(int, match.group(1, 2, 3))
            sign = match.group(4)
            tz_h, tz_m = map(int, match.group(5, 6))
            total_seconds = (h * 3600) + (m * 60) + s
            tz_total_seconds = (tz_h * 3600) + (tz_m * 60)
            #
            if sign == '+':
                total_seconds -= tz_total_seconds # +0330 time zone means UTC is local_time-00:03:30
            else:
                total_seconds += tz_total_seconds
            #
            total_seconds = total_seconds % 86400
            utc_hour = total_seconds // 3600
            utc_minute = (total_seconds % 3600) // 60
            utc_second = total_seconds % 60
            return (utc_hour, utc_minute, utc_second)
        else:
            return None

    def _match_int(code):
        try:
            return int(code)
        except:
            return None

    # these functions are used to interpret the fields. I thought it would be cleaner than doing 9 if statements
    funcs = (_match_ip, _match_str, _match_str, _match_time, _match_str, _match_int, _match_int, _match_str, _match_str)
    names = ("ip", "ident", "user", "time", "req", "status_code", "bytes", "referrer", "user_agent")

    def set_from_tuple(self, fields):
        """
        sets the values from the given tuple. must be proper length or it will throw ValueError
        """
        if type(fields) != tuple:
            raise TypeError("Bad type for argument fields")
        if len(fields) != 9: # I really should change this magic number to a constant or better mechanism
            raise ValueError(f"Bad length for argument fields {len(fields)}")
        #
        for func, name, field in zip(log_line.funcs, log_line.names, fields):
            self.__dict__[name] = func(field)

def split_line(line):
    """
    splits the line into the fields. takes two types of special characters into account.
    [] and "" will be considered string literals and the space between them will not be
    parsed. otherwise the string is split into space seperated substrings.
    inputs:
        line: string. the input line
    outputs:
        a list of the fields as strings
    """
    output_list = []
    st = [] # using a list as an stack for storing the brackets indices. should be fine because python handles the space
    last = -1
    for i, c in enumerate(line):
        if c == ' ':
            if not st: # if the bracket stack is not empty we ignore the spaces
                output_list.append(line[last+1:i])
                last = i
        elif c == '[':
            st.append(i)
        elif c == ']':
            if st and line[st[-1]] == '[':
                st.pop()
            else:
                raise ValueError(f"malformed brackets in line. {i}")
        elif c == '"':
            if st and line[st[-1]] == '"':
                st.pop()
            else:
                st.append(i)
        else:
            pass
    if st:
        raise ValueError("unclosesd string at the end of line")
    output_list.append(line[last+1:])
    return output_list


def parse_line(line):
    """
    parse a single log line with this format
    <ip> <ident> <user> <timestamp> <request line> <status code> <bytes sent> <referrer> <user agent>
    inputs:
        line: string
    output:
        a tuple of the fields values or an error
    """
    fields = split_line(line)
    if len(fields) != 9: # the len should be 9 maybe not use a magic number but not now
        raise ValueError(f"malformed line bad number of fields extracted {len(fields)}")
    return tuple(fields)

def interpret_fields(fields):
    """ expects a tuple of fields and returns a structured """
    log = log_line()
    log.set_from_tuple(fields)
    return log

def basic_report(args, req_count, error_count, ips_reqs):
    if args.basic_report:
        print("=== Basic report ===")
        print("[info] Total reqs", req_count)
        print("[info] Total error", error_count, f"({error_count / req_count:.2%})")
        print("[info] Total ips", len(ips_reqs))
        # getting top ips by request number
        top_ips = sorted(ips_reqs.items(), key=lambda x: -x[1])[:args.ip_count]
        print(f"[info] Top {args.ip_count} ips by number of requests")
        for ip, count in top_ips:
            print("\t", ip, ":", count)
        print()

def time_dist_report(args, hour_reqs, hour_errs):
    if args.time_distribution:
        print("=== Request count by time ===")
        print("[info] Peak requests hour is marked with *\n")
        print("hour\t\trequests\t\terror")
        peak_hour = hour_reqs.index(max(hour_reqs))
        for i, (req, err) in enumerate(zip(hour_reqs, hour_errs)):
            print(f"{i:2.0f}"+ ("*" if i == peak_hour else ""), req, err, sep="\t\t")
        print()

def login_report(args, failed_login_attempts):
    if args.login_attack:
        print("=== Failed login attempts ===")
        for ip, count in failed_login_attempts.items():
            if count > args.login_attack:
                print(ip, "attempted without success", count, "times")
        print()

def enumerate_file(f, args):
    req_count = 0 # total number of requests
    ips_reqs = dict() # total number of requests for each ip, the lenght will be used as total number of unique ips
    failed_login_attempts = dict() # number of failed login attempts from each ip
    error_count = 0 # number of requests answered with 4xx or 5xx
    hour_reqs = [0] * 24
    hour_errs = [0] * 24
    while (line := f.readline()) != '':
        line = line.strip()
        try:
            fields = parse_line(line)
            log = interpret_fields(fields)
            req_count += 1
            if log.ip != None:
                ips_reqs[log.ip] = ips_reqs.get(log.ip, 0) + 1
            is_err = bool(log.status_code is not None and 400 <= log.status_code < 600)
            error_count += is_err # bool adds 0 or 1 to int
            # for the time table
            if log.time is not None:
                hour = log.time[0]
                if 0 <= hour < 24:
                    hour_reqs[hour] += 1
                    hour_errs[hour] += is_err
            if is_err and log.req is not None and "login" in log.req:
                failed_login_attempts[log.ip] = failed_login_attempts.get(log.ip, 0) + 1
        except ValueError as e:
            if args.verbose:
                print(f"[warning] bad line {line}", file=sys.stderr)
    #
    basic_report(args, req_count, error_count, ips_reqs)
    time_dist_report(args, hour_reqs, hour_errs)
    login_report(args, failed_login_attempts)

def run(args):
    if args.file is None or not os.path.isfile(args.file):
        raise FileNotFoundError(f"{args.file} doesn't exists")
    
    if args.gzip:
        with gzip.open(args.file, "rt") as f:
            enumerate_file(f, args)
    else:
        with open(args.file, "r") as f: # throws error if a proper file is not supplied
            enumerate_file(f, args)

def main():
    aparser = argparse.ArgumentParser()
    aparser.add_argument("-g", "--gzip", help="use a gzip compressed file", action="store_true")
    aparser.add_argument("-f", "--file", help="log file", required=True)
    aparser.add_argument("-b", "--basic-report", action="store_true", help="show basic report")
    aparser.add_argument("-t", "--time-distribution", action="store_true", help="show time distribution of accesses")
    aparser.add_argument("-n", "--ip-count", help="number of top ips in report", type=int, default=10)
    aparser.add_argument("-l", "--login-attack", help="find any ip with high number of login attempts. you can specify the required number of attempts to flag this ip. the default is 10", nargs="?", type=int, const=10, default=None)
    aparser.add_argument("-v", "--verbose", action="store_true")
    args = aparser.parse_args()

    start = timer()
    run(args)
    end = timer()
    print("[done] ellapsed time:", end-start)

if __name__ == "__main__":
    main()

