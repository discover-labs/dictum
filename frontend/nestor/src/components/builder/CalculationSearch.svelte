<script>
    import { createEventDispatcher } from "svelte";
    import CalculationList from "./CalculationList.svelte";

    export let availableCalculations;
    export let placeholder;

    let value; // search input value
    let selectedIndex = 0; // highlighted item
    let focused = false; // if input is focused (show search)

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
        if (selection >= availableCalculations.length) {
            selectedIndex = 0;
        } else if (selection < 0) {
            selectedIndex = availableCalculations.length - 1;
        } else {
            selectedIndex = selection;
        }
    };
    const inputKeyDown = ({ key }) => {
        if (key == "ArrowDown") {
            selectItem(+1);
        } else if (key == "ArrowUp") {
            selectItem(-1);
        } else if (key == "Enter") {
            dispatch("selectItem", {
                item: availableCalculations[selectedIndex],
            });
        }
    };
    const clickItem = (event) => {
        dispatch("selectItem", {
            item: availableCalculations[event.detail.index],
        });
    };
</script>

<div>
    {#if availableCalculations.length > 0}
        <input
            bind:value
            {placeholder}
            on:focus={focus}
            on:blur={blur}
            on:keydown={inputKeyDown}
        />
    {/if}
    {#if focused}
        <CalculationList
            calculations={availableCalculations}
            {selectedIndex}
            on:hoverItem={hoverItem}
            on:clickItem={clickItem}
        />
    {/if}
</div>
