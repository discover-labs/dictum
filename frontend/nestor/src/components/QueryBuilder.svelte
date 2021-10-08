<script>
    import CalculationSelector from "./builder/CalculationSelector.svelte";
    import QueryResultDisplay from "./display/QueryResultDisplay.svelte";

    let store = { measures: [], dimensions: [] };
    let measures = [];
    let dimensions = [];
    let queryResult = { data: [] };

    $: query = {
        measures: measures.map((i) => i.id),
        dimensions: dimensions.map((i) => i.id),
    };
    $: runQuery(query);

    const addCalculation = (arr, item) => {
        const ids = arr.map((i) => i.id);
        if (ids.indexOf(item.id) === -1) {
            return [...arr, item];
        }
        return arr;
    };
    const addMeasure = (event) => {
        measures = addCalculation(measures, event.detail.item);
    };
    const addDimension = (event) => {
        dimensions = addCalculation(dimensions, event.detail.item);
    };
    const removeMeasure = (event) => {
        measures = measures.filter((i) => i.id !== event.detail.id);
        if (measures.length === 0) {
            dimensions = [];
            getStore();
        }
    };
    const removeDimension = (event) => {
        dimensions = dimensions.filter((i) => i.id !== event.detail.id);
    };
    const runQuery = (query) => {
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
        calculations={measures}
        availableCalculations={store.measures}
        on:addCalculation={addMeasure}
        on:removeCalculation={removeMeasure}
    />
    {#if measures.length > 0}
        <CalculationSelector
            title="by"
            placeholder="add a breakdown..."
            calculations={dimensions}
            availableCalculations={store.dimensions}
            on:addCalculation={addDimension}
            on:removeCalculation={removeDimension}
        />
    {/if}

    {#if measures.length > 0}
        <QueryResultDisplay {queryResult} />
    {/if}
</div>
