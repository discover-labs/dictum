<script lang="ts">
    import MetricsSection from "../components/MetricsSection.svelte";
    import type { Metric } from "src/schema";
    import { Server } from "../graphql";

    const server = new Server();
    let metrics: Metric[] = [];
    const metricsRequest = `
    query {
        store {
            metrics {
                id
                name
                description
                format {
                    spec
                }
                dimensions {
                    id
                    name
                }
            }
        }
    }
    `;
    server
        .request(metricsRequest)
        .then((data) => (metrics = data.store.metrics));
</script>

<div>
    <MetricsSection name="Key Metrics" {metrics} />
</div>
