import kopf


def mutate(spec, name, namespace, patch, **kwargs):
    kopf.label(
        objs=[patch],
        labels={
            'app.kubernetes.io/name': name,
            'app.kubernetes.io/instance': f"{namespace}.{name}",
            'app.kubernetes.io/version': f"{spec['workflow']['version']}",
            'app.kubernetes.io/component': 'otaq',
            'app.kubernetes.io/part-of': 'aquakube',
            'app.kubernetes.io/managed-by': 'otaq-operator'
        },
    )


def validate(body, spec, **kwargs):

    # enforcing namespace validation
    namespace = body.metadata.get('namespace')
    if namespace is None or namespace != "otaq":
        raise kopf.AdmissionError("otaqs must be created in the 'otaq' namespace")

    # enforcing provision strategy validation
    provision_strategy = spec['workflow']['provision_strategy']
    if provision_strategy == "resolve_mac_address":
        mac_address = spec['network'].get('mac_address')
        subnet = spec['network'].get('subnet')

        if mac_address is None or subnet is None:
            raise kopf.AdmissionError("Must set mac_address and subnet if using 'resolve_mac_address' strategy")

    elif provision_strategy == "dhcp_ip_address":
        dhcp_ip_address = spec['network'].get('dhcp_ip_address')
        
        if dhcp_ip_address is None:
            raise kopf.AdmissionError("Must set dhcp_ip_address if using 'dhcp_ip_address' strategy")

    # enforce network mode validation
    network_mode = spec['network']['mode']
    if network_mode == 'static':
        static_ip_address = spec['network'].get('static_ip_address')

        if static_ip_address is None:
            raise kopf.AdmissionError("Must set static_ip_address if using 'static' network mode")
    
    elif network_mode == 'dhcp':
        mac_address = spec['network'].get('mac_address')
        subnet = spec['network'].get('subnet')

        if mac_address is None or subnet is None:
            raise kopf.AdmissionError("Must set mac_address and subnet if using DHCP mode, this is so the operator can use resolve the IP address assigned automatically via DHCP")
