# -*- coding: utf-8 -*-
#
# gdb-frontend is a easy, flexible and extensionable gui debugger
#
# https://github.com/rohanrhu/gdb-frontend
# https://oguzhaneroglu.com/projects/gdb-frontend/
#
# Licensed under GNU/GPLv3
# Copyright (C) 2019, Oğuzhan Eroğlu (https://oguzhaneroglu.com/) <rohanrhu2@gmail.com>

import os
import sys
import shutil
import json
import base64
import subprocess

import config
config.init()

import statics
import util

path = os.path.dirname(os.path.realpath(__file__))

gdb_executable = "gdb"
tmux_executable = "tmux"
terminal_id = "gdb-frontend"
is_random_port = False

arg_config = {}

def argHandler_gdbExecutable(path):
    global gdb_executable

    if not os.path.exists(path):
        print("[Error] GDB executable: "+path+" not found.\n")
        exit(0)

    gdb_executable = path

def argHandler_tmuxExecutable(path):
    global tmux_executable

    if not os.path.exists(path):
        print("[Error] Tmux executable: "+path+" not found.\n")
        exit(0)

    tmux_executable = path

def argHandler_terminalId(name):
    global terminal_id

    terminal_id = name

def argHandler_host(address):
    arg_config["HOST_ADDRESS"] = address
    config.HOST_ADDRESS = address

def argHandler_listen(address):
    arg_config["BIND_ADDRESS"] = address
    config.BIND_ADDRESS = address

def argHandler_port(port):
    global is_random_port
    
    port = int(port)

    if port == 0:
        is_random_port = True
        
        arg_config["GOTTY_PORT"] = 0
        arg_config["HTTP_PORT"] = 0
        arg_config["SERVER_PORT"] = 0

        config.GOTTY_PORT = 0
        config.HTTP_PORT = 0
        config.SERVER_PORT = 0
    else:
        arg_config["GOTTY_PORT"] = port
        arg_config["HTTP_PORT"] = port+1
        arg_config["SERVER_PORT"] = port+2

        config.GOTTY_PORT = port
        config.HTTP_PORT = port+1
        config.SERVER_PORT = port+2

def argHandler_httpPort(port):
    port = int(port)

    arg_config["HTTP_PORT"] = port
    config.HTTP_PORT = port

def argHandler_serverPort(port):
    port = int(port)

    arg_config["SERVER_PORT"] = port
    config.SERVER_PORT = port

def argHandler_gottyPort(port):
    port = int(port)
    
    arg_config["GOTTY_PORT"] = port
    config.GOTTY_PORT = port

def argHandler_readonly():
    arg_config["IS_READONLY"] = True
    config.IS_READONLY = True

def argHandler_verbose():
    config.VERBOSE = True
    arg_config["VERBOSE"] = True

def argHandler_help():
    global gdb_executable

    print("GDBFrontend is a easy, flexible and extensionable gui debugger.\n")
    print("Options:")
    print("  --help, -h:\t\t\t\tShows this help message.")
    print("  --version, -v:\t\t\tShows version.")
    print("  --gdb-executable=PATH, -g PATH:\tSpecifies GDB executable path (Default is \"gdb\" command on PATH environment variable.)")
    print("  --tmux-executable=PATH, -tmux PATH:\tSpecifies Tmux executable path (Default is \"tmux\" command on PATH environment variable.)")
    print("  --terminal-id=NAME, -t NAME:\t\tSpecifies tmux terminal identifier name (Default is \"gdb-frontend\".)")
    print("  --host=IP, -H IP:\t\t\tSpecifies current host address that you can access via for HTTP and WS servers.")
    print("  --listen=IP, -l IP:\t\t\tSpecifies listen address for HTTP and WS servers.")
    print("  --port=PORT, -p PORT:\t\t\tSpecifies port range for three ports to (Gotty: PORT, HTTP: PORT+1, WS: PORT+2 or 0 for random ports).")
    print("  --http-port=PORT:\t\t\tSpecifies HTTP server port.")
    print("  --server-port=PORT:\t\t\tSpecifies WS server port.")
    print("  --gotty-port=PORT:\t\t\tSpecifies Gotty server port.")
    print("  --readonly, -r:\t\t\tMakes code editor readonly. (Notice: This option is not related to security.)")
    print("  --verbose, -V:\t\t\tEnables verbose output.")
    print("")

    exit(0)

def argHandler_version():
    global gdb_executable

    print("GDBFrontend is a easy, flexible and extensionable gui debugger.\n")
    print("Version: " + util.versionString(statics.VERSION))
    print("")

    exit(0)

args = [
    ["--verbose", "-V", argHandler_verbose, False],
    ["--gdb-executable", "-g", argHandler_gdbExecutable, True],
    ["--tmux-executable", "-tmux", argHandler_tmuxExecutable, True],
    ["--terminal-id", "-t", argHandler_terminalId, True],
    ["--host", "-H", argHandler_host, True],
    ["--listen", "-l", argHandler_listen, True],
    ["--port", "-p", argHandler_port, True],
    ["--http-port", False, argHandler_httpPort, True],
    ["--server-port", False, argHandler_serverPort, True],
    ["--gotty-port", False, argHandler_gottyPort, True],
    ["--readonly", "-r", argHandler_readonly, False],
    ["--help", "-h", argHandler_help, False],
    ["--version", "-v", argHandler_version, False]
]

value_expected_arg = []

