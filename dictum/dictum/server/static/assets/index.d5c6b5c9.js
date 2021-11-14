import { S as w, i as L, s as O, e as g, t as j, a as S, b as h, c as k, d as m, f as N, n as R, g as q, h as P, m as Q, j as y, k as v, l as T, o as B, p as D, q as C, u as F, r as E, v as Z, w as x, x as $, y as H, z as M, A as ee } from "./vendor.415a5065.js";
const te = function() { const e = document.createElement("link").relList; if (e && e.supports && e.supports("modulepreload")) return; for (const l of document.querySelectorAll('link[rel="modulepreload"]')) t(l);
    new MutationObserver(l => { for (const r of l)
            if (r.type === "childList")
                for (const i of r.addedNodes) i.tagName === "LINK" && i.rel === "modulepreload" && t(i) }).observe(document, { childList: !0, subtree: !0 });

    function n(l) { const r = {}; return l.integrity && (r.integrity = l.integrity), l.referrerpolicy && (r.referrerPolicy = l.referrerpolicy), l.crossorigin === "use-credentials" ? r.credentials = "include" : l.crossorigin === "anonymous" ? r.credentials = "omit" : r.credentials = "same-origin", r }

    function t(l) { if (l.ep) return;
        l.ep = !0; const r = n(l);
        fetch(l.href, r) } };
te();

function ne(a) { let e, n, t, l, r, i; return { c() { e = g("div"), n = g("h1"), t = j(a[0]), l = S(), r = g("span"), i = j(a[1]), h(n, "class", "svelte-mi0gkn"), h(r, "class", "svelte-mi0gkn"), h(e, "class", "svelte-mi0gkn") }, m(u, s) { k(u, e, s), m(e, n), m(n, t), m(e, l), m(e, r), m(r, i) }, p(u, [s]) { s & 1 && N(t, u[0]), s & 2 && N(i, u[1]) }, i: R, o: R, d(u) { u && q(e) } } }

function le(a, e, n) { let t, { name: l } = e,
        { value: r } = e,
        { format: i = null } = e; return a.$$set = u => { "name" in u && n(0, l = u.name), "value" in u && n(2, r = u.value), "format" in u && n(3, i = u.format) }, a.$$.update = () => { a.$$.dirty & 12 && n(1, t = r) }, [l, t, r, i] }
class re extends w { constructor(e) { super();
        L(this, e, le, ne, O, { name: 0, value: 2, format: 3 }) } }

function z(a, e, n) { const t = a.slice(); return t[4] = e[n].name, t[5] = e[n].value, t }

function I(a) { let e, n; return e = new re({ props: { name: a[4], value: a[5] } }), { c() { P(e.$$.fragment) }, m(t, l) { Q(e, t, l), n = !0 }, p(t, l) { const r = {};
            l & 1 && (r.name = t[4]), l & 1 && (r.value = t[5]), e.$set(r) }, i(t) { n || (y(e.$$.fragment, t), n = !0) }, o(t) { v(e.$$.fragment, t), n = !1 }, d(t) { T(e, t) } } }

function ae(a) { let e, n, t = a[0],
        l = []; for (let i = 0; i < t.length; i += 1) l[i] = I(z(a, t, i)); const r = i => v(l[i], 1, 1, () => { l[i] = null }); return { c() { e = g("div"); for (let i = 0; i < l.length; i += 1) l[i].c();
            h(e, "class", "big-numbers svelte-s599iq") }, m(i, u) { k(i, e, u); for (let s = 0; s < l.length; s += 1) l[s].m(e, null);
            n = !0 }, p(i, [u]) { if (u & 1) { t = i[0]; let s; for (s = 0; s < t.length; s += 1) { const f = z(i, t, s);
                    l[s] ? (l[s].p(f, u), y(l[s], 1)) : (l[s] = I(f), l[s].c(), y(l[s], 1), l[s].m(e, null)) } for (B(), s = t.length; s < l.length; s += 1) r(s);
                D() } }, i(i) { if (!n) { for (let u = 0; u < t.length; u += 1) y(l[u]);
                n = !0 } }, o(i) { l = l.filter(Boolean); for (let u = 0; u < l.length; u += 1) v(l[u]);
            n = !1 }, d(i) { i && q(e), C(l, i) } } }

