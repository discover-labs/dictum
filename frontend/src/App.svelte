<script lang="ts">
    import QLPage from "./pages/QLPage.svelte";
</script>

<div class="root">
    <nav class="navbar">
        <div class="container">Dictum</div>
    </nav>
    <div class="page">
        <div class="container">
            <QLPage />
        </div>
    </div>
</div>

<style lang="scss">
    @import "./styles/colors.scss";
    .root {
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    .navbar {
        @include card-shadow;
        background-color: $blue;
        color: white;
        font-weight: 300;
        padding: 10pt 0 10pt 0;
        font-size: 18pt;
    }
    .page {
        margin-top: 2rem;
        flex: 1;
        min-height: 0;
    }
</style>
