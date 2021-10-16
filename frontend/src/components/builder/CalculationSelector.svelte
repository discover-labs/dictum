<script lang="ts">
    import type { Calculation } from "src/schema";
    import type { Event } from "../types";
    import { createEventDispatcher } from "svelte";
    import CalculationDisplay from "./CalculationDisplay.svelte";
    import CalculationSearch from "./CalculationSearch.svelte";

    export let title: string;
    export let placeholder: string;
    export let availableCalculations: Calculation[];

    let calculations: Calculation[] = [];

    const dispatch = createEventDispatcher();
    const notify = () => {
        dispatch("updateCalculations", { calculations });
    };
    const addItem = (event: Event) => {
        calculations = [...calculations, event.detail.item];
        notify();
    };
    const removeItem = (event: Event) => {
        calculations = calculations.filter((i) => i.id !== event.detail.id);
        notify();
    };
</script>

<div class="calculation-selector">
    <span>{title}</span>
    {#each calculations as { id, name }, i (id)}
        <CalculationDisplay {id} {name} on:closeItemClick={removeItem} />
        {#if i < calculations.length - 1}, {/if}
    {/each}
    <CalculationSearch
        on:selectItem={addItem}
        {availableCalculations}
        {placeholder}
    />
</div>

<style>
    .calculation-selector {
        margin: 0.5em;
    }
</style>
