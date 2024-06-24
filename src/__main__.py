import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s

from lib import HelmRelease, K8sConfig, K8sApplication

# ---------------------------------------------------------------------------------------
#
#   Configuration
#
# ---------------------------------------------------------------------------------------
config = pulumi.Config()
gke = config.require_object("gke")
gke_master_version = gke.get("masterVersion")
gke_node_count = gke.get("nodeCount")
gke_node_machine_type = gke.get("nodeMachineType")
is_merge_kubeconfig = config.get_bool("mergeKubeconfig")


# ---------------------------------------------------------------------------------------
#
#   Kubernetes Cluster
#
# ---------------------------------------------------------------------------------------
gke_cluster = gcp.container.Cluster(
    "gke-cluster",
    deletion_protection=False,
    initial_node_count=1,
    node_config=gcp.container.ClusterNodeConfigArgs(
        disk_size_gb=10,
        disk_type="pd-standard",
        image_type="cos_containerd",
        machine_type="e2-micro",
        oauth_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        preemptible=False,
    ),
    location=gcp.config.zone,
    min_master_version=gke_master_version,
    opts=pulumi.ResourceOptions(
        # Prevent cluster from being replaced on every run
        # See https://github.com/pulumi/pulumi-gcp/issues/744
        ignore_changes=["nodeConfig"],
    ),
    remove_default_node_pool=True,
)

gke_nodepool_1 = gcp.container.NodePool(
    "gke-nodepool-1",
    cluster=gke_cluster.name,
    initial_node_count=gke_node_count,
    location=gcp.config.zone,
    node_config=gcp.container.NodePoolNodeConfigArgs(
        disk_size_gb=10,
        disk_type="pd-standard",
        image_type="cos_containerd",
        machine_type=gke_node_machine_type,
        oauth_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        preemptible=False,
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[gke_cluster],
        parent=gke_cluster,
    ),
)

k8s_config = K8sConfig(
    "k8s-config",
    cluster=gke_cluster,
    write_config=is_merge_kubeconfig,
)

# Make a Kubernetes provider instance that uses our cluster from above.
k8s_provider = k8s.Provider("k8s-provider", kubeconfig=k8s_config.kubeconfig)

# ---------------------------------------------------------------------------------------
#
#   Controllers
#
# ---------------------------------------------------------------------------------------
HelmRelease(
    "ingress-nginx",
    namespace="default",
    chart_name="ingress-nginx",
    chart_repo="https://kubernetes.github.io/ingress-nginx",
    chart_values={
        "controller": {
            "kind": "Deployment",
            "replicaCount": 3,
            "service": {
                "externalTrafficPolicy": "Local",
            },
        },
    },
    chart_version="4.10.1",
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
    ),
)

# ---------------------------------------------------------------------------------------
#
#   Applications
#
# ---------------------------------------------------------------------------------------
K8sApplication(
    "nginx",
    image_name="nginx",
    image_version="latest",
    ingress_annotations={
        "kubernetes.io/ingress.class": "nginx",
    },
    ingress_enabled=True,
    ingress_host="nginx.local",
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
    ),
)

# ---------------------------------------------------------------------------------------
#
#   Exports
#
# ---------------------------------------------------------------------------------------
pulumi.export("kubeconfig", k8s_config.kubeconfig)
pulumi.export("clusterName", gke_cluster.name)
pulumi.export("clusterEndpoint", gke_cluster.endpoint)
pulumi.export("masterAuth", gke_cluster.master_auth)
