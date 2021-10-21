<script lang="ts">
    import Components from "./pages/Components.svelte";
</script>

<div>
    <nav class="navbar">
        <div class="container">Hyperplane</div>
    </nav>
    <div class="page">
        <div class="container">
            <Components />
        </div>
    </div>
</div>

<style lang="scss">
    @import "./styles/colors.scss";
    .navbar {
        @include card-shadow;
        background-color: $blue;
        color: white;
        font-weight: 300;
        padding: 10pt 0 10pt 0;
        font-size: 18pt;
    }
    .page {
        margin-top: 30pt;
    }
</style>
