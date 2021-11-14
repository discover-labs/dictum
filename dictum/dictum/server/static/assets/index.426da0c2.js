import { S as j, i as Q, s as S, e as _, t as B, a as R, b as p, c as w, d as f, f as O, n as M, g as L, h as P, m as T, j as v, k as q, l as A, o as D, p as E, q as x, u as F, r as H, v as Z, w as I, x as C, y as $ } from "./vendor.6a7c4d5c.js";
const ee = function() { const e = document.createElement("link").relList; if (e && e.supports && e.supports("modulepreload")) return; for (const n of document.querySelectorAll('link[rel="modulepreload"]')) l(n);
    new MutationObserver(n => { for (const r of n)
            if (r.type === "childList")
                for (const a of r.addedNodes) a.tagName === "LINK" && a.rel === "modulepreload" && l(a) }).observe(document, { childList: !0, subtree: !0 });

    function t(n) { const r = {}; return n.integrity && (r.integrity = n.integrity), n.referrerpolicy && (r.referrerPolicy = n.referrerpolicy), n.crossorigin === "use-credentials" ? r.credentials = "include" : n.crossorigin === "anonymous" ? r.credentials = "omit" : r.credentials = "same-origin", r }

    function l(n) { if (n.ep) return;
        n.ep = !0; const r = t(n);
        fetch(n.href, r) } };
ee();

function te(s) { let e, t, l, n, r, a; return { c() { e = _("div"), t = _("h1"), l = B(s[0]), n = R(), r = _("span"), a = B(s[1]), p(t, "class", "svelte-mi0gkn"), p(r, "class", "svelte-mi0gkn"), p(e, "class", "svelte-mi0gkn") }, m(i, u) { w(i, e, u), f(e, t), f(t, l), f(e, n), f(e, r), f(r, a) }, p(i, [u]) { u & 1 && O(l, i[0]), u & 2 && O(a, i[1]) }, i: M, o: M, d(i) { i && L(e) } } }

function le(s, e, t) { let l, { name: n } = e,
        { value: r } = e,
        { format: a = null } = e; return s.$$set = i => { "name" in i && t(0, n = i.name), "value" in i && t(2, r = i.value), "format" in i && t(3, a = i.format) }, s.$$.update = () => { s.$$.dirty & 12 && t(1, l = r) }, [n, l, r, a] }
class ne extends j { constructor(e) { super();
        Q(this, e, le, te, S, { name: 0, value: 2, format: 3 }) } }

function J(s, e, t) { const l = s.slice(); return l[3] = e[t].name, l[4] = e[t].value, l }

