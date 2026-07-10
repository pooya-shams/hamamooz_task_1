#!/usr/bin/env python3

import sys


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

def main():
    parse_line("""62.175.167.52 - - [01/Jun/2026:00:00:00 +0000] "GET / HTTP/1.1" 200 8956 "-" "python-requests/2.31.0"\n""")
    parse_line("""garbage_line<<<12213""")


if __name__ == "__main__":
    main()

