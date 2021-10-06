<script>
    import { createEventDispatcher } from "svelte";
    import CalculationDisplay from "./CalculationDisplay.svelte";
    import CalculationSearch from "./CalculationSearch.svelte";

    export let title;
    export let placeholder;
    export let availableCalculations;
    export let calculations;

    const dispatch = createEventDispatcher();
    const addItem = (event) => {
        dispatch("addCalculation", event.detail);
    };
    const removeItem = (event) => {
        dispatch("removeCalculation", event.detail);
    };
</script>

<div>
    <span>{title}</span>
    {#each calculations as { id, name, type }, i (id)}
        <CalculationDisplay {id} {name} {type} on:closeItemClick={removeItem} />
        {#if i < calculations.length - 1}, {/if}
    {/each}
    <CalculationSearch
        on:selectItem={addItem}
        {availableCalculations}
        {placeholder}
    />
</div>

<style>
</style>
