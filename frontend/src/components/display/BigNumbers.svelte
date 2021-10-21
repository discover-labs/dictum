<script lang="ts">
    import BigNumber from "./BigNumber.svelte";

    export let data: object[];
    export let formatters: object;
    export let meta: object;
    let values = [];

    $: if (data.length === 1) {
        const row = data[0];
        values = Object.keys(row).map((k) => ({
            name: meta[k].name,
            value: formatters[k](row[k]),
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
