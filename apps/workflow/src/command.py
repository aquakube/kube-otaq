import subprocess
import logging
import os

logger = logging.getLogger(__name__)

def fast_ping(host):
    '''
    Floods the host with ping messages
    concurrently that will timeout quickly.
    Useful for quickly checking if device is up,
    routable, and network is in optimal state.

    Linux Docs: https://linux.die.net/man/8/ping
    -f => flood the pings. Cocurrent
    -n => numeric output only
    -W => Wait time in seconds for each ping
    -w => absolute timeout in seconds
    -c => how many pings to send

    returns:
        bool => true if status code of 0, false otherwise
        None => if exception occurs
    '''
    try:
        command = ['ping', '-n', '-f', '-W 3', '-w 5', '-c 5', host]
        status_code = subprocess.call(command, stdout=open(os.devnull, 'wb'))
        return status_code == 0
    except:
        logger.exception('Failed to execute fast ping')

    return None


def run_command(command: str, timeout=60) -> str:
    logger.info(f"Running shell command: {command}")

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()
    stderr = stderr.decode("utf-8")
    stdout = stdout.decode("utf-8")
    exit_code = process.wait(timeout=timeout)

    logger.debug(f"Command exited with code: {exit_code}")
    logger.debug(f"Command stdout: {stdout}")

    if stderr:
        raise Exception(stderr)

    return stdout