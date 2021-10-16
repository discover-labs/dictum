<script lang="ts">
    import CalculationSelector from "./builder/CalculationSelector.svelte";
    import FilterSelector from "./builder/FilterSelector.svelte";
    import QueryResultDisplay from "./display/QueryResultDisplay.svelte";
    import type {
        Query,
        Measure,
        Dimension,
        QueryResult,
        Store,
    } from "../schema";
    import type { Event } from "./types";

    let store: Store = {
        measures: [],
        dimensions: [],
    };
    let measures: Measure[] = [];
    let dimensions: Dimension[] = [];
    let queryResult: QueryResult | null = null;

    $: query = {
        measures: measures.map((i) => i.id),
        dimensions: dimensions.map((i) => i.id),
    };
    $: runQuery(query);

    const setMeasures = (event: Event) => {
        measures = event.detail.calculations;
        if (measures.length === 0) {
            dimensions = [];
            queryResult = null;
            getStore();
        }
    };
    const setDimensions = (event: Event) => {
        dimensions = event.detail.calculations;
    };
    const runQuery = (query: Query) => {
        if (measures.length > 0) {
            fetch("/api/query/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(query),
            })
                .then((res) => res.json())
                .then((data) => {
                    queryResult = data;
                    store = data.metadata.store;
                });
        }
    };
    const getStore = () => {
        fetch("/api/store/")
            .then((res) => res.json())
            .then((data) => (store = data))
            .catch((err) => console.error(err));
    };

    getStore();
</script>

<div>
    <CalculationSelector
        title="Show me"
        placeholder="find a metric..."
        availableCalculations={store.measures}
        on:updateCalculations={setMeasures}
    />
    {#if measures.length > 0}
        <CalculationSelector
            title="by"
            placeholder="add a breakdown..."
            availableCalculations={store.dimensions}
            on:updateCalculations={setDimensions}
        />
        <FilterSelector
            title="but only if"
            placeholder="add a filter..."
            availableDimensions={store.dimensions}
            on:filters
        />
    {/if}

    {#if queryResult !== null}
        <QueryResultDisplay {queryResult} />
    {/if}
</div>
