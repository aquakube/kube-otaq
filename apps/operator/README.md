# OTAQ Operator

This operator will react to OTAQ Custom Resources defined in the cluster.
On CRUD events the operator will respectivelly provsion or configure the OTAQ device.


## Run

```
kopf run --namespace otaq apps/operator/src/main.py
```