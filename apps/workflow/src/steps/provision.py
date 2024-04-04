import json
import time
import logging
import xml.etree.ElementTree as ET

from dvrip import DVRIPCam
from DeviceManager import SetIP

from command import run_command

logger = logging.getLogger(__name__)


def resolve_ip_address(mac_address: str, subnet: str):
    """
    Resolves the MAC address to an IP address using nmap. The subnet used
    will be scanned for all devices on the network. This function must be run
    as root and on the same direct layer 2 network as the device you are
    trying to resolve.
    """

    nmap_discover_command = f"sudo nmap --host-timeout 30 --max-retries 0 -sP -n -oX - {subnet}"
    output = run_command(nmap_discover_command)
    logger.debug(f"Nmap discover output: {output}")
    output = ET.fromstring(output)

    for host in output.findall('host'):
        addresses = [a for a in host.findall('address')]
        mac = [a for a in addresses if a.get('addrtype') == 'mac']
        ip = [a for a in addresses if a.get('addrtype') == 'ipv4']
        if mac and ip:
            mac = mac[0].get('addr').lower()
            ip = ip[0].get('addr').lower()

            if mac == mac_address:
                return ip


def update_network_settings(camera: DVRIPCam, resource: dict, state: dict):
    """
    Updates the network settings to reflect the spec.
    """
    hostname = resource['metadata']['name']

    logger.info(f"Updating hostname to {hostname}")
    camera.set_info('NetWork.NetCommon.HostName', hostname)

    network_mode = resource['spec']['network']['mode']
    if network_mode == 'static':
        static_ip_address = resource['spec']['network']['static_ip_address']
        logger.info(f"Updating static ip address to {static_ip_address}")
        camera.set_info('NetWork.NetCommon.HostIP', SetIP(static_ip_address))

        # update the static ip address because the camera will now be
        # responding on this ip since it was just assigned.
        state['ip_address'] = static_ip_address

    elif network_mode == 'dhcp':
        logger.info("Updating camera to use use DHCP")
        dhcp = camera.get_info("NetWork.NetDHCP")
        dhcp[0]['Enable'] = True
        camera.set_info("NetWork.NetDHCP", dhcp)
        # After setting the camera to use DHCP, it will reboot to be allocated an IP address
        camera.reboot()
        time.sleep(60)
        network = resource['spec']['network']
        logger.info("Resolving MAC address to IP address")
        ip_address = resolve_ip_address(network['mac_address'], network['subnet'])
        if ip_address is None:
            raise Exception(f"Could not resolve the newly provisioned DHCP address via the provided MAC address: {network['mac_address']} on subnet: {network['subnet']}")
        else:
            logger.info(f"Resolved IP address to {ip_address}")
            state['ip_address'] = ip_address


def update_video_settings(camera: DVRIPCam, resource: dict):
    """
    Updates the video encoding settings to reflect the spec.
    """

    logger.info("Updating video encoding settings")

    video_profile = camera.get_encode_info()

    video = resource['spec']['video']

    # configure the framerate
    video_profile[0]['MainFormat']['Video']['FPS'] = video['framerate']

    # configure the encoder quality
    # image quality only applied in variable streams (vbr)
    # the valid values is 1-6, the larger the value, the better the image quality
    video_profile[0]['MainFormat']['Video']['Quality'] = video['quality']

    # configure the resolution
    video_profile[0]['MainFormat']['Video']['Resolution'] = video['resolution']

    # configure the i-frame interval
    video_profile[0]['MainFormat']['Video']['GOP'] = video['gop']

    # configure the bitrate controller
    video_profile[0]['MainFormat']['Video']['BitRateControl'] = video['bitrate_controller']

    # configure the video compression
    video_profile[0]['MainFormat']['Video']['Compression'] = video['compression']

    # set the video profile
    camera.set_info("Simplify.Encode", video_profile)


def run(resource: dict):
    
    state = {}
    with open('/tmp/state.json', 'r') as f:
        state = json.load(f)

    camera = DVRIPCam(
        ip=state['ip_address'],
        user='admin',
        password=''
    )

    if not camera.login():
        raise Exception(f"Could not login to OTAQ device at IP address: {state['ip_address']}")

    update_video_settings(camera, resource)

    update_network_settings(camera, resource, state)

    camera.reboot()

    camera.close()

    logger.info("OTAQ device was provisioned successfully")

    with open('/tmp/state.json', 'w') as f:
        json.dump(state, f)