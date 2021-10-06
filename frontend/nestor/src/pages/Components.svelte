<script>
    import QueryBuilder from "../components/QueryBuilder.svelte";

    let name = "Number of Tracks";
    let description =
        "Total number of tracks in our media library. Note that there are different media types included, not only music. Use this measure to explore what can possible be sold here. Can be split up by various musical parameters: genre, artist, album. Has no connection to sales.";
    let expr = "count()";
    let calculations = [
        { id: 1, name, description, expr },
        { id: 2, name, description, expr },
    ];
</script>

<div class="container">
    <QueryBuilder />
</div>

<style>
    .container {
        max-width: 960px;
        margin: 0 auto 0 auto;
    }
</style>
