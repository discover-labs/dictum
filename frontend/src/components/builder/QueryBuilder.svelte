<script lang="ts">
    import CalculationSelector from "./CalculationSelector.svelte";
    import FilterSelector from "./FilterSelector.svelte";
    import QueryResultDisplay from "../display/QueryResultDisplay.svelte";
    import type {
        Query,
        Measure,
        Dimension,
        QueryResult,
        Store,
    } from "src/schema";
    import type { Event } from "src/components/types";
    import { Server } from "../../graphql";

    let store: Store = {
        measures: [],
        dimensions: [],
    };
    let measures: Measure[] = [];
    let dimensions: Dimension[] = [];
    let filters: string[] = [];
    let queryResult: QueryResult | null = null;

    $: query = {
        measures: measures.map((i) => i.id),
        dimensions: dimensions.map((i) => i.id),
        filters: filters,
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
    const setFilters = (event: Event) => {
        filters = event.detail;
    };
    const server = new Server();
    const executeQuery = `
    query executeQuery($input: StoreQuery!) {
        result: query(input: $input) {
            metadata {
                columns {
                    __typename
                    ...on Calculation {
                        id
                        name
                        format {
                            spec
                            currencyPrefix
                            currencySuffix
                        }
                    }
                }
                locale { number time }
                store {
                    measures { id name }
                    dimensions { id name }
                }
            }
            data
        }
    }`;
    const runQuery = (query: Query) => {
        if (measures.length > 0) {
            server
                .request(executeQuery, { input: query })
                .then((res) => res.json())
                .then((res) => {
                    queryResult = res.data.result;
                    store = queryResult.metadata.store;
                });
        }
    };
    const getStoreQuery = `
        query {
            store {
                measures { id name }
                dimensions { id name }
            }
        }`;
    const getStore = () => {
        server
            .request(getStoreQuery)
            .then((res) => res.json())
            .then((res) => (store = res.data.store))
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
            on:updateFilters={setFilters}
        />
    {/if}

    {#if queryResult !== null}
        <QueryResultDisplay {queryResult} />
    {/if}
</div>
