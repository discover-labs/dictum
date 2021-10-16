<script lang="ts">
    import type { Filter } from "./types";
    import type { CheckboxToggleEvent } from "./events";
    import FilterEditor from "./FilterEditor.svelte";
    import { createEventDispatcher } from "svelte";

    export let filter: Filter;

    let editing = true;
    const edit = () => (editing = !editing);

    const dispatch = createEventDispatcher();
    const handleToggle = (event: CheckboxToggleEvent) => {
        dispatch("toggle", {
            label: event.detail.label,
            id: filter.dimension.id,
        });
    };
    const handleCheckAll = () => {
        dispatch("checkAll", { id: filter.dimension.id });
    };
    const handleUncheckAll = () => {
        dispatch("uncheckAll", { id: filter.dimension.id });
    };
</script>

<div class="filter">
    <mark>{filter.dimension.name}</mark>
    <button on:click={edit}>✍️</button>
    {#if filter.info !== null && editing}
        <FilterEditor
            info={filter.info}
            state={filter.state}
            on:apply
            on:toggle={handleToggle}
            on:checkAll={handleCheckAll}
            on:uncheckAll={handleUncheckAll}
        />
    {/if}
</div>

<style>
    .filter {
        display: inline-block;
        margin-left: 0.5rem;
    }
</style>
