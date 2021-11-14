<script lang="ts">
    import QueryResultDisplay from "../components/display/QueryResultDisplay.svelte";
    import { Server } from "../graphql";
    import type { QueryResult } from "src/schema";

    let value = "";
    let queryResult: QueryResult | null = null;
    let errors: { message: string }[] | null = null;
    let running = false;
    let formatting = true;
    $: executeLabel = running ? "Running..." : "Execute";

    const qlQuery = `
    query executeQuery($query: String!, $formatting: Boolean!) {
        result: qlQuery(input: $query, formatting: $formatting) {
            metadata {
                rawQuery
                columns {
                    id
                    name
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
            .request(qlQuery, { query: value, formatting })
            .then((data) => {
                queryResult = data.result;
                errors = null;
                running = false;
            })
            .catch((err) => {
                errors = err;
                queryResult = null;
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
    <div class="query card metric">
        <textarea
            id="query"
            spellcheck="false"
            bind:value
            on:keydown={keydown}
        />
        <button on:click={execute} disabled={running}>{executeLabel}</button>
        <label
            ><input type="checkbox" bind:checked={formatting} /> Formatting</label
        >
    </div>
    <div class="card display">
        {#if queryResult !== null}
            <QueryResultDisplay {queryResult} />
        {/if}
        {#if errors !== null}
            {#each errors as err}
                {err.message}
            {/each}
        {/if}
    </div>
</div>

<style lang="scss">
    .wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    textarea {
        width: 100%;
        height: 10em;
        border: 0;
        resize: none;
        border: 1px solid lightgray;

        &:focus {
            outline: none;
        }
    }

    .display {
        overflow: scroll;
        margin-top: 1rem;
        flex-grow: 1;
        max-height: 100%;
        margin-bottom: 1rem;
    }
</style>
