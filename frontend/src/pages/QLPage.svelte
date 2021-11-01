<script lang="ts">
    import QueryResultDisplay from "../components/display/QueryResultDisplay.svelte";
    import { Server } from "../graphql";
    import type { QueryResult } from "src/schema";

    let value = "";
    let queryResult: QueryResult | null = null;
    let running = false;
    $: executeLabel = running ? "Running..." : "Execute";

    const qlQuery = `
    query executeQuery($query: String!) {
        result: qlQuery(input: $query) {
            metadata {
                rawQuery
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
                    ...on Dimension { type }
                }
                locale { number time }
                store {
                    metrics { id name }
                    dimensions { id name }
                }
            }
            data
        }
    }
    `;
    const server = new Server();
    function execute() {
        running = true;
        server
            .request(qlQuery, { query: value })
            .then((data) => {
                queryResult = data.result;
                running = false;
            })
            .catch((err) => {
                console.log(err);
                running = false;
            });
    }
    function keydown(event: KeyboardEvent) {
        if (event.key == "Enter" && event.getModifierState("Control")) {
            execute();
        }
    }
    $: if (queryResult !== null) {
        console.log(queryResult.metadata.rawQuery);
    }
</script>

<div class="wrapper">
    <div class="query card">
        <textarea id="query" bind:value on:keydown={keydown} />
        <button on:click={execute} disabled={running}>{executeLabel}</button>
    </div>
    <div class="display">
        {#if queryResult !== null}
            <QueryResultDisplay {queryResult} />
        {/if}
    </div>
</div>

<style lang="scss">
    .wrapper {
        display: flex;
        flex-direction: column;
        max-height: 100vh;
    }
    textarea {
        width: 100%;
        height: 10em;
        border: 0;
        resize: none;
    }

    .display {
        width: 100%;
        overflow: scroll;
    }
</style>
