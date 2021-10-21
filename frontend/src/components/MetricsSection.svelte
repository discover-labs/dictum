<script lang="ts">
    import type { Calculation } from "src/schema";
    import MetricCard from "./MetricCard.svelte";

    export let name: string;
    export let metrics: Calculation[];
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

        .wrapper {
            padding: 10pt 10pt 10pt 0;
        }
    }
</style>