function K(s) { let e, t; return e = new ne({ props: { name: s[3], value: s[4] } }), { c() { P(e.$$.fragment) }, m(l, n) { T(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 1 && (r.name = l[3]), n & 1 && (r.value = l[4]), e.$set(r) }, i(l) { t || (v(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function re(s) { let e, t, l = s[0],
        n = []; for (let a = 0; a < l.length; a += 1) n[a] = K(J(s, l, a)); const r = a => q(n[a], 1, 1, () => { n[a] = null }); return { c() { e = _("div"); for (let a = 0; a < n.length; a += 1) n[a].c();
            p(e, "class", "big-numbers svelte-s599iq") }, m(a, i) { w(a, e, i); for (let u = 0; u < n.length; u += 1) n[u].m(e, null);
            t = !0 }, p(a, [i]) { if (i & 1) { l = a[0]; let u; for (u = 0; u < l.length; u += 1) { const c = J(a, l, u);
                    n[u] ? (n[u].p(c, i), v(n[u], 1)) : (n[u] = K(c), n[u].c(), v(n[u], 1), n[u].m(e, null)) } for (D(), u = l.length; u < n.length; u += 1) r(u);
                E() } }, i(a) { if (!t) { for (let i = 0; i < l.length; i += 1) v(n[i]);
                t = !0 } }, o(a) { n = n.filter(Boolean); for (let i = 0; i < n.length; i += 1) q(n[i]);
            t = !1 }, d(a) { a && L(e), x(n, a) } } }

function ae(s, e, t) { let l, { data: n } = e,
        { meta: r } = e; return s.$$set = a => { "data" in a && t(1, n = a.data), "meta" in a && t(2, r = a.meta) }, s.$$.update = () => { s.$$.dirty & 6 && t(0, l = r.map(({ id: a, name: i }) => ({ name: i, value: n[a] }))) }, [l, n, r] }
class se extends j { constructor(e) { super();
        Q(this, e, ae, re, S, { data: 1, meta: 2 }) } }

function V(s, e, t) { const l = s.slice(); return l[4] = e[t], l }

function z(s, e, t) { const l = s.slice(); return l[7] = e[t], l }

function G(s, e, t) { const l = s.slice(); return l[10] = e[t], l }

function U(s, e) { let t, l = e[10] + "",
        n; return { key: s, first: null, c() { t = _("th"), n = B(l), p(t, "class", "svelte-2x1jox"), this.first = t }, m(r, a) { w(r, t, a), f(t, n) }, p(r, a) { e = r, a & 2 && l !== (l = e[10] + "") && O(n, l) }, d(r) { r && L(t) } } }

function W(s, e) { let t, l = e[4][e[7]] + "",
        n; return { key: s, first: null, c() { t = _("td"), n = B(l), p(t, "class", "svelte-2x1jox"), this.first = t }, m(r, a) { w(r, t, a), f(t, n) }, p(r, a) { e = r, a & 5 && l !== (l = e[4][e[7]] + "") && O(n, l) }, d(r) { r && L(t) } } }

function X(s) { let e, t = [],
        l = new Map,
        n, r = s[2]; const a = i => i[7]; for (let i = 0; i < r.length; i += 1) { let u = z(s, r, i),
            c = a(u);
        l.set(c, t[i] = W(c, u)) } return { c() { e = _("tr"); for (let i = 0; i < t.length; i += 1) t[i].c();
            n = R() }, m(i, u) { w(i, e, u); for (let c = 0; c < t.length; c += 1) t[c].m(e, null);
            f(e, n) }, p(i, u) { u & 5 && (r = i[2], t = F(t, u, a, 1, i, r, l, e, H, W, n, z)) }, d(i) { i && L(e); for (let u = 0; u < t.length; u += 1) t[u].d() } } }

function ie(s) { let e, t, l, n, r = [],
        a = new Map,
        i, u, c = s[1]; const b = o => o[10]; for (let o = 0; o < c.length; o += 1) { let m = G(s, c, o),
            d = b(m);
        a.set(d, r[o] = U(d, m)) } let k = s[0],
        g = []; for (let o = 0; o < k.length; o += 1) g[o] = X(V(s, k, o)); return { c() { e = _("div"), t = _("table"), l = _("thead"), n = _("tr"); for (let o = 0; o < r.length; o += 1) r[o].c();
            i = R(), u = _("tbody"); for (let o = 0; o < g.length; o += 1) g[o].c();
            p(t, "class", "svelte-2x1jox"), p(e, "class", "table-wrapper svelte-2x1jox") }, m(o, m) { w(o, e, m), f(e, t), f(t, l), f(l, n); for (let d = 0; d < r.length; d += 1) r[d].m(n, null);
            f(t, i), f(t, u); for (let d = 0; d < g.length; d += 1) g[d].m(u, null) }, p(o, [m]) { if (m & 2 && (c = o[1], r = F(r, m, b, 1, o, c, a, n, H, U, null, G)), m & 5) { k = o[0]; let d; for (d = 0; d < k.length; d += 1) { const h = V(o, k, d);
                    g[d] ? g[d].p(h, m) : (g[d] = X(h), g[d].c(), g[d].m(u, null)) } for (; d < g.length; d += 1) g[d].d(1);
                g.length = k.length } }, i: M, o: M, d(o) { o && L(e); for (let m = 0; m < r.length; m += 1) r[m].d();
            x(g, o) } } }

function ue(s, e, t) { let l, n, { data: r } = e,
        { meta: a } = e; return s.$$set = i => { "data" in i && t(0, r = i.data), "meta" in i && t(3, a = i.meta) }, s.$$.update = () => { s.$$.dirty & 8 && t(2, l = a.map(i => i.id)), s.$$.dirty & 8 && t(1, n = a.map(i => i.name)) }, [r, n, l, a] }
class oe extends j { constructor(e) { super();
        Q(this, e, ue, ie, S, { data: 0, meta: 3 }) } }

function ce(s) { let e, t; return e = new oe({ props: { data: s[2], meta: s[1] } }), { c() { P(e.$$.fragment) }, m(l, n) { T(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 4 && (r.data = l[2]), n & 2 && (r.meta = l[1]), e.$set(r) }, i(l) { t || (v(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function fe(s) { let e, t; return e = new se({ props: { data: s[2][0], meta: s[1] } }), { c() { P(e.$$.fragment) }, m(l, n) { T(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 4 && (r.data = l[2][0]), n & 2 && (r.meta = l[1]), e.$set(r) }, i(l) { t || (v(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function de(s) { let e, t, l, n; const r = [fe, ce],
        a = [];

    function i(u, c) { return u[0].data.length === 1 ? 0 : u[0].data.length > 1 ? 1 : -1 } return ~(e = i(s)) && (t = a[e] = r[e](s)), { c() { t && t.c(), l = Z() }, m(u, c) {~e && a[e].m(u, c), w(u, l, c), n = !0 }, p(u, [c]) { let b = e;
            e = i(u), e === b ? ~e && a[e].p(u, c) : (t && (D(), q(a[b], 1, 1, () => { a[b] = null }), E()), ~e ? (t = a[e], t ? t.p(u, c) : (t = a[e] = r[e](u), t.c()), v(t, 1), t.m(l.parentNode, l)) : t = null) }, i(u) { n || (v(t), n = !0) }, o(u) { q(t), n = !1 }, d(u) {~e && a[e].d(u), u && L(l) } } }

function me(s, e, t) { let l, n, { queryResult: r } = e; return s.$$set = a => { "queryResult" in a && t(0, r = a.queryResult) }, s.$$.update = () => { s.$$.dirty & 1 && t(2, l = r.data), s.$$.dirty & 1 && t(1, n = r.metadata.columns) }, [r, n, l] }
class _e extends j { constructor(e) { super();
        Q(this, e, me, de, S, { queryResult: 0 }) } }
class ge { request(e, t) { return fetch("/graphql/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: e, variables: t }) }).then(l => l.json()).then(l => l.data) } }

function Y(s) { let e, t; return e = new _e({ props: { queryResult: s[0] } }), { c() { P(e.$$.fragment) }, m(l, n) { T(e, l, n), t = !0 }, p(l, n) { const r = {};
            n & 1 && (r.queryResult = l[0]), e.$set(r) }, i(l) { t || (v(e.$$.fragment, l), t = !0) }, o(l) { q(e.$$.fragment, l), t = !1 }, d(l) { A(e, l) } } }

function he(s) { let e, t, l, n, r, a, i, u, c, b, k, g, o, m, d, h = s[0] !== null && Y(s); return { c() { e = _("div"), t = _("div"), l = _("textarea"), n = R(), r = _("button"), a = B(s[4]), i = R(), u = _("label"), c = _("input"), b = B(" Formatting"), k = R(), g = _("div"), h && h.c(), p(l, "id", "query"), p(l, "spellcheck", "false"), p(l, "class", "svelte-9lkexn"), r.disabled = s[1], p(r, "class", "svelte-9lkexn"), p(c, "type", "checkbox"), p(u, "class", "svelte-9lkexn"), p(t, "class", "query card metric svelte-9lkexn"), p(g, "class", "card display svelte-9lkexn"), p(e, "class", "wrapper svelte-9lkexn") }, m(y, N) { w(y, e, N), f(e, t), f(t, l), I(l, s[2]), f(t, n), f(t, r), f(r, a), f(t, i), f(t, u), f(u, c), c.checked = s[3], f(u, b), f(e, k), f(e, g), h && h.m(g, null), o = !0, m || (d = [C(l, "input", s[7]), C(l, "keydown", s[6]), C(r, "click", s[5]), C(c, "change", s[8])], m = !0) }, p(y, [N]) { N & 4 && I(l, y[2]), (!o || N & 16) && O(a, y[4]), (!o || N & 2) && (r.disabled = y[1]), N & 8 && (c.checked = y[3]), y[0] !== null ? h ? (h.p(y, N), N & 1 && v(h, 1)) : (h = Y(y), h.c(), v(h, 1), h.m(g, null)) : h && (D(), q(h, 1, 1, () => { h = null }), E()) }, i(y) { o || (v(h), o = !0) }, o(y) { q(h), o = !1 }, d(y) { y && L(e), h && h.d(), m = !1, $(d) } } }

function pe(s, e, t) { let l, n = "",
        r = null,
        a = !1,
        i = !0; const u = `
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
    `,
        c = new ge;

    function b() { t(1, a = !0), c.request(u, { query: n, formatting: i }).then(m => { t(0, r = m.result), t(1, a = !1) }).catch(m => { console.log(m), t(1, a = !1) }) }

    function k(m) { m.key == "Enter" && m.getModifierState("Control") && b() }

    function g() { n = this.value, t(2, n) }

    function o() { i = this.checked, t(3, i) } return s.$$.update = () => { s.$$.dirty & 2 && t(4, l = a ? "Running..." : "Execute"), s.$$.dirty & 1 && r !== null && console.log(r.metadata.rawQuery) }, [r, a, n, i, l, b, k, g, o] }
class ye extends j { constructor(e) { super();
        Q(this, e, pe, he, S, {}) } }

function ve(s) { let e, t, l, n, r, a, i; return a = new ye({}), { c() { e = _("div"), t = _("nav"), t.innerHTML = '<div class="container">Dictum</div>', l = R(), n = _("div"), r = _("div"), P(a.$$.fragment), p(t, "class", "navbar svelte-1wb6m37"), p(r, "class", "container"), p(n, "class", "page svelte-1wb6m37"), p(e, "class", "root svelte-1wb6m37") }, m(u, c) { w(u, e, c), f(e, t), f(e, l), f(e, n), f(n, r), T(a, r, null), i = !0 }, p: M, i(u) { i || (v(a.$$.fragment, u), i = !0) }, o(u) { q(a.$$.fragment, u), i = !1 }, d(u) { u && L(e), A(a) } } }
class be extends j { constructor(e) { super();
        Q(this, e, null, ve, S, {}) } }
new be({ target: document.body });