#!/usr/bin/python3

from __future__ import print_function
import argparse


DEFAULT_INTERVAL  = 1
# Initial watch success
SUCCESS = False

parser = argparse.ArgumentParser(description='Watch for command repeated execution result')
parser.add_argument('-c', '--command', '--cmd',  type=str,            help='Command to watch')
parser.add_argument('-i', '--interval',          type=float,  action='store',  dest='INTERVAL',  default=DEFAULT_INTERVAL,  help='Repeat interval in seconds')
parser.add_argument('-t', '--timeout',           type=float,  action='store',  dest='TIMEOUT',                              help='Timeout in seconds')
parser.add_argument('-n', '--count',             type=int,    action='store',  dest='COUNT',                                help='Retryes limit')
parser.add_argument('-l', '--flappings',         type=int,    action='store',  dest='FLAPPINGS',                            help='Flappings count')
parser.add_argument('-v', '--verbose',                        action='count',  help='Increase verbosity')
parser.add_argument('-x', '--success-command',   type=str,                     help='Execute after success')
parser.add_argument('-u', '--fail-command',      type=str,                     help='Execute after fail')
parser.add_argument('-a', '--change-command',    type=str,                     help='Execute after change')
parser.add_argument('-o', '--timeout-command',   type=str,                     help='Execute after timeout')
parser.add_argument('-w', '--overcount-command', type=str,                     help='Execute after reaching iterations limit')
parser.add_argument('-b', '--heartbeat-command', type=str,                     help='Execute on every iteration')
parser.add_argument('-p', '--progress',                       action='count',  help='Print status, repeat key for increase')

success_or_fail = parser.add_mutually_exclusive_group(required=False)
success_or_fail.add_argument('-s', '--success', '--true',   action='store_true', default=True,  help='Wait for success')
success_or_fail.add_argument('-f', '--fail',    '--false',  action='store_true', default=False, help='Wait for fail')
success_or_fail.add_argument('-g', '--change',              action='store_true', default=False, help='Wait for result change')
success_or_fail.add_argument('-m', '--monitor', '--mon',    action='store_true', default=False, help='Monitor result changes')

args = parser.parse_args()

def debug(message, level=0):
    if args.verbose:
        if level <= args.verbose:
            print(message)

# Check that command is provided, print help otherwise
if args.command:
    debug("Command: " + str(args.command), level=2)
else:
    parser.print_help()

# Select execution mode
if args.fail:
    mode = 'fail'
elif args.change:
    mode = 'change'
elif args.monitor:
    mode = 'monitor'
else:
    mode = 'success'

debug("Watch mode: " + mode, level=2)
debug("Flappings: " + str(args.FLAPPINGS), level=2)
if args.TIMEOUT:
    debug("Timeout is: " + str(args.TIMEOUT), level=2)
else:
    debug("Timeout is not set", level=2)

debug("Arguments: " + str(args), level=3)


SUBPROCESS = False
try:
    import subprocess
    SUBPROCESS = True
    debug("Using module: subprocess", level=3)
except ImportError:
    import os
    debug("Using module: os", level=3)


def rc_to_bool(rc):
    not_rc = not rc
    return not_rc


def print_subresult(not_rc):
    if args.progress:
        if not not_rc:
            if args.progress == 1:
                print('!', end='', flush=True)
            elif args.progress >= 2:
                print('return: fail', flush=True)
        else:
            if args.progress == 1:
                print('.', end='', flush=True)
            elif args.progress >= 2:
                print('return: success', flush=True)


