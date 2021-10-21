<script lang="ts">
    import MetricsSection from "../components/MetricsSection.svelte";
    import type { Calculation } from "src/schema";
    import { Server } from "../graphql";

    const server = new Server();
    let metrics: Calculation[] = [];
    const measuresRequest = `
    query {
        store {
            measures {
                id name description format { spec }
            }
        }
    }
    `;
    server
        .request(measuresRequest)
        .then((data) => (metrics = data.store.measures));
</script>

<div>
    <MetricsSection name="Key Metrics" {metrics} />
</div>
