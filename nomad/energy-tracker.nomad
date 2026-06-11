job "energy-tracker" {
  datacenters = ["home"]
  type        = "service"

  group "energy-tracker" {
    count = 1

    restart {
      attempts = 5
      interval = "5m"
      delay    = "10s"
      mode     = "delay"
    }

    task "octopus-agile" {
      driver = "docker"

      config {
        image = "ghcr.io/clythershackers/energy-tracker:latest"
        force_pull = true
        privileged = true
      }

      env {
        # Podman host access.
        CLICKHOUSE_HOST = "host.containers.internal"
        CLICKHOUSE_INTERFACE = "http"
        CLICKHOUSE_PORT = "8123"
        CLICKHOUSE_DB   = "default"
        OCTOPUS_CLICKHOUSE_CLUSTER = "muthra_cluster"

        # Set this to your active import tariff code, including region suffix.
        OCTOPUS_TARIFF_CODE = "E-1R-AGILE-FLEX-22-11-25-A"
        OCTOPUS_POLL_SECONDS = "1800"
        OCTOPUS_BACKFILL_SECONDS = "86400"
        OCTOPUS_LOOKAHEAD_SECONDS = "172800"
      }

      resources {
        cpu    = 100
        memory = 128
      }
    }
  }
}
