
import time
import os
import json
import sys
import logging
import argparse
from ast import literal_eval

from steps import discover, provision, verify, notify

def required_env(key) -> str:
    """
    Retrieves the key from the os.getenv() method. If
    the value is None, raises an Exception.
    """
    value = os.getenv(key)
    if value is None:
        raise Exception(f'{key} is a required environment variable. Cannot be None')
    
    return value


def execute_step(step_function, *args, **kwargs):
    try:
        step_function(*args, **kwargs)
    except Exception as e:

        state = {}

        if os.path.exists('/tmp/state.json'):
            with open('/tmp/state.json', 'r') as f:
                state = json.loads(f.read())

        state['error'] = f"""
OTAQ provisioning failed due to an exception.
exception: {e}
        """

        with open('/tmp/state.json', 'w') as f:
            f.write(json.dumps(state))

        raise e


formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s %(module)s %(processName)s - %(message)s', datefmt="%Y-%m-%dT%H:%M:%S%z")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--command', type=str, required=True, help='Command to run: discover, provision, verify')
    args = parser.parse_args()
    
    commands = ['discover', 'provision', 'verify', 'notify']

    if args.command not in commands:
        logger.error('Command must be one of: %s', ', '.join(commands))
        exit(1)

    resource = literal_eval(required_env('RESOURCE'))

    if args.command == 'discover':
        execute_step(discover.run, resource)
    
    elif args.command == 'provision':
        execute_step(provision.run, resource)

    elif args.command == 'verify':
        execute_step(verify.run, resource)

    elif args.command == 'notify':
        notify.run(resource)

    else:
        logger.error('Command must be one of: %s', ', '.join(commands))
        exit(1)

    exit(0)