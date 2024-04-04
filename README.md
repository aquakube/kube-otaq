# KUBE-OTAQ

This repository manages the OTAQ cage asset.  These are cameras that are deployed in the pen that allow for remote monitoring of the fish.
OTAQ cameras capture large field of view and are therefore dewarped on the frontend for operators to monitor feeding.

The basic steps in the provisioning process are as follows:
* Plug the OTAQ camera into a DHCP network that your provisioning cluster has access too (Retrieve the IP address of the OTAQ camera or use the devices MAC address for discovery)
* Create an OTAQ resource in the Kubernetes cluster
* Check slack or google chat for the report of the provisioned OTAQ camera

## Operator

The OTAQ operator will deploy an argo workflow that manages the camera settings whenever an OTAQ custom resource is created or updated.

## Workflow

The argo workflow manages discovering the camera on the network either by MAC or IP address.
Once discovered the camera is provisioned and then verified.
The results of the workflow are then sent out via google chat and slack.