for _user_arg in sys.argv[1:]:
    is_exists = False

    if value_expected_arg:
        value_expected_arg[2](_user_arg)
        value_expected_arg = []

        continue

    for _arg in args:
        if len(_user_arg) > 2 and _user_arg[:2] == "--":
            arg = _user_arg.split("=")
            val = "=".join(arg[1:])
            arg = arg[0]

            if arg == _arg[0]:
                is_exists = True

                if _arg[3] and val == "":
                    print("Missing value for option:", _arg[0])
                    exit(0)

                if _arg[3]:
                    _arg[2](val)
                else:
                    _arg[2]()

                break
        elif _arg[1] and (_user_arg == _arg[1]):
            is_exists = True

            if _arg[3]:
                value_expected_arg = _arg
            else:
                _arg[2]()

            break

    if not is_exists:
        print("Invalid argument:", _user_arg)
        print("")
        argHandler_help()
        exit(0)

if value_expected_arg:
    print("Missing value for option:", value_expected_arg[0] + (", " + value_expected_arg[1]) if value_expected_arg[1] else "")
    exit(0)

if tmux_executable == "tmux" and not shutil.which("tmux"):
    print("\033[0;32;31m[Error] Tmux is not installed. Please install tmux on your system and run GDBFrontend again.\033[0m")
    exit(1)

print("GDBFrontend "+statics.VERSION_STRING)

try:
    if 0 in (config.HTTP_PORT, config.GOTTY_PORT, config.SERVER_PORT):
        import psutil
except ImportError:
    print("\033[0;32;31m[Error] The \"psutil\" module is not found. It is necessary for random ports (--port 0).\033[0m")
    print("You can install \"psutil\" module with the command: \033[0;32;40mpython3 -m pip install psutil\033[0m")

if is_random_port:
    import mmap
    import ctypes
    
    mmap_path = '/tmp/gdbfrontend-mmap-'+terminal_id
    arg_config["MMAP_PATH"] = mmap_path
    
    if os.path.exists(mmap_path):
        fd = os.open(mmap_path, os.O_RDWR)
        os.write(fd, b"\0" * mmap.PAGESIZE)
    else:
        fd = os.open(mmap_path, os.O_CREAT | os.O_TRUNC | os.O_RDWR)
        os.write(fd, b"\0" * mmap.PAGESIZE)

    mmapBuff = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)

try:
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    subprocess.Popen([tmux_executable, "kill-session", "-t", terminal_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
    
    if not is_random_port:
        os.system(
            tmux_executable +
            " -f tmux.conf new-session -s " + terminal_id +
            " -d '" + gdb_executable +
            " -ex \"python import sys, os; sys.path.insert(0, \\\""+path+"\\\"); import config, json, base64; config.init(); " +
            "config.setJSON(base64.b64decode(\\\""+base64.b64encode(json.dumps(arg_config).encode()).decode()+"\\\").decode()); import main\"; read;'"
        )
    else:
        os.system(
            tmux_executable +
            " -f tmux.conf new-session -d -s " + terminal_id
        )

    gotty = subprocess.Popen(
        ["./bin/gotty", "--config", "gotty.conf", "-a", config.BIND_ADDRESS, "-p", str(config.GOTTY_PORT), "-w", tmux_executable, "a", "-t", terminal_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE
    )

    if not is_random_port:
        print("Listening on %s: http://%s:%d/" % (config.BIND_ADDRESS, config.HOST_ADDRESS, config.HTTP_PORT))
        print(("Open this address in web browser: \033[0;32;40mhttp://%s:%d/terminal/\033[0m" % (config.HOST_ADDRESS, config.HTTP_PORT)))
        
        gotty.wait()
        subprocess.Popen([tmux_executable, "kill-session", "-t", terminal_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
    else:
        gottyProc = psutil.Process(gotty.pid)

        while gottyProc.connections().__len__() == 0: pass

        config.GOTTY_PORT = gottyProc.connections()[0].laddr.port
        arg_config["GOTTY_PORT"] = config.GOTTY_PORT

        os.system(
            tmux_executable +
            " -f tmux.conf send-keys -t " + terminal_id +
            " \"" +
            gdb_executable +
            " -ex \\\"python import sys, os; sys.path.insert(0, '"+path+"'); import config, json, base64; config.init(); " +
            "config.setJSON(base64.b64decode('"+base64.b64encode(json.dumps(arg_config).encode()).decode()+"').decode()); import main\\\"; read;"
            "\" "
        )
        os.system(
            tmux_executable +
            " -f tmux.conf send-keys -t " + terminal_id +
            " ENTER"
        )

        http_port = ctypes.c_uint16.from_buffer(mmapBuff, 0)
        server_port = ctypes.c_uint16.from_buffer(mmapBuff, 2)
        
        while not http_port.value or not server_port.value: pass

        config.HTTP_PORT = http_port.value
        config.SERVER_PORT = server_port.value

        print("Listening on %s: http://%s:%d/" % (config.BIND_ADDRESS, config.HOST_ADDRESS, config.HTTP_PORT))
        print(("Open this address in web browser: \033[0;32;40mhttp://%s:%d/terminal/\033[0m" % (config.HOST_ADDRESS, config.HTTP_PORT)))
        
        gotty.wait()
        gotty.kill()
        subprocess.Popen([tmux_executable, "kill-session", "-t", terminal_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
except KeyboardInterrupt as e:
    print("Keyboard interrupt.")
    
    gotty.kill()
    subprocess.Popen([tmux_executable, "kill-session", "-t", terminal_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()

if is_random_port:
    os.remove(mmap_path)

print("Stopped GDBFrontend.")