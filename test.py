#!/usr/bin/env python3

import unittest

import main

class TestParser(unittest.TestCase):
    def test_proper_line(self):
        line = '198.203.194.124 - - [01/Jun/2026:04:51:39 +0000] "GET /api/search HTTP/1.1" 200 6778 "-" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"'
        expected_output = ('198.203.194.124',
                '-',
                '-',
                '[01/Jun/2026:04:51:39 +0000]',
                '"GET /api/search HTTP/1.1"',
                '200',
                '6778',
                '"-"',
                '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"')
        fields = main.parse_line(line)
        self.assertEqual(fields, expected_output)
        log = main.interpret_fields(fields)
        self.assertEqual(log.ip, "198.203.194.124")
        self.assertEqual(log.ident, "-")
        self.assertEqual(log.user, "-")
        self.assertEqual(log.time, (4, 51, 39))
        self.assertEqual(log.req, "GET /api/search HTTP/1.1")
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.bytes, 6778)
        self.assertEqual(log.referrer, '-')
        self.assertEqual(log.user_agent, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")

    def test_bad_line(self):
        line = "garbage-683 <<< malformed line"
        self.assertRaises(ValueError, lambda : main.parse_line(line))

if __name__ == '__main__':
    unittest.main()