function se(a, e, n) { let { data: t } = e, { formatters: l } = e, { meta: r } = e, i = []; return a.$$set = u => { "data" in u && n(1, t = u.data), "formatters" in u && n(2, l = u.formatters), "meta" in u && n(3, r = u.meta) }, a.$$.update = () => { if (a.$$.dirty & 14 && t.length === 1) { const u = t[0];
            n(0, i = Object.keys(u).map(s => ({ name: r[s].name, value: l[s](u[s]) }))) } }, [i, t, l, r] }
class ie extends w { constructor(e) { super();
        L(this, e, se, ae, O, { data: 1, formatters: 2, meta: 3 }) } }

function J(a, e, n) { const t = a.slice(); return t[5] = e[n], t }

function K(a, e, n) { const t = a.slice(); return t[8] = e[n], t }

function V(a, e, n) { const t = a.slice(); return t[11] = e[n], t }

function G(a, e) { let n, t = e[11] + "",
        l; return { key: a, first: null, c() { n = g("th"), l = j(t), h(n, "class", "svelte-10mmylh"), this.first = n }, m(r, i) { k(r, n, i), m(n, l) }, p(r, i) { e = r, i & 8 && t !== (t = e[11] + "") && N(l, t) }, d(r) { r && q(n) } } }

function U(a, e) { let n, t = e[1][e[8]](e[5][e[8]]) + "",
        l; return { key: a, first: null, c() { n = g("td"), l = j(t), h(n, "class", "svelte-10mmylh"), this.first = n }, m(r, i) { k(r, n, i), m(n, l) }, p(r, i) { e = r, i & 7 && t !== (t = e[1][e[8]](e[5][e[8]]) + "") && N(l, t) }, d(r) { r && q(n) } } }

function W(a) { let e, n = [],
        t = new Map,
        l, r = a[2]; const i = u => u[8]; for (let u = 0; u < r.length; u += 1) { let s = K(a, r, u),
            f = i(s);
        t.set(f, n[u] = U(f, s)) } return { c() { e = g("tr"); for (let u = 0; u < n.length; u += 1) n[u].c();
            l = S() }, m(u, s) { k(u, e, s); for (let f = 0; f < n.length; f += 1) n[f].m(e, null);
            m(e, l) }, p(u, s) { s & 7 && (r = u[2], n = F(n, s, i, 1, u, r, t, e, E, U, l, K)) }, d(u) { u && q(e); for (let s = 0; s < n.length; s += 1) n[s].d() } } }

function ue(a) { let e, n, t, l, r = [],
        i = new Map,
        u, s, f = a[3]; const p = c => c[11]; for (let c = 0; c < f.length; c += 1) { let _ = V(a, f, c),
            d = p(_);
        i.set(d, r[c] = G(d, _)) } let b = a[0],
        o = []; for (let c = 0; c < b.length; c += 1) o[c] = W(J(a, b, c)); return { c() { e = g("div"), n = g("table"), t = g("thead"), l = g("tr"); for (let c = 0; c < r.length; c += 1) r[c].c();
            u = S(), s = g("tbody"); for (let c = 0; c < o.length; c += 1) o[c].c();
            h(n, "class", "svelte-10mmylh"), h(e, "class", "table-wrapper svelte-10mmylh") }, m(c, _) { k(c, e, _), m(e, n), m(n, t), m(t, l); for (let d = 0; d < r.length; d += 1) r[d].m(l, null);
            m(n, u), m(n, s); for (let d = 0; d < o.length; d += 1) o[d].m(s, null) }, p(c, [_]) { if (_ & 8 && (f = c[3], r = F(r, _, p, 1, c, f, i, l, E, G, null, V)), _ & 7) { b = c[0]; let d; for (d = 0; d < b.length; d += 1) { const A = J(c, b, d);
                    o[d] ? o[d].p(A, _) : (o[d] = W(A), o[d].c(), o[d].m(s, null)) } for (; d < o.length; d += 1) o[d].d(1);
                o.length = b.length } }, i: R, o: R, d(c) { c && q(e); for (let _ = 0; _ < r.length; _ += 1) r[_].d();
            C(o, c) } } }

