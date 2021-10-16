<script lang="ts">
    import CheckboxList from "./CheckboxList.svelte";
    import type { FilterValue } from "./types";
    import { createEventDispatcher } from "svelte";

    export let values: FilterValue[];
    export let checked: Set<FilterValue>;

    const dispatch = createEventDispatcher();
    const apply = () => {
        dispatch("apply");
    };
</script>

<div class="values-filter">
    <div class="checkbox-list">
        <CheckboxList
            options={values}
            {checked}
            on:toggle
            on:checkAll
            on:uncheckAll
        />
    </div>
    <div class="filter-apply">
        <button on:click={apply}>Apply</button>
    </div>
</div>

<style>
    .values-filter {
        max-height: 50vh;
        display: flex;
        flex-direction: column;
    }
    .checkbox-list {
        overflow-y: scroll;
    }
    .filter-apply {
        padding: 0.5em;
    }
</style>
