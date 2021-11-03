<script lang="ts">
    export let data: object[];
    export let meta: { id: string; name: string }[];

    $: keys = meta.map((m) => m.id);
    $: names = meta.map((m) => m.name);
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
                        <td>{row[k]}</td>
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
        margin: 0;
        border-spacing: 0;
        font-size: 12pt;
    }
    th,
    td {
        text-decoration: none;
        padding: 0.5rem;
        text-align: right;
        margin-left: 1rem;
    }
    th {
        font-weight: 400;
        border-bottom: 1px solid gray;
    }
    td {
        border-bottom: 1px solid lightgray;
    }
</style>
