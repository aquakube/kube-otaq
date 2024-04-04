import os
import kopf

from handlers import create, update, admission
from utilities.tunnel import ServiceTunnel


@kopf.on.startup()
def startup(logger, settings, **kwargs):
    """
    Execute this handler when the operator starts.
    No call to the API server is made until this handler
    completes successfully.
    """

    settings.execution.max_workers = 5
    settings.networking.request_timeout = 30
    settings.networking.connect_timeout = 10
    settings.persistence.finalizer = 'otaqs.aquakube.io/finalizer'
    settings.persistence.progress_storage = kopf.AnnotationsProgressStorage(prefix='otaqs.aquakube.io')
    settings.persistence.diffbase_storage = kopf.AnnotationsDiffBaseStorage(prefix='otaqs.aquakube.io')
    settings.admission.managed = 'otaqs.aquakube.io'

    # default to using a tunnel to the service. This will start ngrok.
    # You need to have kopf[dev] installed for this to work.
    if os.environ.get("ENVIRONMENT", "dev") == "dev":
        settings.admission.server = kopf.WebhookAutoTunnel()

    # if we are in production, use a service tunnel. This will use the self-signed
    # cert that is created by the operator.
    else:
        settings.admission.server = ServiceTunnel(
            namespace=os.getenv("NAMESPACE", "otaq"),
            service_name=os.getenv("SERVICE_NAME"),
            service_port=int(os.getenv("SERVICE_PORT", 443)),
            container_port=int(os.getenv("CONTAINER_PORT", 9443))
        )


@kopf.on.cleanup()
def cleanup(logger, **kwargs):
    logger.info("im shutting down. Goodbye!")


@kopf.on.validate('otaq')
def validateotaq(**kwargs):
    admission.validate(**kwargs)
    

@kopf.on.mutate("otaq")
def mutateotaq(**kwargs):
    admission.mutate(**kwargs)


@kopf.on.create('otaq')
@kopf.on.update('otaq')
def on_create(body, name, namespace, logger, patch, **kwargs):
    """
    For each otaq, create a workflow to provision the otaq.
    It's phase will be set to provisioning.
    """
    create.workflow(name, namespace, body, logger, patch)


@kopf.on.field(
    'workflow',
    field='status.phase',
    labels={'otaqs.aquakube.io/name': kopf.PRESENT},
)
def on_update_workflow(old, new, body, logger, **kwargs):
    """
    When the workflow is done, update the otaq status depending
    on the status of the argo workflow
    """
    otaq_name = body['metadata']['labels']['otaqs.aquakube.io/name']

    # when the workflow was running and is now succeeded
    if old == 'Running' and new == 'Succeeded':
        update.status(
            name=otaq_name,
            status={ 'phase': 'provisioned' },
            logger=logger
        )
    
    # when the workflow was running and is now failed
    elif old == 'Running' and new == 'Failed':
        update.status(
            name=otaq_name,
            status={ 'phase': 'failed_provisioning' },
            logger=logger
        )
