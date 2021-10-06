<script>
    import { createEventDispatcher } from "svelte";
    import CalculationListItem from "./CalculationListItem.svelte";

    export let calculations;
    export let selectedIndex;

    $: ids = calculations.map((i) => i.id);
    $: _calculations = calculations.map((i, ix) =>
        Object.assign({ selected: ix == selectedIndex }, i)
    );

    const dispatch = createEventDispatcher();
    const indexFromId = (id) => {
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
    {#each _calculations as { id, name, description, selected } (id)}
        <CalculationListItem
            {id}
            {name}
            {description}
            {selected}
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