def call_subprocess(command):
    proc = subprocess.Popen(
        [command],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    STDOUT = proc.stdout.read().decode()
    STDERR = proc.stderr.read().decode()
    RC     = proc.wait()
    return RC, STDOUT, STDERR


def exec_on_success_command():
    if args.success_command:
        debug("Executing on success command", level=3)
        return call_subprocess(args.success_command)


def exec_on_fail_command():
    if args.fail_command:
        debug("Executing on fail command", level=3)
        return call_subprocess(args.fail_command)


def exec_on_change_command():
    if args.change_command:
        debug("Executing on change command", level=3)
        return call_subprocess(args.change_command)


def exec_on_change_command():
    if args.change_command:
        debug("Executing on change command", level=3)
        return call_subprocess(args.change_command)


def exec_on_overcount_command():
    if args.overcount_command:
        debug("Executing on overcount command", level=3)
        return call_subprocess(args.overcount_command)


def exec_on_timeout_command():
    if args.timeout_command:
        debug("Executing on timeout command", level=3)
        return call_subprocess(args.timeout_command)


def exec_on_heartbeat_command():
    if args.heartbeat_command:
        debug("Executing on heartbeat command", level=3)
        return call_subprocess(args.heartbeat_command)


import time

START_TIME = time.time()

LOOP_CONDITION  = True
PREVIOUS_RC     = None
FLAPPINGS       = 0
TOTAL_FLAPPINGS = 0
ITERATION       = 0

try:
    if args.command:
        while LOOP_CONDITION:

            # Calculate current execution time
            CURRENT_TIME = time.time()
            TIME_SHIFT = CURRENT_TIME - START_TIME

            # Check iterations count exhaustion
            if args.COUNT:
                if ITERATION >= args.COUNT:
                    debug("\nMax iterations reached at {0} iteration at {1:0.3f} second".format(ITERATION, TIME_SHIFT), level=3)
                    exec_on_overcount_command()
                    break

            # Check timeout if it's set
            if args.TIMEOUT:
                if TIME_SHIFT > args.TIMEOUT:
                    debug("\nTimeout reached at {0:0.3f} second".format(TIME_SHIFT), level=3)
                    exec_on_timeout_command()
                    break

            # Execute heartbeat command if defined
            exec_on_heartbeat_command()

            if SUBPROCESS:
                # Use subprocess module
                RC, STDOUT, STDERR = call_subprocess(args.command)
            else:
                # Use os module
                RC = os.system(args.command)

            bool_rc = rc_to_bool(RC)
            if args.progress:
                print_subresult(bool_rc)

            if mode == 'success':
                if bool_rc:
                    SUCCESS = True
                    # Execute on success command if defined
                    exec_on_success_command()
                    break
            elif mode == 'fail':
                if not bool_rc:
                    SUCCESS = True
                    # Execute on fail command if defined
                    exec_on_fail_command()
                    break
            elif mode == 'change' or mode == 'monitor':
                if PREVIOUS_RC is not None:
                    bool_prc = rc_to_bool(PREVIOUS_RC)
                    # Compare previous return code and current
                    if bool_prc != bool_rc:
                        # Execute on change command if defined
                        exec_on_change_command()
                        # If current result is True
                        if bool_rc:
                            # Execute on success command if defined
                            exec_on_success_command()
                        else:
                            # Execute on fail command if defined
                            exec_on_fail_command()
                        # If flappings is set
                        if args.FLAPPINGS:
                            FLAPPINGS += 1
                            TOTAL_FLAPPINGS += 1
                            if FLAPPINGS >= args.FLAPPINGS:
                                debug("\n{0}: reached expected flappings: {1}".format(mode, args.FLAPPINGS), level=3)
                                FLAPPINGS = 0
                                if mode != 'monitor':
                                    SUCCESS = True
                                    break
                        # If mode is 'change' and flappings is not set, finish watching
                        else:
                            if mode != 'monitor':
                                SUCCESS = True
                                break

            # Set previous RC
            PREVIOUS_RC = RC
            # Increment iterations
            ITERATION += 1
            time.sleep(args.INTERVAL)
except KeyboardInterrupt:
    # Suppress output of KeyboardInterrupt exception
    pass
except Exception as e:
    print("Exception: " + e)
finally:
    # Break current line
    if args.verbose:
        print()
    return_code = not SUCCESS
    debug("Return code: {0}".format(int(return_code)), level=3)
    exit(return_code)



# TODO: Add variables substitution to event commands