function ce(a, e, n) { let t, l, { data: r } = e,
        { formatters: i } = e,
        { meta: u } = e; return a.$$set = s => { "data" in s && n(0, r = s.data), "formatters" in s && n(1, i = s.formatters), "meta" in s && n(4, u = s.meta) }, a.$$.update = () => { a.$$.dirty & 2 && n(2, t = Object.keys(i)), a.$$.dirty & 20 && n(3, l = t.map(s => u[s].name)) }, [r, i, t, l, u] }
class oe extends w { constructor(e) { super();
        L(this, e, ce, ue, O, { data: 0, formatters: 1, meta: 4 }) } }
const X = a => a;

function fe(a, e) { if (typeof e == "undefined" || e === null) return X; const n = e.currencyPrefix.length > 0 || e.currencySuffix.length > 0 ? [e.currencyPrefix, e.currencySuffix] : a.currency,
        t = Object.assign({}, a, { currency: n }); return Z(t).format(e.spec) }

function me(a, e) { if (typeof e == "undefined" || e === null) return X; const t = x(a).format(e.spec); return l => { const r = new Date(l); return t(r) } }

function de(a) { const { time: e, number: n } = a.locale; return a.columns.reduce((t, l) => Object.assign(t, {
        [l.id]: l.type === "time" ? me(e, l.format) : fe(n, l.format) }), {}) }

function _e(a) { let e, n; return e = new oe({ props: { data: a[3], formatters: a[2], meta: a[1] } }), { c() { P(e.$$.fragment) }, m(t, l) { Q(e, t, l), n = !0 }, p(t, l) { const r = {};
            l & 8 && (r.data = t[3]), l & 4 && (r.formatters = t[2]), l & 2 && (r.meta = t[1]), e.$set(r) }, i(t) { n || (y(e.$$.fragment, t), n = !0) }, o(t) { v(e.$$.fragment, t), n = !1 }, d(t) { T(e, t) } } }

function ge(a) { let e, n; return e = new ie({ props: { data: a[3], formatters: a[2], meta: a[1] } }), { c() { P(e.$$.fragment) }, m(t, l) { Q(e, t, l), n = !0 }, p(t, l) { const r = {};
            l & 8 && (r.data = t[3]), l & 4 && (r.formatters = t[2]), l & 2 && (r.meta = t[1]), e.$set(r) }, i(t) { n || (y(e.$$.fragment, t), n = !0) }, o(t) { v(e.$$.fragment, t), n = !1 }, d(t) { T(e, t) } } }

function he(a) { let e, n, t, l; const r = [ge, _e],
        i = [];

    function u(s, f) { return s[0].data.length === 1 ? 0 : s[0].data.length > 1 ? 1 : -1 } return ~(e = u(a)) && (n = i[e] = r[e](a)), { c() { n && n.c(), t = $() }, m(s, f) {~e && i[e].m(s, f), k(s, t, f), l = !0 }, p(s, [f]) { let p = e;
            e = u(s), e === p ? ~e && i[e].p(s, f) : (n && (B(), v(i[p], 1, 1, () => { i[p] = null }), D()), ~e ? (n = i[e], n ? n.p(s, f) : (n = i[e] = r[e](s), n.c()), y(n, 1), n.m(t.parentNode, t)) : n = null) }, i(s) { l || (y(n), l = !0) }, o(s) { v(n), l = !1 }, d(s) {~e && i[e].d(s), s && q(t) } } }

function ye(a, e, n) { let t, l, r, { queryResult: i } = e; return a.$$set = u => { "queryResult" in u && n(0, i = u.queryResult) }, a.$$.update = () => { a.$$.dirty & 1 && n(3, t = i.data), a.$$.dirty & 1 && n(2, l = de(i.metadata)), a.$$.dirty & 1 && n(1, r = i.metadata.columns.reduce((u, s) => Object.assign(u, {
            [s.id]: s }), {})) }, [i, r, l, t] }
