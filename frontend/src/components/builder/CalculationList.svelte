<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import CalculationListItem from "./CalculationListItem.svelte";
    import type { Calculation } from "src/schema";

    export let calculations: Calculation[];
    export let selectedIndex: number;

    $: ids = calculations.map((i) => i.id);

    const dispatch = createEventDispatcher();
    const indexFromId = (id: string): number | null => {
        let index = ids.indexOf(id);
        return index > -1 ? index : null;
    };
    const hoverItem = (event) => {
        dispatch("hoverItem", { index: indexFromId(event.detail.id) });
    };
    const clickItem = (event) => {
        dispatch("clickItem", { index: indexFromId(event.detail.id) });
    };
</script>

<div class="calculation-list">
    {#each calculations as { id, name, highlightedName, description }, i (id)}
        <CalculationListItem
            {id}
            name={highlightedName || name}
            {description}
            selected={i === selectedIndex}
            on:hoverItem={hoverItem}
            on:clickItem={clickItem}
        />
    {/each}
</div>

<style>
    .calculation-list {
        max-height: 30rem;
        z-index: 1000;
        overflow-y: scroll;
        position: absolute;
    }
</style>
