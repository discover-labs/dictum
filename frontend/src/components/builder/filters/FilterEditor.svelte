<script lang="ts">
    import ValuesFilter from "./ValuesFilter.svelte";
    import type { FilterInfo, FilterState } from "./types";

    export let info: FilterInfo;
    export let state: FilterState;

    $: isBoth = info.values !== null && info.range !== null;
    let selectedType = info.values !== null ? "values" : "range";

    const selectValues = () => (selectedType = "values");
    const selectRange = () => (selectedType = "range");
</script>

<div>
    {#if isBoth}
        <button on:click={selectValues}>values</button>
        <button on:click={selectRange}>range</button>
    {/if}

    {#if selectedType === "values"}
        <ValuesFilter
            values={info.values}
            checked={state.values}
            on:toggle
            on:apply
            on:checkAll
            on:uncheckAll
        />
    {/if}
</div>

<style>
    div {
        position: absolute;
        border: 1px solid lightgray;
        background-color: white;
    }
</style>
