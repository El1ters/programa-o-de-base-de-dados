#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2023 ajccosta

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# Author: Andre Costa
#   changed by Vitor Duarte

# test proj_ice.py with files in tests directory


import sqlite3
from contextlib import redirect_stdout
import traceback
import io
import os
import sys
# import fileinput
# from mooshak_helper import MooshakHelper
import builtins

# import main
import importlib


use_colors = True
try:
    from colorama import Fore
    from colorama import Style
except ImportError:
    use_colors = False


def prerun( main ):
    """ pre check if some function are working 
    """
    print("Checking some functions...")
    error=False
    try:
        c = sqlite3.connect(':memory:')
        main.cmd_create_tables(c)
        resp = c.execute("pragma main.table_list(Tests);").fetchall()[0]
        if resp[1].lower()!='tests' or resp[3]!=5: error=True
    except: error = True
    if error: print("function cmd_create_tables not working")
    error2=False
    try:
        main.cmd_load_test(c, 'data/file_1.txt')
        resp = c.execute("select * from Tests;").fetchall()[0]
        if resp!=(4, 'IUORBA', 2003, 200.0, 'Not Certified'): error2=True
    except: error2=True
    if error2: print("function cmd_load_test not working")
    
    c.close()
    return not ( error or error2)
        
    
    
def posrun(dbfile, file):
    """ run after one test (after running 'file' test)
        if needed, use to adapt to the project being tested
        to include special tests that don't just use input files
    """
    db = sqlite3.connect(dbfile, isolation_level=None)
      
    if file == '1_create.txt':
        resp = db.execute("pragma main.table_list(Tests);").fetchall()[0]
        print("table:", resp[1], resp[3], "columns")
        resp = db.execute("pragma main.table_list(Samples);").fetchall()[0]
        print("table:", resp[1], resp[3], "columns")
        
    elif file == '2_load.txt':
        resp = db.execute("select * from Tests;").fetchall()[0]
        print(resp)
        resp = db.execute("select * from Samples;").fetchall()[0]
        print(resp)
    elif file == '5_extra.txt':
        resp = db.execute("select * from Tests;").fetchall()
        print(resp)
        with open('foo') as f:
            for l in f.readlines():
                print(l.rstrip())
    db.close()


def mooshak():
    """ run the tests
    """
    orig_print = builtins.print
    orig_input = builtins.input

    try: 
        os.mkdir("outs")
    except:
        pass
    
    try: 
        print('Reading proj_ice...')
        main = importlib.import_module("proj_ice")
    except Exception as e:
        print(e,'\nCan\'t continue.')
        return

    if not prerun(main):
       print('Can\'t continue.')
       return
    else: print('passed\n')
              
    passedAllTests = True
    
    for file in sorted(os.listdir("tests/in")):
        print("Testing tests/in/", file)

        f = io.StringIO()
        diff = False

        try:
            # adapt to the project to test:
            print(f"  running: process_cmds('test.db', '{file}')")
            with redirect_stdout(f):
                cmds = open("tests/in/"+file)
                main.process_cmds("test.db", cmds)
                posrun("test.db", file)
        except Exception as e:
            # Get exception info
            err = traceback.format_exc()
            print("ERROR:", err, end="")
            if use_colors:
                print(f"{Fore.RED} >> {e}{Style.RESET_ALL}")
            else:
                print(" >> ", e)
            print("Failed on test", file, end="\n")

            diff = True
            passedAllTests = False
            print('\n')
            continue

        s = f.getvalue()
        output_lines = s.splitlines()

        expected_lines = []
        teste_out = file.replace("in", "out")
        
        try:
            with open("outs/"+teste_out, "wt", encoding='utf-8') as f:
                f.write(s)
        except: pass
                
        try:
            with open('tests/out/' + teste_out, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    expected_lines.append(line[0:-1])
        except Exception as e:
            err = traceback.format_exc()
            print("ERROR:", e)
            expected_lines = []

        if len(output_lines) != len(expected_lines):
            if use_colors:
                print(f"{Fore.RED}Expecting", len(expected_lines),
                      "lines, got", len(output_lines), f"{Style.RESET_ALL}")
            else:
                print("Expecting", len(expected_lines),
                      "lines, got", len(output_lines))
            diff = True
            passedAllTests = False


        for i in range(min(len(expected_lines), len(output_lines))):
            if (output_lines[i] != expected_lines[i]):
                print("Line", i, "is different")
                print("Expecting:", [expected_lines[i]])
                print("Got:      ", [output_lines[i]])
                diff = True
                passedAllTests = False

        for i in range(min(len(expected_lines), len(output_lines)), max(len(expected_lines), len(output_lines))):
            if i >= len(expected_lines):
                print("Got:      ", [output_lines[i]])
            else:
                print("Expecting:", [expected_lines[i]])

        if not diff:
            if use_colors:
                print(f"{Fore.GREEN}Passed test!{Style.RESET_ALL}")
            else:
                print("Passed test!")
        else:
            if use_colors:
                print(f"{Fore.RED}Test Failed!{Style.RESET_ALL}")
            else:
                print("Test Failed!")
        print("\n")

    if passedAllTests:
        if use_colors:
            print(f"{Fore.GREEN}** Passed all tests! **{Style.RESET_ALL}")
        else:
            print("** Passed all tests! **")
    

    builtins.input = orig_input


###################

mooshak()
