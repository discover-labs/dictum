<script lang="ts">
    import type { Metric } from "src/schema";
    import MetricCard from "./MetricCard.svelte";

    export let name: string;
    export let metrics: Metric[];
</script>

<div class="metrics-section">
    <h1>{name}</h1>
    <div class="body">
        {#each metrics as metric}
            <div class="wrapper">
                <MetricCard {metric} />
            </div>
        {/each}
    </div>
</div>

<style lang="scss">
    h1 {
        font-size: 18pt;
        font-weight: 300;
        margin: 1em 0 0.5em 0;
    }
    .body {
        display: flex;
        flex-direction: row;
        overflow-x: scroll;
        flex-wrap: wrap;

        .wrapper {
            padding: 0 10pt 10pt 2px;
        }
    }
</style>
