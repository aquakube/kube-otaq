import logging
import json
import logging
import os
import xml.etree.ElementTree as ET

from dvrip import DVRIPCam

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


def confirm_firmware_version(camera: DVRIPCam, resource: dict):
    """
    Checks the firmware the OTAQ camera is running to determine if it is supported or not.
    Unsupported firmware versions will cause the provisioning process to fail,
    The user can set force_provision to true on the CR to override this behavior.
    denied firmware versions cause some major issue with integration like not supporting RTSP via UDP.
    """

    force_provision = resource['spec']['workflow']['force_provision']

    firmware_allow_list = os.getenv("FIRMWARE_ALLOW_LIST", "")
    firmware_deny_list = os.getenv("FIRMWARE_DENY_LIST", "")
    firmware_allow_list = [v.strip() for v in firmware_allow_list.strip().split(',')]
    firmware_deny_list = [v.strip() for v in firmware_deny_list.strip().split(',')]
    
    system_info = camera.get_system_info()
    if system_info['SoftWareVersion'] in firmware_allow_list:
        logger.info(f"Detected support firmware version: {system_info['SoftWareVersion']}")

    elif system_info['SoftWareVersion'] in firmware_deny_list:
        logger.info(f"Detected unsupported firmware version: {system_info['SoftWareVersion']}")
        if force_provision:
            logger.warning(f"""
                Detected unsupported firmware version: {system_info['SoftWareVersion']}.
                Continuing to provision because force_provision was set.
            """)
        else:
            raise Exception(f"Detected unsupported firmware version: {system_info['SoftWareVersion']}")

    else:
        logger.warning(f"Detected unknown firmware version: {system_info['SoftWareVersion']}")

        if force_provision:
            logger.warning(f"""
                Detected unknown firmware version: {system_info['SoftWareVersion']}.
                Continuing to provision because force_provision was set.
            """)
        else:
            raise Exception(f"Detected unknown firmware version: {system_info['SoftWareVersion']}")


def discover_otaq(resource: dict, state: dict):
    workflow = resource['spec']['workflow']
    network = resource['spec']['network']

    if workflow['provision_strategy'] == 'resolve_mac_address':
        logger.info("Resolving MAC address to IP address")
        ip_address = resolve_ip_address(network['mac_address'], network['subnet'])

        if ip_address is None:
            raise Exception(f"Could not resolve MAC address: {network['mac_address']} to IP address on subnet: {network['subnet']}")
        
        logger.info(f"Resolved MAC address: {network['mac_address']} to IP address: {ip_address}")
        state['ip_address'] = ip_address

    elif workflow['provision_strategy'] == 'dhcp_ip_address':
        logger.info(f"Using DHCP IP: {network['dhcp_ip_address']} to provision device")
        state['ip_address'] = network['dhcp_ip_address']


def run(resource: dict):
    """
    Attempts to discover the OTAQ device via MAC adress or via a provided IP address.
    """

    state = {}
    discover_otaq(resource, state)
    
    logger.info(f"Attempting to connect to OTAQ device at IP address: {state['ip_address']}")
    camera = DVRIPCam(
        ip=state['ip_address'],
        user='admin',
        password=''
    )

    if not camera.login():
        raise Exception(f"Could not login to OTAQ device at IP address: {state['ip_address']}")

    confirm_firmware_version(camera, resource)

    logger.info(f"Connected to OTAQ device at IP address: {state['ip_address']}")
    logger.info("OTAQ device was discovered successfully")

    with open('/tmp/state.json', 'w') as f:
        json.dump(state, f)