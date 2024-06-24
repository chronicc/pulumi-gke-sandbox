from requests import get
import pulumi_kubernetes.helm.v3 as helm
import pulumi_kubernetes.yaml.v2 as yaml
import pulumi_kubernetes as k8s
import git
import os
import pathlib
import pulumi


class HelmRelease(pulumi.ComponentResource):
    _pulumiCrds: yaml.ConfigGroup
    _pulumiRelease: helm.Release

    def __init__(
        self,
        name: str,
        namespace: str,
        chart_name: str,
        chart_repo: str,
        chart_values: dict,
        chart_version: str,
        crd_base_url: str = "",
        crd_files: list[str] = [],
        crd_version: str = "",
        opts: pulumi.ResourceOptions = None,
    ) -> None:
        """Deploy a helm chart with optional CRDs.

        Args:
        - name (str): The unique name of the resource.
        - namespace (str): The namespace to deploy the helm chart into.
        - chart_name (str): The name of the helm chart to deploy.
        - chart_repo (str): The repository URL of the helm chart.
        - chart_values (dict: {}): A dictionary of values to pass to the helm chart
        - chart_version (str): The version of the helm chart to deploy.
        - crd_base_url (str: ""): The base URL where the CRDs can be downloaded.
        - crd_files (list: []): A list of CRD files to download.
        - crd_version (str: ""): The version of the CRDs to download.
        - opts (ResourceOptions, optional): A set of pulumi.ResourceOptions to use for
            this resource.

        Returns: None
        """
        super().__init__(
            f"chronicc:lib:{self.__class__.__name__}", name=name, opts=opts
        )
        self.name = name
        self.namespace = namespace
        self.chart_name = chart_name
        self.chart_repo = chart_repo
        self.chart_values = chart_values
        self.chart_version = chart_version
        self.crd_base_url = crd_base_url
        self.crd_files = crd_files
        self.crd_version = crd_version
        self.create_crds()
        self.create_release()

    def create_crds(self) -> None:
        if len(self.crd_files) > 0:
            repo_root = git.Repo(
                os.getcwd(), search_parent_directories=True
            ).working_tree_dir
            crd_dir = f"{repo_root}/.crds/{self.name}/{self.crd_version}"

            pathlib.Path(crd_dir).mkdir(parents=True, exist_ok=True)
            for file in self.crd_files:
                file_path = f"{crd_dir}/{file}"
                if not pathlib.Path(file_path).is_file():
                    with open(file_path, "w") as f:
                        f.write(get(f"{self.crd_base_url}{file}").text)

            crds = yaml.ConfigGroup(
                f"{self.name}-crds",
                files=[f"{crd_dir}/*.yaml"],
                opts=pulumi.ResourceOptions(parent=self),
            )
            self.export("customCrdsInstalled", "true")
        else:
            crds = yaml.ConfigGroup(
                f"{self.name}-no-crds",
                opts=pulumi.ResourceOptions(parent=self),
            )
            self.export("customCrdsInstalled", "false")
        self._pulumiCrds = crds

    def create_release(self) -> None:
        self._pulumiRelease = helm.Release(
            f"{self.name}-release",
            helm.ReleaseArgs(
                chart=self.chart_name,
                create_namespace=False,
                dependency_update=True,
                namespace=self.namespace,
                repository_opts=helm.RepositoryOptsArgs(repo=self.chart_repo),
                skip_crds=True,
                values=self.chart_values,
                version=self.chart_version,
            ),
            opts=pulumi.ResourceOptions(
                depends_on=[self._pulumiCrds],
                parent=self,
            ),
        )
        self.export(
            "appVersion", self._pulumiRelease.status.apply(lambda s: s.app_version)
        )
        self.export("id", self._pulumiRelease.id)
        self.export("revision", self._pulumiRelease.status.apply(lambda s: s.revision))
        self.export("status", self._pulumiRelease.status.apply(lambda s: s.status))
        self.export("version", self._pulumiRelease.status.apply(lambda s: s.version))

    def export(self, name: str, value: any) -> None:
        pulumi.export(f"{self.name}/{name}", value)
