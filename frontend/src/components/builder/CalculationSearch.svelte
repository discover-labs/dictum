<script>
    import { createEventDispatcher } from "svelte";
    import CalculationList from "./CalculationList.svelte";
    import Fuse from "fuse.js";

    export let availableCalculations;
    export let placeholder;

    let query = ""; // search input value
    let selectedIndex = 0; // highlighted item
    let focused = false; // if input is focused (show search)

    // fuzzy search
    let fuse = new Fuse(availableCalculations, {
        keys: ["name"],
        includeMatches: true,
    });
    $: fuse.setCollection(availableCalculations);
    $: searchResults = fuse.search(query);
    $: calculations =
        query.length > 0
            ? searchResults.map(searchResultsToCalculations)
            : availableCalculations;

    const searchResultsToCalculations = (i) => {
        let name = i.item.name;
        i.matches[0].indices.reverse().forEach(([s, e]) => {
            name =
                name.slice(0, s) +
                "<u>" +
                name.slice(s, e + 1) +
                "</u>" +
                name.slice(e + 1);
        });
        return Object.assign({ highlightedName: name }, i.item);
    };

    const dispatch = createEventDispatcher();
    const focus = () => (focused = true);
    // timeout so that the click on an item in search list has time to be processed
    // before it's hidden due to blur
    const blur = () => setTimeout(() => (focused = false), 10);
    const hoverItem = (event) => {
        selectedIndex = event.detail.index;
    };
    const selectItem = (n) => {
        // +1 for next -1 for previous. loops around
        let selection = selectedIndex + n;
        if (selection >= calculations.length) {
            selectedIndex = 0;
        } else if (selection < 0) {
            selectedIndex = calculations.length - 1;
        } else {
            selectedIndex = selection;
        }
    };
    const inputKeyDown = ({ key, target }) => {
        if (key == "ArrowDown") {
            selectItem(+1);
        } else if (key == "ArrowUp") {
            selectItem(-1);
        } else if (key == "Enter") {
            dispatchSelectItem(calculations[selectedIndex], target);
        } else if (key == "Escape") {
            target.blur();
        }
    };
    const clickItem = (event) => {
        dispatchSelectItem(calculations[event.detail.index], event.target);
    };
    const dispatchSelectItem = (item, target) => {
        dispatch("selectItem", { item });
        query = "";
        if (target !== null) {
            target.blur();
        }
    };
</script>

<div>
    {#if availableCalculations.length > 0}
        <input
            bind:value={query}
            {placeholder}
            on:focus={focus}
            on:blur={blur}
            on:keydown={inputKeyDown}
        />
    {/if}
    {#if focused}
        <CalculationList
            {calculations}
            {selectedIndex}
            on:hoverItem={hoverItem}
            on:clickItem={clickItem}
        />
    {/if}
</div>

<style>
    div,
    input {
        display: inline-block;
    }
</style>