class pe extends w { constructor(e) { super();
        L(this, e, ye, he, O, { queryResult: 0 }) } }
class be { request(e, n) { return fetch("/graphql/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: e, variables: n }) }).then(t => t.json()).then(t => t.data) } }

function Y(a) { let e, n; return e = new pe({ props: { queryResult: a[0] } }), { c() { P(e.$$.fragment) }, m(t, l) { Q(e, t, l), n = !0 }, p(t, l) { const r = {};
            l & 1 && (r.queryResult = t[0]), e.$set(r) }, i(t) { n || (y(e.$$.fragment, t), n = !0) }, o(t) { v(e.$$.fragment, t), n = !1 }, d(t) { T(e, t) } } }

function ve(a) { let e, n, t, l, r, i, u, s, f, p, b, o = a[0] !== null && Y(a); return { c() { e = g("div"), n = g("div"), t = g("textarea"), l = S(), r = g("button"), i = j(a[3]), u = S(), s = g("div"), o && o.c(), h(t, "id", "query"), h(t, "spellcheck", "false"), t.autofocus = !0, h(t, "class", "svelte-1k19cnq"), r.disabled = a[1], h(n, "class", "query card metric"), h(s, "class", "display svelte-1k19cnq"), h(e, "class", "wrapper svelte-1k19cnq") }, m(c, _) { k(c, e, _), m(e, n), m(n, t), H(t, a[2]), m(n, l), m(n, r), m(r, i), m(e, u), m(e, s), o && o.m(s, null), f = !0, t.focus(), p || (b = [M(t, "input", a[6]), M(t, "keydown", a[5]), M(r, "click", a[4])], p = !0) }, p(c, [_]) { _ & 4 && H(t, c[2]), (!f || _ & 8) && N(i, c[3]), (!f || _ & 2) && (r.disabled = c[1]), c[0] !== null ? o ? (o.p(c, _), _ & 1 && y(o, 1)) : (o = Y(c), o.c(), y(o, 1), o.m(s, null)) : o && (B(), v(o, 1, 1, () => { o = null }), D()) }, i(c) { f || (y(o), f = !0) }, o(c) { v(o), f = !1 }, d(c) { c && q(e), o && o.d(), p = !1, ee(b) } } }

function ke(a, e, n) { let t, l = "",
        r = null,
        i = !1; const u = `
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
    `,
        s = new be;

    function f() { n(1, i = !0), s.request(u, { query: l }).then(o => { n(0, r = o.result), n(1, i = !1) }).catch(o => { console.log(o), n(1, i = !1) }) }

    function p(o) { o.key == "Enter" && o.getModifierState("Control") && f() }

    function b() { l = this.value, n(2, l) } return a.$$.update = () => { a.$$.dirty & 2 && n(3, t = i ? "Running..." : "Execute"), a.$$.dirty & 1 && r !== null && console.log(r.metadata.rawQuery) }, [r, i, l, t, f, p, b] }
class qe extends w { constructor(e) { super();
        L(this, e, ke, ve, O, {}) } }

function we(a) { let e, n, t, l, r, i, u; return i = new qe({}), { c() { e = g("div"), n = g("nav"), n.innerHTML = '<div class="container">Dictum</div>', t = S(), l = g("div"), r = g("div"), P(i.$$.fragment), h(n, "class", "navbar svelte-bhc2bh"), h(r, "class", "container"), h(l, "class", "page svelte-bhc2bh") }, m(s, f) { k(s, e, f), m(e, n), m(e, t), m(e, l), m(l, r), Q(i, r, null), u = !0 }, p: R, i(s) { u || (y(i.$$.fragment, s), u = !0) }, o(s) { v(i.$$.fragment, s), u = !1 }, d(s) { s && q(e), T(i) } } }
class Le extends w { constructor(e) { super();
        L(this, e, null, we, O, {}) } }
new Le({ target: document.body });