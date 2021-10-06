<script>
    import BigNumber from "./BigNumber.svelte";

    export let queryResult;
    let values = [];

    $: if (queryResult.data.length === 1) {
        let data = queryResult.data[0];
        let meta = queryResult.metadata.columns;
        values = Object.keys(data).map((k) => ({
            name: meta[k],
            value: data[k],
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
