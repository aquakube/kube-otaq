import json
import time
import os
import logging

from dvrip import DVRIPCam

from command import fast_ping, run_command

logger = logging.getLogger(__name__)

def wait_for_device_reboot(ip_address):
    """
    Waits for the OTAQ device at the provided ip_address
    to respond to a ping before proceeding. If it fails after
    60 seconds, an exception will be thrown.
    """
    response = False
    start_time = time.time()

    while not response:
        response = fast_ping(ip_address)

        if time.time() - start_time > 60:
            raise Exception(f'OTAQ Device at ip address: {ip_address} did not respond to pings')


def check_video_encoding_settings(camera: DVRIPCam, resource: dict):
    """
    Checks if the video encoding settings were updated to reflect
    the spec.
    """
    logger.info("Checking video encoding settings")

    video_profile = camera.get_encode_info()
    video = resource['spec']['video']

    assert video_profile[0]['MainFormat']['Video']['FPS'] == video['framerate']
    assert video_profile[0]['MainFormat']['Video']['Quality'] == video['quality']
    assert video_profile[0]['MainFormat']['Video']['Resolution'] == video['resolution']
    assert video_profile[0]['MainFormat']['Video']['GOP'] == video['gop']
    assert video_profile[0]['MainFormat']['Video']['BitRateControl'] == video['bitrate_controller']
    assert video_profile[0]['MainFormat']['Video']['Compression'] == video['compression']


def check_hostname(camera: DVRIPCam, resource: dict):
    """
    Checks if the hostname was updated to reflect the spec.
    """
    logger.info("Checking host name")

    host_name = camera.get_info('NetWork.NetCommon.HostName')

    expected_hostname = resource['metadata']['name']

    assert host_name == expected_hostname


def get_sample_image(ip_address: str):
    """
    Gets a sample image from the OTAQ device at the provided ip_address
    """

    logger.info("Getting sample image from OTAQ device")

    pipeline = f"""
    ffmpeg \
        -y \
        -i \
        'rtsp://{ip_address}:554/user=admin&password=tlJwpbo6&channel=1&stream=0.sdp?real_stream' \
        -vframes 1 \
        /tmp/output.png
    """

    run_command(pipeline)

    if not os.path.exists('/tmp/output.png'):
        raise Exception(f"Could not create sample image from OTAQ device at IP address: {ip_address}")


    # take snapshot
    # image = await camera.snapshot()

    # if len(image) <= 1000:
    #     raise Exception("Snapshot failed to be taken")

    # # save it
    # with open("snap.jpeg", "wb") as fp:
    #   fp.write(image)


def run(resource: dict):
    
    state = {}
    with open('/tmp/state.json', 'r') as f:
        state = json.load(f)

    wait_for_device_reboot(state['ip_address'])

    camera = DVRIPCam(
        ip=state['ip_address'],
        user='admin',
        password=''
    )

    if not camera.login():
        raise Exception(f"Could not login to OTAQ device at IP address: {state['ip_address']}")

    check_video_encoding_settings(camera, resource)

    check_hostname(camera, resource)

    # TODO: figure out connection refused issue and get auth setup for notify
    # get_sample_image(state['ip_address'])

    camera.close()