<script>
    import BigNumber from "./BigNumber.svelte";
    import { getFormatters } from "../format";

    export let queryResult;
    let values = [];

    $: formatters = getFormatters(queryResult.metadata);

    $: if (queryResult.data.length === 1) {
        const data = queryResult.data[0];
        const meta = queryResult.metadata.columns;
        values = Object.keys(data).map((k) => ({
            name: meta[k].name,
            value: formatters[k](data[k]),
        }));
    }
</script>

<div class="big-numbers">
    {#each values as { name, value }}
        <BigNumber {name} {value} />
    {/each}
</div>

<style>
    .big-numbers {
        display: flex;
        flex-direction: row;
        justify-content: center;
    }
</style>
