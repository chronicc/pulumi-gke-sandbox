from pulumi_docker import RemoteImage
from pulumi_kubernetes.apps.v1 import (
    Deployment,
    DeploymentSpecArgs,
)
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    ContainerPortArgs,
    Namespace,
    PodSpecArgs,
    PodTemplateSpecArgs,
    Service,
    ServicePortArgs,
    ServiceSpecArgs,
)
from pulumi_kubernetes.networking.v1 import (
    HTTPIngressPathArgs,
    HTTPIngressRuleValueArgs,
    Ingress,
    IngressBackendArgs,
    IngressRuleArgs,
    IngressServiceBackendArgs,
    IngressSpecArgs,
    ServiceBackendPortArgs,
)
from pulumi_kubernetes.meta.v1 import (
    LabelSelectorArgs,
    ObjectMetaArgs,
)
import pulumi


class K8sApplication(pulumi.ComponentResource):
    _pulumiDeployment: Deployment
    _pulumiService: Service
    _pulumiIngress: Ingress

    def __init__(
        self,
        name: str,
        image_name: str,
        image_version: str,
        ingress_host: str,
        ingress_annotations: dict = {},
        ingress_enabled: bool = False,
        ingress_path_type: str = "Prefix",
        ingress_path: str = "/",
        namespace: str = "default",
        opts: pulumi.ResourceOptions = None,
        replicas: int = 1,
        service_source_port: int = 80,
        service_target_port: int = 80,
    ) -> None:
        """Create a new Kubernetes deployment.

        Args:
        - image_name (str): The name of the container image to use.
        - image_version (str): The version of the container image to use.
        - ingress_annotations (dict: {}): A dictionary of annotations to apply to the ingress.
        - ingress_enabled (bool: False): True if an ingress should be created for the deployment.
        - ingress_host (str): The hostname for the ingress. Mandatory when ingress is enabled.
        - ingress_path_type (str: "Prefix"): The path type for the ingress.
        - ingress_path (str: "/"): The path for the ingress. Defaults to "/".
        - service_source_port (int: 80): The source port for the service which is
            pointing to the internet.
        - service_target_port (int: 80): The target port for the service which is
            exposed by the container.

        Returns: None
        """
        super().__init__(
            f"chronicc:lib:{self.__class__.__name__}", name=name, opts=opts
        )
        self.image_name = image_name
        self.image_version = image_version
        self.ingress_annotations = ingress_annotations
        self.ingress_enabled = ingress_enabled
        self.ingress_host = ingress_host
        self.ingress_path = ingress_path
        self.ingress_path_type = ingress_path_type
        self.name = name
        self.namespace = namespace
        self.replicas = replicas
        self.service_source_port = service_source_port
        self.service_target_port = service_target_port

        self.create_deployment()
        self.create_service()
        if self.ingress_enabled:
            self.create_ingress()

    def create_deployment(self) -> None:
        image = RemoteImage(
            f"{self.name}-image",
            name=f"{self.image_name}:{self.image_version}",
            opts=pulumi.ResourceOptions(parent=self),
        )
        self._pulumiDeployment = Deployment(
            f"{self.name}-deployment",
            metadata=ObjectMetaArgs(
                labels={"app": self.name},
                name=self.name,
                namespace=self.namespace,
            ),
            opts=pulumi.ResourceOptions(parent=self),
            spec=DeploymentSpecArgs(
                replicas=self.replicas,
                selector=LabelSelectorArgs(match_labels={"app": self.name}),
                template=PodTemplateSpecArgs(
                    metadata=ObjectMetaArgs(labels={"app": self.name}),
                    spec=PodSpecArgs(
                        containers=[
                            ContainerArgs(
                                name=self.name,
                                image=image.repo_digest,
                                ports=[
                                    ContainerPortArgs(
                                        container_port=self.service_target_port,
                                    ),
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )
        self.export("imageName", self.image_name)
        self.export("imageVersion", self.image_version)

    def create_ingress(self) -> None:
        self._pulumiIngress = Ingress(
            f"{self.name}-ingress",
            metadata=ObjectMetaArgs(
                annotations=self.ingress_annotations,
                name=self.name,
                namespace=self.namespace,
            ),
            opts=pulumi.ResourceOptions(parent=self),
            spec=IngressSpecArgs(
                rules=[
                    IngressRuleArgs(
                        host=self.ingress_host,
                        http=HTTPIngressRuleValueArgs(
                            paths=[
                                HTTPIngressPathArgs(
                                    backend=IngressBackendArgs(
                                        service=IngressServiceBackendArgs(
                                            name=self.name,
                                            port=ServiceBackendPortArgs(
                                                number=self.service_source_port,
                                            ),
                                        ),
                                    ),
                                    path=self.ingress_path,
                                    path_type=self.ingress_path_type,
                                )
                            ],
                        ),
                    )
                ],
            ),
        )
        self.export(
            "ingressHost", self._pulumiIngress.spec.apply(lambda s: s.rules[0].host)
        )
        self.export(
            "loadBalancerIp",
            self._pulumiIngress.status.apply(lambda s: s.load_balancer.ingress[0].ip),
        )

    def create_service(self) -> Service:
        self._pulumiService = Service(
            f"{self.name}-service",
            metadata=ObjectMetaArgs(
                labels={"app": self.name},
                name=self.name,
                namespace=self.namespace,
            ),
            opts=pulumi.ResourceOptions(parent=self),
            spec=ServiceSpecArgs(
                ports=[
                    ServicePortArgs(
                        port=80,
                        protocol="TCP",
                        target_port=self.service_target_port,
                    ),
                ],
                selector={
                    "app": self.name,
                },
            ),
        )
        self.export("serviceIp", self._pulumiService.spec.apply(lambda s: s.cluster_ip))
        self.export(
            "servicePorts",
            self._pulumiService.spec.apply(lambda s: s.ports).apply(
                lambda p: [v["port"] for v in p]
            ),
        )

    def export(self, name: str, value: any) -> None:
        pulumi.export(f"{self.name}/{name}", value)
