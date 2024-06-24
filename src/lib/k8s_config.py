from textwrap import dedent
import os
import pulumi
import pulumi_gcp as gcp
import yaml


class K8sConfig(pulumi.ComponentResource):

    def __init__(
        self,
        resource_name: str,
        cluster: gcp.container.cluster,
        config_path: str = "~/.kube/config",
        opts: pulumi.ResourceOptions = None,
        write_config: bool = False,
    ) -> None:
        """Creating a Kubernetes cluster config.

        :param: str resource_name: The unique name of the resource.
        :param: gcp.container.cluster cluster: The Kubernetes cluster to create the
            config for.
        :param: str config_path: The path to write the kubeconfig to.
        :param: ResourceOptions opts: A set of pulumi.ResourceOptions to use for
            this resource.
        :param: bool write_config: Whether to write the kubeconfig to the file specified
            with `config_path`.

        Returns: None
        """
        super().__init__(
            f"chronicc:lib:{self.__class__.__name__}",
            name=resource_name,
            opts=opts,
        )

        cluster_info = pulumi.Output.all(
            cluster.endpoint,
            cluster.master_auth,
            cluster.name,
        )

        self.config_path = config_path
        self.kubeconfig = self.generate_kubeconfig(cluster_info)

        if write_config:
            self.kubeconfig.apply(self._write_file)

    def generate_kubeconfig(self, cluster_info) -> pulumi.Output[str]:
        """Generate the kubeconfig for the Kubernetes cluster."""

        return cluster_info.apply(
            lambda info: dedent(
                """\
                apiVersion: v1
                kind: Config
                current-context: {name}
                clusters:
                - cluster:
                    certificate-authority-data: {ca}
                    server: https://{url}
                  name: {name}
                contexts:
                - context:
                    cluster: {name}
                    user: {name}
                  name: {name}
                users:
                - name: {name}
                  user:
                    exec:
                      apiVersion: client.authentication.k8s.io/v1beta1
                      command: gke-gcloud-auth-plugin
                      interactiveMode: IfAvailable
                      provideClusterInfo: true
                """
            ).format(
                url=info[0],
                ca=info[1]["cluster_ca_certificate"],
                name=info[2],
            )
        )

    def _write_file(self, v: str) -> None:
        target_path = os.path.expanduser(self.config_path)
        try:
            data1 = yaml.safe_load(open(target_path))
        except FileNotFoundError:
            data1 = {}
        if data1 is None:
            data1 = {}
        with open(target_path, "w") as fp:
            data2 = yaml.safe_load(v)
            data1.update(data2)
            yaml.dump(data1, fp)
