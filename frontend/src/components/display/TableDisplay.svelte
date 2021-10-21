<script lang="ts">
    export let data: object[];
    export let formatters: object;
    export let meta: object;

    $: keys = Object.keys(formatters);
    $: names = keys.map((k) => meta[k].name);
</script>

<div class="table-wrapper">
    <table>
        <thead>
            <tr>
                {#each names as name (name)}
                    <th>{name}</th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#each data as row}
                <tr>
                    {#each keys as k (k)}
                        <td> {formatters[k](row[k])}</td>
                    {/each}
                </tr>
            {/each}
        </tbody>
    </table>
</div>

<style>
    .table-wrapper {
        overflow: scroll;
    }
    table {
        margin: 0 auto 0 auto;
    }
    th,
    td {
        padding: 0.5rem;
        text-align: right;
        margin-left: 1rem;
    }
</style>
