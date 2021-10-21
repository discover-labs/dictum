<script lang="ts">
    import type { Dimension } from "src/schema";
    import type { Event } from "src/components/types";
    import CalculationSearch from "./CalculationSearch.svelte";

    import { createEventDispatcher } from "svelte";
    import FilterDisplay from "./filters/FilterDisplay.svelte";
    import type { Filter, FilterInfoResponse } from "./filters/types";
    import type { ValuesFilterToggleEvent } from "./filters/events";
    import { compileFilter } from "./compile";

    export let title: string;
    export let placeholder: string;
    export let availableDimensions: Dimension[];
    let filters: Filter[] = [];
    $: compiled = filters.map(compileFilter).filter((i) => i !== null);
    const dispatch = createEventDispatcher();
    $: dispatch("updateFilters", compiled);

    const addItem = (event: Event) => {
        addFilter(event.detail.item.id);
    };

    function createFilter(resp: FilterInfoResponse): Filter {
        return Object.assign(resp, {
            state: {
                range: resp.info.range,
                values: new Set(resp.info.values),
            },
            query: null,
        });
    }
    function addFilter(id: string) {
        fetch(`/api/filter/${id}`, { method: "GET" })
            .then((res) => res.json())
            .then((data: FilterInfoResponse) => {
                filters = [...filters, createFilter(data)];
            })
            .catch((err) => console.log(err));
    }
    function handleToggle(event: ValuesFilterToggleEvent) {
        filters = filters.map((f) => {
            const { id, label } = event.detail;
            if (f.dimension.id === id) {
                if (!f.state.values.delete(label)) {
                    f.state.values.add(label);
                }
            }
            f.query = { values: Array.from(f.state.values) };
            return f;
        });
    }
    function replaceFilterStateValues(
        filterId: string,
        clear: boolean = false
    ) {
        filters = filters.map((f) => {
            if (f.dimension.id === filterId) {
                if (clear) {
                    f.state.values = new Set();
                } else {
                    f.state.values = new Set(f.info.values);
                }
                f.query = { values: Array.from(f.state.values) };
            }
            return f;
        });
    }
    function handleCheckAll(event: { detail: { id: string } }) {
        replaceFilterStateValues(event.detail.id);
    }
    function handleUncheckAll(event: { detail: { id: string } }) {
        replaceFilterStateValues(event.detail.id, true);
    }
</script>

<div>
    <span>{title}</span>
    {#each filters as filter}
        <FilterDisplay
            {filter}
            on:toggle={handleToggle}
            on:checkAll={handleCheckAll}
            on:uncheckAll={handleUncheckAll}
        />
    {/each}
    <CalculationSearch
        availableCalculations={availableDimensions}
        {placeholder}
        on:selectItem={addItem}
    />
</div>
