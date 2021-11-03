<script lang="ts">
    import BigNumber from "./BigNumber.svelte";

    export let data: object;
    export let meta: { id: string; name: string }[];

    $: values = meta.map(({ id, name }) => ({ name, value: data[id] }));
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
